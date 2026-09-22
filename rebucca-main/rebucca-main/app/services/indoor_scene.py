# -*- coding: utf-8 -*-
"""
室内互动场景引擎 — IndoorSceneEngine。

四大模式：
  pet_mode    宠物陪伴：YOLO 检测 cat/dog → PTZ 对准 + spotlight 闪烁 + 逗宠音频 → 日常小视频
  elder_mode  老人看护：跌倒检测 + 久站不动判定 → 立即告警 + 语音询问 + 通知子女
  child_mode  儿童看护：厨房/阳台/窗边危险区域 → 语音提醒
  night_mode  智能夜间：22:00~06:00 低照度人形 → 调暗 spotlight + PTZ 跟随

热更新：配置每次从 DB 实时读取（IndoorSceneConfig），修改即生效，无需重启。
"""
import logging
from datetime import datetime

from app.models import IndoorSceneConfig, IndoorEvent
from app.services.device_hub import DeviceHub

logger = logging.getLogger("services.indoor_scene")


class IndoorSceneEngine:
    """室内场景引擎：统一管理室内摄像头的四大看护模式。"""

    MODE_PET = "pet"
    MODE_ELDER = "elder"
    MODE_CHILD = "child"
    MODE_NIGHT = "night"

    # 默认配置（可被 DB 中 scene_type='general' 的 config 覆盖）
    DEFAULT_CONFIG = {
        "pet_mode_enabled": True,
        "elder_mode_enabled": True,
        "child_mode_enabled": True,
        "night_mode_enabled": True,
        "night_start": "22:00",
        "night_end": "06:00",
        "sensitivity": 8,
        # 扩展参数
        "elder_stationary_frames": 90,   # 连续 N 帧无动作判定久站/异常
        "spotlight_blink_brightness": 70,
        "night_light_brightness": 20,
    }

    # 音频资源（stub：以 tts:// 表达合成语音，接入时替换为真实音频 URL）
    AUDIO_PET = "tts://逗宠音效"
    AUDIO_ELDER_INQUIRY = "tts://您好，您还好吗？需要帮助吗？"
    AUDIO_ALARM = "tts://紧急告警，请立即关注"
    AUDIO_CHILD_WARN = "tts://小朋友，这里危险哦，快离开这里"

    # 儿童模式危险区域关键词
    DANGER_ZONES = ("kitchen", "balcony", "window", "厨房", "阳台", "窗边", "窗户")

    # ----------------------- 统一入口 -----------------------

    def on_motion_detected(self, camera_id, frame=None, snapshot_path=""):
        """运动事件入口：按启用的模式逐一检测与联动。

        frame 可为 dict（由上层检测管线写入）：
          {"detections": [{"label": "cat", "confidence": 0.9, "bbox": [...]}],
           "fall": False, "stationary_frames": 0,
           "zone": "kitchen", "low_light": True}
        其它类型 frame 会尝试走 YOLO（无模型环境下优雅降级为空检测）。
        """
        cfg = self.get_effective_config(camera_id)
        results = []

        # 1. 宠物陪伴
        if cfg.get("pet_mode_enabled") and self._mode_row_enabled(camera_id, self.MODE_PET):
            results.append(self.pet_mode(camera_id, frame, cfg=cfg))

        # 2. 老人看护
        if cfg.get("elder_mode_enabled") and self._mode_row_enabled(camera_id, self.MODE_ELDER):
            results.append(self.elder_mode(camera_id, frame, cfg=cfg))

        # 3. 儿童看护
        if cfg.get("child_mode_enabled") and self._mode_row_enabled(camera_id, self.MODE_CHILD):
            results.append(self.child_mode(camera_id, frame, cfg=cfg))

        # 4. 智能夜间（受时间窗约束）
        if cfg.get("night_mode_enabled") and self._mode_row_enabled(camera_id, self.MODE_NIGHT) \
                and self.in_night_window(cfg):
            results.append(self.night_mode(camera_id, frame, cfg=cfg))

        triggered = [r for r in results if r.get("triggered")]
        logger.info("室内运动事件 cam=%s 触发模式 %d/%d",
                    camera_id, len(triggered), len(results))
        return {
            "camera_id": int(camera_id),
            "modes": results,
            "triggered_count": len(triggered),
        }

    # ----------------------- 宠物陪伴模式 -----------------------

    def pet_mode(self, camera_id, frame, cfg=None):
        """宠物陪伴：检测 cat/dog → PTZ 对准 + spotlight 闪烁 + 逗宠音频 + 日常小视频。"""
        cfg = cfg or self.get_effective_config(camera_id)
        animals = self.detect_objects(frame, labels=("cat", "dog"))
        if not animals:
            return {"mode": self.MODE_PET, "triggered": False}

        target = animals[0]
        hub = DeviceHub()
        actions = [
            hub.control_ptz(camera_id, "track", {"label": target.get("label"),
                                                 "bbox": target.get("bbox")}),
            # spotlight 闪烁（以 blink 参数下发，实际由设备固件执行）
            hub.control_light(camera_id, True,
                              cfg.get("spotlight_blink_brightness", 70)),
            hub.play_audio(camera_id, self.AUDIO_PET),
        ]
        clip_path = self.generate_pet_clip(camera_id, target)

        event = self._save_event(
            camera_id, event_type="pet_detected", scene_mode=self.MODE_PET,
            actions=actions, snapshot_path="", notified=0,
        )
        logger.info("宠物模式触发 cam=%s animal=%s clip=%s",
                    camera_id, target.get("label"), clip_path)
        return {
            "mode": self.MODE_PET, "triggered": True,
            "animal": target.get("label"), "event_id": event.id,
            "clip_path": clip_path, "actions": actions,
        }

    # ----------------------- 老人看护模式 -----------------------

    def elder_mode(self, camera_id, frame, cfg=None):
        """老人看护：跌倒 / 久站不动 → 立即告警 + 语音询问 + 通知子女。"""
        cfg = cfg or self.get_effective_config(camera_id)
        meta = frame if isinstance(frame, dict) else {}

        fall = bool(meta.get("fall"))
        stationary_frames = int(meta.get("stationary_frames", 0) or 0)
        stationary = stationary_frames >= int(cfg.get("elder_stationary_frames", 90))

        if not fall and not stationary:
            return {"mode": self.MODE_ELDER, "triggered": False}

        event_type = "elder_fall" if fall else "elder_stationary"
        hub = DeviceHub()
        actions = [
            hub.play_audio(camera_id, self.AUDIO_ALARM),
            hub.play_audio(camera_id, self.AUDIO_ELDER_INQUIRY),
            # 通知子女由广播完成：event_broadcast 推送给相关设备/订阅方
        ]
        event = self._save_event(
            camera_id, event_type=event_type, scene_mode=self.MODE_ELDER,
            actions=actions, snapshot_path="", notified=1,
        )
        hub.event_broadcast({
            "type": "elder_notify_family",
            "camera_id": int(camera_id),
            "event_type": event_type,
            "event_id": event.id,
            "timestamp": datetime.now().isoformat(),
            "targets": meta.get("notify_targets", []),
        })

        logger.warning("老人看护告警 cam=%s type=%s 已通知子女", camera_id, event_type)
        return {
            "mode": self.MODE_ELDER, "triggered": True,
            "event_type": event_type, "event_id": event.id, "actions": actions,
        }

    # ----------------------- 儿童看护模式 -----------------------

    def child_mode(self, camera_id, frame, cfg=None):
        """儿童看护：检测厨房/阳台/窗边等危险区域 → 语音提醒。"""
        cfg = cfg or self.get_effective_config(camera_id)
        meta = frame if isinstance(frame, dict) else {}

        zone = str(meta.get("zone", ""))
        danger = any(k in zone.lower() for k in
                     [z.lower() for z in self.DANGER_ZONES])
        # 也兼容通过检测目标携带 zone 标记
        if not danger:
            for d in meta.get("detections", []) or []:
                z = str(d.get("zone", "")).lower()
                if any(k in z for k in [x.lower() for x in self.DANGER_ZONES]):
                    danger, zone = True, z
                    break

        if not danger:
            return {"mode": self.MODE_CHILD, "triggered": False}

        hub = DeviceHub()
        actions = [hub.play_audio(camera_id, self.AUDIO_CHILD_WARN)]
        event = self._save_event(
            camera_id, event_type="danger_zone", scene_mode=self.MODE_CHILD,
            actions=actions, snapshot_path="", notified=0,
        )
        logger.info("儿童危险区域提醒 cam=%s zone=%s", camera_id, zone)
        return {
            "mode": self.MODE_CHILD, "triggered": True,
            "zone": zone, "event_id": event.id, "actions": actions,
        }

    # ----------------------- 智能夜间模式 -----------------------

    def night_mode(self, camera_id, frame, cfg=None):
        """智能夜间：低照度人形（起夜）→ 调暗 spotlight + PTZ 跟随。"""
        cfg = cfg or self.get_effective_config(camera_id)
        persons = self.detect_objects(frame, labels=("person",))
        if not persons:
            return {"mode": self.MODE_NIGHT, "triggered": False}

        target = persons[0]
        hub = DeviceHub()
        actions = [
            hub.control_light(camera_id, True,
                              cfg.get("night_light_brightness", 20)),
            hub.control_ptz(camera_id, "track", target.get("bbox")),
        ]
        event = self._save_event(
            camera_id, event_type="night_wake", scene_mode=self.MODE_NIGHT,
            actions=actions, snapshot_path="", notified=0,
        )
        logger.info("夜间起夜跟随 cam=%s", camera_id)
        return {
            "mode": self.MODE_NIGHT, "triggered": True,
            "event_id": event.id, "actions": actions,
        }

    # ----------------------- 检测 / 工具方法 -----------------------

    def detect_objects(self, frame, labels=("person",)):
        """目标检测：优先使用 frame 中上层已写入的 detections；无则尝试 YOLO。

        Returns:
            list[{"label": str, "confidence": float, "bbox": list}]
        """
        wanted = {str(x).lower() for x in labels}
        if isinstance(frame, dict):
            dets = frame.get("detections") or []
            return [d for d in dets if str(d.get("label", "")).lower() in wanted]

        # 真实环境接入点：调用分析管线 YOLO；无模型时返回空列表（优雅降级）
        try:
            from app.analysis.detector import Detector  # noqa: F401
            # 预留：return Detector().infer(frame, labels=wanted)
        except Exception as e:
            logger.debug("YOLO 不可用，跳过检测: %s", e)
        return []

    def generate_pet_clip(self, camera_id, target):
        """生成宠物日常小视频片段（stub：返回约定路径）。"""
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"static/upload/clips/pet_cam{camera_id}_{ts}.mp4"

    @classmethod
    def in_night_window(cls, cfg, now=None):
        """判断当前是否处于夜间时间窗（支持跨午夜，如 22:00~06:00）。"""
        now = now or datetime.now()

        def _hm(s):
            try:
                h, m = str(s).split(":")
                return int(h) * 60 + int(m)
            except Exception:
                return 22 * 60

        cur = now.hour * 60 + now.minute
        start = _hm(cfg.get("night_start", "22:00"))
        end = _hm(cfg.get("night_end", "06:00"))
        if start == end:
            return False
        if start < end:
            return start <= cur < end
        return cur >= start or cur < end  # 跨午夜

    # ----------------------- 配置管理（热更新） -----------------------

    @classmethod
    def get_effective_config(cls, camera_id):
        """读取某摄像头的生效配置：默认值 ← general 行覆盖（每次实时查库）。"""
        cfg = dict(cls.DEFAULT_CONFIG)
        row = IndoorSceneConfig.objects.filter(
            camera_id=int(camera_id), scene_type="general").first()
        if row is not None and isinstance(row.config, dict):
            cfg.update(row.config)
        return cfg

    def _mode_row_enabled(self, camera_id, scene_type):
        """检查某模式独立配置行是否启用（无独立行视为启用）。"""
        row = IndoorSceneConfig.objects.filter(
            camera_id=int(camera_id), scene_type=scene_type).first()
        return True if row is None else bool(row.enabled)

    @staticmethod
    def get_configs(camera_id):
        return list(IndoorSceneConfig.objects.filter(camera_id=int(camera_id)))

    @staticmethod
    def upsert_config(camera_id, scene_type="general", enabled=True, config=None):
        """新增或更新场景配置（热更新写入点，保存后所有引擎立即读到新值）。"""
        obj = IndoorSceneConfig.objects.filter(
            camera_id=int(camera_id), scene_type=scene_type).first()
        if obj is None:
            obj = IndoorSceneConfig(
                camera_id=int(camera_id), scene_type=scene_type,
                enabled=1 if enabled else 0, config=config or {},
            )
        else:
            obj.enabled = 1 if enabled else 0
            if config is not None:
                obj.config = config
            obj.last_update_time = datetime.now()
        obj.save()
        return obj

    # ----------------------- 测试入口（供 API 手动联调） -----------------------

    def test_pet(self, camera_id):
        """手动测试宠物模式：注入合成 cat 检测。"""
        synth = {"detections": [
            {"label": "cat", "confidence": 0.98, "bbox": [120, 90, 300, 360]}]}
        return self.pet_mode(int(camera_id), synth)

    def test_elder(self, camera_id):
        """手动测试老人模式：注入合成跌倒事件。"""
        synth = {"fall": True, "stationary_frames": 0}
        return self.elder_mode(int(camera_id), synth)

    # ----------------------- 落库 -----------------------

    @staticmethod
    def _save_event(camera_id, event_type, scene_mode, actions,
                    snapshot_path="", notified=0):
        return IndoorEvent.objects.create(
            camera_id=int(camera_id),
            event_type=event_type,
            scene_mode=scene_mode,
            timestamp=datetime.now(),
            snapshot_path=snapshot_path or "",
            actions_taken=actions or [],
            notified=int(notified),
        )
