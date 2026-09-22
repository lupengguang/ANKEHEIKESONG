# 作者：北小菜
# 官网：https://www.yuturuishi.com
# 微信：bilibili_bxc
# 哔哩哔哩主页：https://space.bilibili.com/487906612
# gitee地址：https://gitee.com/Vanishi/rebucca
# github地址：https://github.com/beixiaocai/rebucca
"""
户外场景引擎 — 迎宾 / 访客接待 / 快递识别 / 夜间入侵等场景。

典型流程：
  运动检测(on_motion_detected) → 身份识别(identify_person)
     → 根据 person_type 触发对应场景(welcome/visitor/intrusion)
     → PTZ 转向 + 灯光 + 语音播报 + 事件落库
"""
import json
import logging
from datetime import datetime

from app.models import OutdoorSceneConfig, OutdoorEvent, StreamModel

logger = logging.getLogger("services.outdoor_scene")


class OutdoorSceneEngine:
    """户外场景引擎：统一管理户外摄像头的场景触发与联动控制。"""

    # 身份类型常量
    PERSON_FAMILY = "family"
    PERSON_VISITOR = "visitor"
    PERSON_STRANGER = "stranger"
    PERSON_DELIVERY = "delivery"
    PERSON_UNKNOWN = "unknown"

    # 场景类型 → 事件类型映射
    SCENE_EVENT_MAP = {
        "welcome": "welcome",
        "visitor": "visitor",
        "intrusion": "intrusion",
        "delivery": "delivery",
    }

    # ----------------------- 入口 -----------------------

    def on_motion_detected(self, camera_id, frame=None, snapshot_path=""):
        """运动检测触发的统一入口：识别身份 → 触发对应场景 → 落库。

        Args:
            camera_id: 摄像头ID
            frame: 可选图像数据(bytes/path/base64)
            snapshot_path: 可选快照路径

        Returns:
            dict: {"scene_type": str, "person_info": dict, "event_id": int, "actions": list}
        """
        # 1. 身份识别
        person_info = self.identify_person(frame=frame, camera_id=camera_id)

        # 2. 查询本摄像头启用的场景配置
        cfgs = OutdoorSceneConfig.objects.filter(camera_id=camera_id, enabled=1)
        cfg_map = {c.scene_type: c for c in cfgs}

        person_type = person_info.get("person_type", self.PERSON_UNKNOWN)
        confidence = person_info.get("confidence", 0.0)

        scene_type = None
        actions_taken = []

        try:
            # 3. 根据 person_type 选择场景
            if person_type == self.PERSON_FAMILY:
                scene_type = "welcome"
            elif person_type in (self.PERSON_DELIVERY,):
                scene_type = "delivery"
            elif person_type == self.PERSON_STRANGER:
                # 夜间(22:00~06:00)陌生人 → intrusion，白天 → visitor
                hour = datetime.now().hour
                scene_type = "intrusion" if (hour >= 22 or hour < 6) else "visitor"
            else:
                scene_type = "visitor"

            # 4. 触发场景动作（未配置则跳过动作，仅落库）
            cfg = cfg_map.get(scene_type)
            if cfg is not None:
                if scene_type == "welcome":
                    actions_taken = self.trigger_welcome_scene(camera_id, person_info, cfg)
                elif scene_type == "visitor":
                    actions_taken = self.trigger_visitor_scene(camera_id, person_info, cfg)
                elif scene_type == "intrusion":
                    actions_taken = self.trigger_intrusion_scene(camera_id, person_info, cfg)
                elif scene_type == "delivery":
                    actions_taken = self.trigger_delivery_scene(camera_id, person_info, cfg)
            else:
                logger.info("cam=%s 场景 %s 未配置或未启用，跳过动作执行", camera_id, scene_type)
        except Exception as e:
            logger.exception("场景触发异常 cam=%s scene=%s: %s", camera_id, scene_type, str(e))
            actions_taken.append({"action": "error", "result": str(e)})

        # 5. 落库 OutdoorEvent
        oe = OutdoorEvent.objects.create(
            camera_id=int(camera_id),
            event_type=scene_type or "unknown",
            person_type=person_type,
            person_confidence=confidence,
            timestamp=datetime.now(),
            snapshot_path=snapshot_path or "",
            actions_taken=actions_taken,
            notified=1 if scene_type == "intrusion" else 0,
        )
        logger.info("OutdoorEvent 入库 id=%s cam=%s scene=%s person=%s",
                    oe.id, camera_id, scene_type, person_type)

        return {
            "scene_type": scene_type,
            "person_info": person_info,
            "event_id": oe.id,
            "actions": actions_taken,
        }

    # ----------------------- 2. 身份识别 -----------------------

    def identify_person(self, frame=None, camera_id=None):
        """识别摄像头前的人员身份。

        实现策略（由易到难）：
        1) 如果已经有 ReID 结果写进来（调用方在 frame 上附带 person_type 元信息），直接用；
        2) 调用 VLM 做简单描述，提取人员类型关键词；
        3) 兜底返回 unknown。

        Args:
            frame: 图像数据，可为 bytes/path/base64，或 dict（含 person_type 等元信息）
            camera_id: 可选，仅用于日志

        Returns:
            dict: {"person_type": str, "confidence": float, "detail": str}
        """
        # 如果 frame 本身就是 dict 且已经带 person_type，直接用（上层已识别好）
        if isinstance(frame, dict):
            pt = frame.get("person_type") or self.PERSON_UNKNOWN
            conf = float(frame.get("confidence", 0.8) or 0.8)
            return {"person_type": pt, "confidence": conf, "detail": frame.get("detail", "")}

        person_type = self.PERSON_UNKNOWN
        confidence = 0.0
        detail = ""

        # 尝试调用 VLM
        try:
            from app.services.brain_center import BrainCenter
            bc = BrainCenter()
            if bc._llm_utils is not None and frame is not None:
                image_bytes = bc._normalize_frame(frame)
                if image_bytes is not None:
                    prompt = (
                        "请判断画面中的人是家人(family)、快递员(delivery)、"
                        "访客(visitor)、陌生人(stranger)还是无法识别(unknown)。"
                        "返回严格 JSON："
                        '{"person_type": "family", "confidence": 0.9, "detail": "..." }'
                    )
                    raw = bc._llm_utils.infer(prompt, image_bytes)
                    data = bc._parse_vlm_json(raw)
                    pt = (data.get("person_type") or self.PERSON_UNKNOWN).lower()
                    # 校验合法值
                    allowed = {
                        self.PERSON_FAMILY, self.PERSON_VISITOR,
                        self.PERSON_STRANGER, self.PERSON_DELIVERY, self.PERSON_UNKNOWN,
                    }
                    if pt in allowed:
                        person_type = pt
                        confidence = float(data.get("confidence", 0.6) or 0.6)
                        detail = data.get("detail", "")
        except Exception as e:
            logger.warning("identify_person VLM 识别失败 cam=%s: %s", camera_id, str(e))

        # 兜底：返回 unknown + 低置信度
        return {
            "person_type": person_type,
            "confidence": confidence,
            "detail": detail,
        }

    # ----------------------- 3~5. 场景触发 -----------------------

    def trigger_welcome_scene(self, camera_id, person_info, cfg=None):
        """触发迎宾场景：PTZ 转向预设位 + 灯光开启 + 语音播报。"""
        actions = []
        cfg_dict = self._cfg_to_dict(cfg)
        try:
            preset = cfg_dict.get("ptz_preset", 1)
            actions.append(self.control_ptz(camera_id, "preset", preset))
        except Exception as e:
            actions.append({"action": "ptz", "result": f"error:{e}"})

        try:
            actions.append(self.control_light(camera_id, True, cfg_dict.get("brightness", 80)))
        except Exception as e:
            actions.append({"action": "light", "result": f"error:{e}"})

        try:
            tts = cfg_dict.get("tts_text", "欢迎回家")
            actions.append(self.tts_speak(camera_id, tts))
        except Exception as e:
            actions.append({"action": "tts", "result": f"error:{e}"})

        logger.info("迎宾场景 cam=%s person=%s actions=%d",
                    camera_id, person_info.get("person_type"), len(actions))
        return actions

    def trigger_visitor_scene(self, camera_id, person_info, cfg=None):
        """触发访客接待：PTZ 对准门口 + 灯光柔和 + 语音问候访客。"""
        actions = []
        cfg_dict = self._cfg_to_dict(cfg)
        try:
            preset = cfg_dict.get("ptz_preset", 2)
            actions.append(self.control_ptz(camera_id, "preset", preset))
        except Exception as e:
            actions.append({"action": "ptz", "result": f"error:{e}"})

        try:
            actions.append(self.control_light(camera_id, True, cfg_dict.get("brightness", 60)))
        except Exception as e:
            actions.append({"action": "light", "result": f"error:{e}"})

        try:
            tts = cfg_dict.get("tts_text", "您好，请问找谁？")
            actions.append(self.tts_speak(camera_id, tts))
        except Exception as e:
            actions.append({"action": "tts", "result": f"error:{e}"})

        return actions

    def trigger_intrusion_scene(self, camera_id, person_info, cfg=None):
        """触发入侵防御：PTZ 追踪 + 强光 + 警告语音 + 可选报警通知。"""
        actions = []
        cfg_dict = self._cfg_to_dict(cfg)
        try:
            preset = cfg_dict.get("ptz_preset", 3)
            actions.append(self.control_ptz(camera_id, "preset", preset))
        except Exception as e:
            actions.append({"action": "ptz", "result": f"error:{e}"})

        try:
            actions.append(self.control_light(camera_id, True, cfg_dict.get("brightness", 100)))
        except Exception as e:
            actions.append({"action": "light", "result": f"error:{e}"})

        try:
            tts = cfg_dict.get("tts_text", "这里是私人区域，请立即离开！")
            actions.append(self.tts_speak(camera_id, tts))
        except Exception as e:
            actions.append({"action": "tts", "result": f"error:{e}"})

        logger.warning("入侵场景触发 cam=%s", camera_id)
        return actions

    def trigger_delivery_scene(self, camera_id, person_info, cfg=None):
        """快递识别场景：PTZ 对准 + 灯光 + 语音提示代收。"""
        actions = []
        cfg_dict = self._cfg_to_dict(cfg)
        try:
            preset = cfg_dict.get("ptz_preset", 2)
            actions.append(self.control_ptz(camera_id, "preset", preset))
        except Exception as e:
            actions.append({"action": "ptz", "result": f"error:{e}"})

        try:
            actions.append(self.control_light(camera_id, True, cfg_dict.get("brightness", 80)))
        except Exception as e:
            actions.append({"action": "light", "result": f"error:{e}"})

        try:
            tts = cfg_dict.get("tts_text", "快递已到门口，请查收。")
            actions.append(self.tts_speak(camera_id, tts))
        except Exception as e:
            actions.append({"action": "tts", "result": f"error:{e}"})

        return actions

    # ----------------------- 6~8. 设备控制 -----------------------

    def control_ptz(self, camera_id, direction, angle):
        """PTZ 控制：调用 ONVIF 工具或 stub。

        Args:
            direction: 方向或 preset 名称 — left/right/up/down/preset
            angle: 角度数值或预设位编号

        Returns:
            dict: {"action": "ptz", "camera_id": int, "direction": str, "angle": any, "result": str}
        """
        result = "ok"
        try:
            # 先尝试调用已有的 ONVIF PTZ（如项目中存在）
            try:
                from app.services.onvif_discovery import discover_onvif  # noqa: F401
                # 项目目前只有 discovery，没有真正的 PTZ 控制；
                # 这里预留扩展点，直接做 log
                logger.info("PTZ 控制 cam=%s direction=%s angle=%s (ONVIF 未真正实现)",
                            camera_id, direction, angle)
            except Exception:
                logger.debug("onvif_discovery 导入失败，跳过 ONVIF 调用")
        except Exception as e:
            result = f"error:{e}"
            logger.warning("control_ptz 失败 cam=%s: %s", camera_id, str(e))

        return {
            "action": "ptz",
            "camera_id": int(camera_id),
            "direction": direction,
            "angle": angle,
            "result": result,
        }

    def control_light(self, camera_id, on_off, brightness=80):
        """灯光控制（stub，实际可对接 HomeKit / 局域网开关）。"""
        result = "ok"
        try:
            logger.info("灯光控制 cam=%s on=%s brightness=%s", camera_id, on_off, brightness)
        except Exception as e:
            result = f"error:{e}"
        return {
            "action": "light",
            "camera_id": int(camera_id),
            "on": bool(on_off),
            "brightness": int(brightness),
            "result": result,
        }

    def tts_speak(self, camera_id, text):
        """语音播报（stub，实际可对接本地 TTS / 小米小爱 / HomePod 等）。"""
        result = "ok"
        try:
            logger.info("TTS 播报 cam=%s text=%s", camera_id, text)
        except Exception as e:
            result = f"error:{e}"
        return {
            "action": "tts",
            "camera_id": int(camera_id),
            "text": text,
            "result": result,
        }

    # ----------------------- 工具方法 -----------------------

    @staticmethod
    def _cfg_to_dict(cfg):
        """OutdoorSceneConfig 对象 → dict（兼容 None 与 dict 输入）。"""
        if cfg is None:
            return {}
        if isinstance(cfg, dict):
            return cfg
        return getattr(cfg, "config", {}) or {}

    @staticmethod
    def get_scene_configs(camera_id):
        """查询某摄像头的全部场景配置。"""
        return list(OutdoorSceneConfig.objects.filter(camera_id=camera_id))

    @staticmethod
    def upsert_scene_config(camera_id, scene_type, enabled=True, config=None):
        """更新或创建一个场景配置。"""
        obj = OutdoorSceneConfig.objects.filter(camera_id=camera_id, scene_type=scene_type).first()
        if obj is None:
            obj = OutdoorSceneConfig(
                camera_id=int(camera_id),
                scene_type=scene_type,
                enabled=1 if enabled else 0,
                config=config or {},
            )
        else:
            obj.enabled = 1 if enabled else 0
            if config is not None:
                obj.config = config
            obj.last_update_time = datetime.now()
        obj.save()
        return obj
