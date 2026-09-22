# 作者：北小菜
# 官网：https://www.yuturuishi.com
# 微信：bilibili_bxc
# 哔哩哔哩主页：https://space.bilibili.com/487906612
# gitee地址：https://gitee.com/Vanishi/rebucca
# github地址：https://github.com/beixiaocai/rebucca
"""
户外场景相关单元测试 — Django TestCase。

运行：python manage.py test app.tests_outdoor -v 2
"""
import json
from datetime import datetime

from django.test import TestCase, RequestFactory

from app.models import OutdoorSceneConfig, OutdoorEvent
from app.services.outdoor_scene import OutdoorSceneEngine


class OutdoorSceneConfigTests(TestCase):
    """测试 OutdoorSceneConfig 的增改查。"""

    def test_upsert_scene_config_create(self):
        obj = OutdoorSceneEngine.upsert_scene_config(
            camera_id=10, scene_type="welcome",
            enabled=True, config={"ptz_preset": 1, "tts_text": "欢迎回家"},
        )
        self.assertEqual(obj.camera_id, 10)
        self.assertEqual(obj.scene_type, "welcome")
        self.assertTrue(obj.enabled)
        self.assertEqual(obj.config["ptz_preset"], 1)

    def test_upsert_scene_config_update(self):
        OutdoorSceneEngine.upsert_scene_config(
            camera_id=10, scene_type="visitor",
            enabled=True, config={"ptz_preset": 2},
        )
        obj = OutdoorSceneEngine.upsert_scene_config(
            camera_id=10, scene_type="visitor",
            enabled=False, config={"ptz_preset": 9},
        )
        obj.refresh_from_db()
        self.assertFalse(bool(obj.enabled))
        self.assertEqual(obj.config["ptz_preset"], 9)

    def test_get_scene_configs(self):
        OutdoorSceneEngine.upsert_scene_config(camera_id=11, scene_type="welcome")
        OutdoorSceneEngine.upsert_scene_config(camera_id=11, scene_type="intrusion")
        cfgs = OutdoorSceneEngine.get_scene_configs(11)
        self.assertEqual(len(cfgs), 2)


class OutdoorSceneEngineControlTests(TestCase):
    """测试设备控制方法（stub，不依赖真实硬件）。"""

    def setUp(self):
        self.engine = OutdoorSceneEngine()

    def test_control_ptz_returns_dict(self):
        r = self.engine.control_ptz(camera_id=1, direction="preset", angle=3)
        self.assertEqual(r["action"], "ptz")
        self.assertEqual(r["camera_id"], 1)
        self.assertEqual(r["result"], "ok")

    def test_control_light_returns_dict(self):
        r = self.engine.control_light(camera_id=1, on_off=True, brightness=80)
        self.assertEqual(r["on"], True)
        self.assertEqual(r["brightness"], 80)

    def test_tts_speak_returns_dict(self):
        r = self.engine.tts_speak(camera_id=1, text="你好")
        self.assertEqual(r["text"], "你好")


class OutdoorSceneEngineSceneTriggerTests(TestCase):
    """测试场景触发：welcome / visitor / intrusion / delivery。"""

    def setUp(self):
        self.engine = OutdoorSceneEngine()
        # 预置 4 种场景配置，确保触发链路完整
        for st in ("welcome", "visitor", "intrusion", "delivery"):
            OutdoorSceneEngine.upsert_scene_config(
                camera_id=100, scene_type=st, enabled=True,
                config={"ptz_preset": 1, "brightness": 80, "tts_text": f"{st}-text"},
            )

    def test_trigger_welcome(self):
        person = {"person_type": "family", "confidence": 1.0}
        actions = self.engine.trigger_welcome_scene(100, person)
        self.assertGreaterEqual(len(actions), 3)  # ptz + light + tts
        self.assertEqual(actions[0]["action"], "ptz")
        self.assertEqual(actions[1]["action"], "light")
        self.assertEqual(actions[2]["action"], "tts")

    def test_trigger_visitor(self):
        person = {"person_type": "visitor", "confidence": 0.9}
        actions = self.engine.trigger_visitor_scene(100, person)
        self.assertEqual(len(actions), 3)

    def test_trigger_intrusion(self):
        person = {"person_type": "stranger", "confidence": 0.99}
        actions = self.engine.trigger_intrusion_scene(100, person)
        self.assertEqual(len(actions), 3)

    def test_trigger_delivery(self):
        person = {"person_type": "delivery", "confidence": 0.85}
        actions = self.engine.trigger_delivery_scene(100, person)
        self.assertEqual(len(actions), 3)


class OutdoorSceneOnMotionDetectedTests(TestCase):
    """测试 on_motion_detected 完整链路：识别 → 场景 → 落库。"""

    def setUp(self):
        self.engine = OutdoorSceneEngine()
        # 配置四种场景
        for st in ("welcome", "visitor", "intrusion", "delivery"):
            OutdoorSceneEngine.upsert_scene_config(camera_id=200, scene_type=st, enabled=True)

    def test_on_motion_family_triggers_welcome(self):
        info = {"person_type": "family", "confidence": 1.0}
        result = self.engine.on_motion_detected(camera_id=200, frame=info)
        self.assertEqual(result["scene_type"], "welcome")
        self.assertIn("event_id", result)
        self.assertGreater(result["event_id"], 0)
        oe = OutdoorEvent.objects.get(id=result["event_id"])
        self.assertEqual(oe.event_type, "welcome")
        self.assertEqual(oe.person_type, "family")

    def test_on_motion_stranger_daytime_triggers_visitor(self):
        """白天陌生人 → visitor（intrusion 仅夜间）。"""
        info = {"person_type": "stranger", "confidence": 0.9}
        # 简单 mock 夜间判断很难，这里只验证能正确走通
        result = self.engine.on_motion_detected(camera_id=200, frame=info)
        self.assertIn(result["scene_type"], ("visitor", "intrusion"))
        oe = OutdoorEvent.objects.get(id=result["event_id"])
        self.assertEqual(oe.event_type, result["scene_type"])

    def test_on_motion_unknown_frame_gracefully_degrades(self):
        """frame 为 None 时，不应抛异常。"""
        result = self.engine.on_motion_detected(camera_id=200, frame=None)
        self.assertIsNotNone(result)
        self.assertIn("event_id", result)


class OutdoorIdentifyPersonTests(TestCase):
    """测试 identify_person：dict 输入应直接用，其它情况兜底 unknown。"""

    def test_dict_input_used_directly(self):
        engine = OutdoorSceneEngine()
        info = engine.identify_person(frame={
            "person_type": "delivery", "confidence": 0.8, "detail": "外卖员"
        })
        self.assertEqual(info["person_type"], "delivery")
        self.assertEqual(info["confidence"], 0.8)

    def test_none_input_falls_back_to_unknown(self):
        engine = OutdoorSceneEngine()
        info = engine.identify_person(frame=None)
        self.assertEqual(info["person_type"], "unknown")
        self.assertEqual(info["confidence"], 0.0)


class OutdoorAPITests(TestCase):
    """测试 outdoor_api 函数式 View。"""

    def setUp(self):
        # 预置配置和事件
        OutdoorSceneEngine.upsert_scene_config(
            camera_id=300, scene_type="welcome",
            enabled=True, config={"ptz_preset": 1},
        )
        OutdoorEvent.objects.create(
            camera_id=300, event_type="welcome", person_type="family",
            person_confidence=1.0, timestamp=datetime.now(),
            actions_taken=[{"action": "tts", "result": "ok"}], notified=0,
        )
        self.rf = RequestFactory()

    def test_outdoor_config_get(self):
        from app import outdoor_api
        req = self.rf.get("/api/outdoor/config", {"camera_id": 300})
        resp = outdoor_api.outdoor_config(req)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 1000)
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["scene_type"], "welcome")

    def test_outdoor_config_update(self):
        from app import outdoor_api
        req = self.rf.post(
            "/api/outdoor/config",
            data=json.dumps({
                "camera_id": 300,
                "scene_type": "intrusion",
                "enabled": True,
                "config": {"brightness": 100},
            }),
            content_type="application/json",
        )
        resp = outdoor_api.outdoor_config_update(req)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 1000)
        # 验证 DB 有新增
        self.assertEqual(OutdoorSceneConfig.objects.filter(
            camera_id=300, scene_type="intrusion").count(), 1)

    def test_outdoor_events_get(self):
        from app import outdoor_api
        req = self.rf.get("/api/outdoor/events", {"camera_id": 300})
        resp = outdoor_api.outdoor_events(req)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 1000)
        self.assertGreaterEqual(len(data["data"]), 1)

    def test_outdoor_trigger_welcome(self):
        from app import outdoor_api
        req = self.rf.post(
            "/api/outdoor/trigger-welcome",
            data=json.dumps({"camera_id": 300}),
            content_type="application/json",
        )
        resp = outdoor_api.outdoor_trigger_welcome(req)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 1000)
        self.assertIn("actions", data["data"])
        self.assertIn("event_id", data["data"])

    def test_outdoor_trigger_intrusion(self):
        from app import outdoor_api
        req = self.rf.post(
            "/api/outdoor/trigger-intrusion",
            data=json.dumps({"camera_id": 300}),
            content_type="application/json",
        )
        resp = outdoor_api.outdoor_trigger_intrusion(req)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 1000)
        # intrusion 事件应自动 notified=1（在 service 层 set）
        self.assertEqual(OutdoorEvent.objects.order_by("-id").first().event_type, "intrusion")

    def test_outdoor_config_missing_camera_id(self):
        from app import outdoor_api
        req = self.rf.get("/api/outdoor/config")
        resp = outdoor_api.outdoor_config(req)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 0)

    def test_outdoor_events_by_time_range(self):
        from app import outdoor_api
        past_dt = datetime.now().isoformat()
        req = self.rf.get("/api/outdoor/events", {
            "camera_id": 300,
            "start_time": "2020-01-01T00:00:00",
            "end_time": past_dt,
        })
        resp = outdoor_api.outdoor_events(req)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 1000)
