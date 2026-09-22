# -*- coding: utf-8 -*-
"""
本地摄像头 + VLM 迎宾闭环 单元测试。

覆盖：
  - LocalCameraStream：无摄像头时友好返回（不抛异常）
  - WelcomeSceneEngine：离开不触发 / 靠近触发 / 5 秒防抖
  - 告警落库：scene_type / ai_description / triggered_actions / snapshot
  - camera API：状态、场景配置存取、告警筛选
"""
import time

import numpy as np

from django.test import TestCase, Client

from app.services.video_stream import LocalCameraStream
from app.services.welcome_scene import WelcomeSceneEngine
from app.services.device_control import MockDeviceControl
from app.models import AlarmModel


class FakeManager:
    """迎宾引擎所需的管理器桩。"""

    def __init__(self, frame):
        self._frame = frame
        self.frame_count = 0

    def get_latest_frame(self):
        return self._frame


class LocalCameraStreamTest(TestCase):
    """无摄像头（越界索引）时不崩溃、有友好错误。"""

    def test_invalid_index_does_not_raise(self):
        stream = LocalCameraStream(99)
        # 本机若无摄像头则必须 opened=False 且有错误信息；
        # 极端情况下系统有第 100 个摄像头时跳过
        if stream.is_opened():
            stream.release()
            return
        self.assertFalse(stream.is_opened())
        self.assertTrue(stream.last_error)
        ok, frame = stream.get_frame()
        self.assertFalse(ok)
        self.assertIsNone(frame)
        # release 幂等不报错
        stream.release()


class WelcomeSceneEngineTest(TestCase):
    """迎宾引擎判定 / 防抖 / 落库。"""

    def setUp(self):
        self.frame = np.zeros((120, 160, 3), dtype=np.uint8)
        self.manager = FakeManager(self.frame)
        self.control = MockDeviceControl("local-cam")
        self.engine = WelcomeSceneEngine(
            self.manager, frame_interval=5, control=self.control)

    def test_leaving_does_not_trigger(self):
        result = self.engine.evaluate(
            self.frame,
            {"has_person": True, "direction": "leaving",
             "age_group": "adult", "source": "mock"})
        self.assertIsNone(result)
        self.assertEqual(AlarmModel.objects.count(), 0)

    def test_no_person_does_not_trigger(self):
        result = self.engine.evaluate(
            self.frame,
            {"has_person": False, "direction": "approaching",
             "age_group": "adult", "source": "mock"})
        self.assertIsNone(result)

    def test_approaching_triggers_and_persists(self):
        result = self.engine.evaluate(
            self.frame,
            {"has_person": True, "direction": "approaching",
             "age_group": "elder", "source": "mock"})
        self.assertEqual(result["result"], "triggered")

        alert = AlarmModel.objects.latest("id")
        self.assertEqual(alert.scene_type, "welcome")
        self.assertIn("靠近", alert.ai_description)
        self.assertIn("elder", alert.ai_description)
        # 三个动作：ptz / light / tts
        action_names = [a["action"] for a in alert.triggered_actions]
        self.assertEqual(action_names, ["ptz", "light", "tts"])

    def test_debounce_within_5_seconds(self):
        r1 = self.engine.evaluate(
            self.frame,
            {"has_person": True, "direction": "approaching",
             "age_group": "adult", "source": "mock"})
        r2 = self.engine.evaluate(
            self.frame,
            {"has_person": True, "direction": "approaching",
             "age_group": "adult", "source": "mock"})
        self.assertEqual(r1["result"], "triggered")
        self.assertEqual(r2["result"], "debounced")
        self.assertEqual(AlarmModel.objects.count(), 1)

        # 超过防抖窗口后可再次触发
        self.engine._last_trigger_ts = time.time() - 6
        r3 = self.engine.evaluate(
            self.frame,
            {"has_person": True, "direction": "approaching",
             "age_group": "adult", "source": "mock"})
        self.assertEqual(r3["result"], "triggered")
        self.assertEqual(AlarmModel.objects.count(), 2)


class CameraApiTest(TestCase):
    """camera_api 接口行为（绕过鉴权中间件，直接 Client 调 View 路由）。"""

    def setUp(self):
        # 直接登录态：在 session 中写入用户标记
        session = self.client.session
        session["user"] = "admin"
        session.save()

    def test_camera_status_structure(self):
        resp = self.client.get("/api/camera/status")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 200)
        self.assertIn("running", body["data"])
        self.assertIn("width", body["data"])

    def test_scene_config_default_and_update(self):
        resp = self.client.get("/api/scene/config")
        body = resp.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(len(body["data"]), 4)

        resp = self.client.put(
            "/api/scene/config",
            data='{"scene_type":"welcome","enabled":false,"sensitivity":8}',
            content_type="application/json")
        body = resp.json()
        self.assertEqual(body["code"], 200)
        welcome = [s for s in body["data"] if s["scene_type"] == "welcome"][0]
        self.assertFalse(welcome["enabled"])
        self.assertEqual(welcome["sensitivity"], 8)

    def test_alerts_filter_by_scene_type(self):
        AlarmModel.objects.create(
            event_type="welcome", description="测试迎宾",
            timestamp=__import__("datetime").datetime.now(),
            scene_type="welcome", ai_description="AI迎宾分析")
        resp = self.client.get("/api/alerts?scene_type=welcome")
        body = resp.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["ai_description"], "AI迎宾分析")

        # 筛选不存在的场景
        resp = self.client.get("/api/alerts?scene_type=pet")
        self.assertEqual(resp.json()["data"], [])
