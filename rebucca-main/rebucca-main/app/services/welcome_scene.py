# -*- coding: utf-8 -*-
"""
回家迎宾场景引擎 — WelcomeSceneEngine。

- 后台工作线程：每 FRAME_INTERVAL(默认5) 帧调用一次 VLM 理解画面
- 检测到 has_person=true 且 direction=approaching：
    5 秒防抖（DEBOUNCE_SEC），窗口内不重复触发
- 触发动作（MockDeviceControl，全部写日志）：
    1. PTZ 转向居中
    2. 迎宾灯亮起
    3. 语音问候（按年龄层区分文案）
    4. 写入 av_alarm（scene_type=welcome，AI 描述 + 动作 + 截图）
    5. SSE 实时推送前端（EventBus）
"""
import logging
import os
import threading
from datetime import datetime

import cv2

from app.services.device_control import MockDeviceControl
from app.services.event_bus import EventBus
from app.services.vlm_client import VLMClient, load_env_file

logger = logging.getLogger("services.welcome_scene")

# 不同年龄层的问候语
GREETINGS = {
    "adult": "欢迎回家，已为您点亮灯光",
    "elder": "您回来啦，辛苦了，欢迎回家",
    "child": "小朋友，欢迎回家呀",
    "unknown": "欢迎回家",
}


class WelcomeSceneEngine:
    """迎宾场景：VLM 理解 → 防抖 → 设备联动 → 落库 + 推送。"""

    DEBOUNCE_SEC = 5.0  # 两次迎宾最小间隔

    def __init__(self, manager, camera_id="local-cam", frame_interval=None,
                 vlm=None, control=None):
        self.manager = manager
        self.camera_id = str(camera_id)
        load_env_file()
        self.frame_interval = int(
            frame_interval if frame_interval is not None
            else os.environ.get("FRAME_INTERVAL", 5))

        self.vlm = vlm or VLMClient()
        self.control = control or MockDeviceControl(self.camera_id)
        self._thread = None
        self._stop_event = threading.Event()
        self._last_analyzed_count = 0
        self._last_trigger_ts = 0.0
        self.trigger_count = 0

    # ----------------------- 生命周期 -----------------------

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._last_analyzed_count = self.manager.frame_count
        self._thread = threading.Thread(
            target=self._run, name="welcome-scene", daemon=True)
        self._thread.start()
        logger.info("迎宾场景引擎已启动 frame_interval=%d", self.frame_interval)

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None
        logger.info("迎宾场景引擎已停止")

    # ----------------------- 主循环 -----------------------

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._maybe_analyze()
            except Exception as e:
                # 单帧异常不能杀死引擎线程
                logger.warning("迎宾分析循环异常: %s", e)
            self._stop_event.wait(0.15)

    def _maybe_analyze(self):
        """每 frame_interval 帧分析一次最新画面。"""
        count = self.manager.frame_count
        if count == self._last_analyzed_count:
            return  # 没有新帧
        if (count - self._last_analyzed_count) < self.frame_interval:
            return
        self._last_analyzed_count = count

        frame = self.manager.get_latest_frame()
        if frame is None or not self.is_scene_enabled("welcome"):
            return

        result = self.vlm.understand_scene(frame)
        self.evaluate(frame, result)

    def evaluate(self, frame, result):
        """根据 VLM 结果决定是否迎宾（供线程与测试复用）。"""
        if not isinstance(result, dict):
            return None
        if not result.get("has_person") \
                or result.get("direction") != "approaching":
            return None

        import time
        now = time.time()
        if (now - self._last_trigger_ts) < self.DEBOUNCE_SEC:
            logger.info("迎宾防抖命中，%.1f 秒内不重复触发",
                        self.DEBOUNCE_SEC - (now - self._last_trigger_ts))
            return {"result": "debounced"}

        alert = self.trigger(frame, result)
        self._last_trigger_ts = now
        return alert

    # ----------------------- 触发动作 -----------------------

    def trigger(self, frame, result):
        """执行迎宾动作 + 落库 + SSE 推送。"""
        age_group = result.get("age_group", "unknown")
        greeting = GREETINGS.get(age_group, GREETINGS["unknown"])

        # 1~3. 模拟设备联动
        actions = [
            self.control.ptz_goto(self.camera_id, "center"),
            self.control.light_on(self.camera_id, 80),
            self.control.tts_speak(self.camera_id, greeting),
        ]

        # 4. 截图 + 落库
        snapshot_url, snapshot_file = self.save_snapshot(frame)
        ai_description = self.build_description(result)
        alert = self.persist_alert(ai_description, actions, snapshot_file)

        # 5. 实时推送前端
        EventBus().publish({
            "type": "welcome_alert",
            "scene_type": "welcome",
            "alert_id": alert.id,
            "ai_description": ai_description,
            "snapshot_url": snapshot_url,
            "timestamp": datetime.now().isoformat(),
            "actions": [a.get("action") for a in actions],
        })

        self.trigger_count += 1
        logger.warning("★ 迎宾触发 #%d age=%s source=%s alert_id=%d",
                       self.trigger_count, age_group,
                       result.get("source"), alert.id)
        return {"result": "triggered", "alert_id": alert.id,
                "actions": actions, "snapshot_url": snapshot_url}

    # ----------------------- 落库 / 工具 -----------------------

    @staticmethod
    def persist_alert(ai_description, actions, snapshot_file):
        """写入 av_alarm 告警表。"""
        from app.models import AlarmModel
        return AlarmModel.objects.create(
            stream=None,
            event_type="welcome",
            description=ai_description[:300],
            timestamp=datetime.now(),
            metadata="{}",
            scene_type="welcome",
            ai_description=ai_description,
            triggered_actions=actions,
            snapshot_path=snapshot_file,
        )

    def save_snapshot(self, frame):
        """保存触发时刻截图，返回 (可访问URL, 相对文件路径)。"""
        from pathlib import Path
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rel = f"snapshots/welcome_{ts}.jpg"
        # __file__ = <根>/app/services/welcome_scene.py，parents[2] 即项目根
        abs_dir = Path(__file__).resolve().parents[2] / "static" \
            / "upload" / "snapshots"
        os.makedirs(abs_dir, exist_ok=True)
        abs_path = abs_dir / f"welcome_{ts}.jpg"
        try:
            # 不能直接用 cv2.imwrite：Windows 下中文路径会静默失败
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                raise RuntimeError("截图 JPEG 编码失败")
            abs_path.write_bytes(buf.tobytes())
        except Exception as e:
            logger.warning("截图保存失败: %s", e)
            return "", ""
        return f"/upload/{rel}", rel

    @staticmethod
    def build_description(result):
        """把 VLM 结构化结果转成可读 AI 分析文字。"""
        source = "视觉大模型" if result.get("source") == "vlm" \
            else "本地模拟分析（未配置VLM key）"
        return (
            f"[{source}] 检测到有人靠近家门，"
            f"年龄层：{result.get('age_group', 'unknown')}，"
            f"方向：{result.get('direction', 'unknown')}，已触发迎宾接待。"
        )

    @staticmethod
    def is_scene_enabled(scene_type):
        """查询场景开关（复用 indoor_scene_config，camera_id=0；无配置行视为启用）。"""
        try:
            from app.models import IndoorSceneConfig
            row = IndoorSceneConfig.objects.filter(
                camera_id=0, scene_type=scene_type).first()
            return True if row is None else bool(row.enabled)
        except Exception:
            return True
