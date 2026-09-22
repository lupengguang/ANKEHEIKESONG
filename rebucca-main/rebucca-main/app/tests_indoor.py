# -*- coding: utf-8 -*-
"""
室内互动 / 无网场景 / 设备联动中枢 三模块单元测试 — Django TestCase。

运行：python manage.py test app.tests_indoor -v 2
不依赖硬件与真实模型：检测结果通过 frame(dict) 注入。
"""
import json
from datetime import datetime

from django.test import TestCase, RequestFactory

from app.models import (
    IndoorEvent, OfflineEvent, Device, DeviceCommand,
)
from app.services.indoor_scene import IndoorSceneEngine
from app.services.offline_scene import OfflineSceneEngine
from app.services.device_hub import DeviceHub, with_retry

from app import indoor_api, offline_api, device_api


def _cat_frame():
    return {"detections": [
        {"label": "cat", "confidence": 0.98, "bbox": [120, 90, 300, 360]}]}


def _dog_frame():
    return {"detections": [
        {"label": "dog", "confidence": 0.95, "bbox": [10, 20, 200, 400]}]}


def _person_frame():
    return {"detections": [
        {"label": "person", "confidence": 0.97, "bbox": [60, 40, 420, 520]}]}


# =====================================================================
# 一、室内互动场景
# =====================================================================

class IndoorEngineTests(TestCase):
    """IndoorSceneEngine 四大模式服务层测试。"""

    def setUp(self):
        self.engine = IndoorSceneEngine()

    def test_default_config(self):
        cfg = self.engine.get_effective_config(1)
        self.assertTrue(cfg["pet_mode_enabled"])
        self.assertTrue(cfg["elder_mode_enabled"])
        self.assertEqual(cfg["night_start"], "22:00")
        self.assertEqual(cfg["sensitivity"], 8)

    def test_pet_mode(self):
        r = self.engine.pet_mode(1, _cat_frame())
        self.assertTrue(r["triggered"])
        self.assertEqual(r["animal"], "cat")
        # PTZ + spotlight + 音频 三个动作
        self.assertEqual(len(r["actions"]), 3)
        self.assertTrue(r["clip_path"].endswith(".mp4"))
        ev = IndoorEvent.objects.get(id=r["event_id"])
        self.assertEqual(ev.event_type, "pet_detected")
        self.assertEqual(ev.scene_mode, "pet")
        self.assertFalse(bool(ev.notified))

    def test_pet_mode_no_animal(self):
        r = self.engine.pet_mode(1, {"detections": []})
        self.assertFalse(r["triggered"])

    def test_elder_fall(self):
        r = self.engine.elder_mode(1, {"fall": True})
        self.assertTrue(r["triggered"])
        self.assertEqual(r["event_type"], "elder_fall")
        self.assertEqual(len(r["actions"]), 2)   # 告警 + 语音询问
        ev = IndoorEvent.objects.get(id=r["event_id"])
        self.assertTrue(bool(ev.notified))        # 已通知子女

    def test_elder_stationary(self):
        r = self.engine.elder_mode(1, {"stationary_frames": 90})
        self.assertTrue(r["triggered"])
        self.assertEqual(r["event_type"], "elder_stationary")

    def test_elder_normal(self):
        r = self.engine.elder_mode(1, {"fall": False, "stationary_frames": 3})
        self.assertFalse(r["triggered"])

    def test_child_danger_zone(self):
        r = self.engine.child_mode(1, {"zone": "kitchen"})
        self.assertTrue(r["triggered"])
        self.assertEqual(r["zone"], "kitchen")
        self.assertEqual(
            r["actions"][0]["payload"]["audio_url"],
            IndoorSceneEngine.AUDIO_CHILD_WARN,
        )

    def test_child_safe_zone(self):
        r = self.engine.child_mode(1, {"zone": "living_room"})
        self.assertFalse(r["triggered"])

    def test_night_mode(self):
        cfg = self.engine.get_effective_config(1)
        r = self.engine.night_mode(1, _person_frame(), cfg=cfg)
        self.assertTrue(r["triggered"])
        # 夜间灯光为调暗亮度
        light_action = r["actions"][0]
        self.assertEqual(light_action["action"], "light")
        self.assertEqual(light_action["payload"]["brightness"], 20)

    def test_night_window_logic(self):
        self.assertTrue(self.engine.in_night_window(
            self.engine.DEFAULT_CONFIG, now=datetime(2026, 1, 1, 23, 0)))
        self.assertTrue(self.engine.in_night_window(
            self.engine.DEFAULT_CONFIG, now=datetime(2026, 1, 1, 3, 0)))
        self.assertFalse(self.engine.in_night_window(
            self.engine.DEFAULT_CONFIG, now=datetime(2026, 1, 1, 12, 0)))

    def test_on_motion_routing(self):
        r = self.engine.on_motion_detected(1, _cat_frame())
        # 白天：pet/elder/child 三模式参与检测，仅 pet 触发
        self.assertEqual(r["triggered_count"], 1)

    def test_mode_row_disabled(self):
        """独立模式配置行 enabled=0 时该模式不执行。"""
        IndoorSceneEngine.upsert_config(1, "pet", enabled=False)
        r = self.engine.on_motion_detected(1, _cat_frame())
        self.assertEqual(r["triggered_count"], 0)


class IndoorApiTests(TestCase):
    """室内 API 与热更新测试。"""

    def setUp(self):
        self.rf = RequestFactory()

    def _get(self, path, params=None):
        return indoor_api.indoor_config_dispatch(
            self.rf.get(path, params or {}))

    def test_get_config(self):
        resp = indoor_api.indoor_config(
            self.rf.get("/api/indoor/config", {"camera_id": 1}))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "success")
        self.assertTrue(body["data"]["effective"]["pet_mode_enabled"])

    def test_get_config_missing_camera(self):
        resp = indoor_api.indoor_config(self.rf.get("/api/indoor/config"))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 400)

    def test_put_config_hot_reload(self):
        body_in = {"camera_id": 1, "scene_type": "general",
                   "enabled": True,
                   "config": {"pet_mode_enabled": False, "sensitivity": 3}}
        resp = indoor_api.indoor_config_update(
            self.rf.put("/api/indoor/config",
                        data=json.dumps(body_in),
                        content_type="application/json"))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        # 热更新：不新建引擎，立即读到新值
        cfg = IndoorSceneEngine().get_effective_config(1)
        self.assertFalse(cfg["pet_mode_enabled"])
        self.assertEqual(cfg["sensitivity"], 3)

    def test_test_pet(self):
        resp = indoor_api.indoor_test_pet(
            self.rf.post("/api/indoor/test-pet",
                         data=json.dumps({"camera_id": 1}),
                         content_type="application/json"))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertTrue(body["data"]["triggered"])

    def test_test_elder(self):
        resp = indoor_api.indoor_test_elder(
            self.rf.post("/api/indoor/test-elder",
                         data=json.dumps({"camera_id": 1}),
                         content_type="application/json"))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["data"]["event_type"], "elder_fall")

    def test_events(self):
        IndoorSceneEngine().test_pet(1)
        resp = indoor_api.indoor_events(
            self.rf.get("/api/indoor/events", {"camera_id": 1}))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["event_type"], "pet_detected")


# =====================================================================
# 二、无网场景
# =====================================================================

class OfflineEngineTests(TestCase):
    """OfflineSceneEngine 服务层测试。"""

    def setUp(self):
        self.engine = OfflineSceneEngine()
        OfflineSceneEngine.network_available = True

    def tearDown(self):
        OfflineSceneEngine.network_available = True

    def test_default_config(self):
        cfg = self.engine.get_effective_config(1)
        self.assertTrue(cfg["intrusion_enabled"])
        self.assertTrue(cfg["low_bandwidth_mode"])
        self.assertEqual(cfg["buffer_size_limit"], 100)

    def test_intrusion_mode(self):
        r = self.engine.intrusion_mode(1, _person_frame())
        self.assertTrue(r["triggered"])
        # 100 流明补光灯
        self.assertEqual(r["actions"][0]["payload"]["brightness"], 100)
        # 告警事件上传视频
        self.assertTrue(r["upload_policy"]["upload_video"])
        ev = OfflineEvent.objects.get(id=r["event_id"])
        self.assertEqual(ev.event_type, "intrusion")
        self.assertTrue(ev.video_path.endswith(".mp4"))

    def test_animal_keyframe_only(self):
        r = self.engine.animal_monitor(1, _dog_frame())
        self.assertTrue(r["triggered"])
        self.assertEqual(r["animal"], "dog")
        self.assertTrue(r["upload_policy"]["keyframe_only"])
        self.assertFalse(r["upload_policy"]["upload_video"])
        ev = OfflineEvent.objects.get(id=r["event_id"])
        self.assertEqual(ev.video_path, "")

    def test_offline_buffer_and_replay(self):
        # 1. 断网：事件本地缓存
        OfflineSceneEngine.network_available = False
        r = self.engine.intrusion_mode(1, _person_frame())
        self.assertTrue(r["buffered"])
        ev = OfflineEvent.objects.get(id=r["event_id"])
        self.assertEqual(ev.is_replayed, 0)
        self.assertIsNone(ev.replayed_at)

        # 2. 未恢复网络 → 等待补传
        waiting = self.engine.offline_buffer_replay(1)
        self.assertFalse(waiting["replayed"])

        # 3. 网络恢复 → 自动补传
        OfflineSceneEngine.network_available = True
        result = self.engine.offline_buffer_replay(1)
        self.assertTrue(result["replayed"])
        self.assertEqual(result["count"], 1)
        ev.refresh_from_db()
        self.assertEqual(ev.is_replayed, 1)
        self.assertIsNotNone(ev.replayed_at)

    def test_stats(self):
        self.engine.intrusion_mode(1, _person_frame())
        stats = OfflineSceneEngine.get_stats(1)
        self.assertEqual(stats["total_events"], 1)
        self.assertEqual(stats["intrusion_events"], 1)
        self.assertGreater(stats["bytes_video_uploaded"], 0)


class OfflineApiTests(TestCase):
    """无网场景 API 测试。"""

    def setUp(self):
        self.rf = RequestFactory()
        OfflineSceneEngine.network_available = True

    def tearDown(self):
        OfflineSceneEngine.network_available = True

    def test_get_config(self):
        resp = offline_api.offline_config(
            self.rf.get("/api/offline/config", {"camera_id": 1}))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertTrue(body["data"]["effective"]["offline_buffer_enabled"])

    def test_put_config(self):
        body_in = {"camera_id": 1, "enabled": True,
                   "config": {"buffer_size_limit": 50}}
        resp = offline_api.offline_config_update(
            self.rf.put("/api/offline/config",
                        data=json.dumps(body_in),
                        content_type="application/json"))
        self.assertEqual(json.loads(resp.content)["code"], 200)
        cfg = OfflineSceneEngine().get_effective_config(1)
        self.assertEqual(cfg["buffer_size_limit"], 50)  # 热更新生效

    def test_test_intrusion(self):
        resp = offline_api.offline_test_intrusion(
            self.rf.post("/api/offline/test-intrusion",
                         data=json.dumps({"camera_id": 1}),
                         content_type="application/json"))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertTrue(body["data"]["triggered"])

    def test_events_and_stats(self):
        OfflineSceneEngine().test_intrusion(1)
        resp = offline_api.offline_events(
            self.rf.get("/api/offline/events", {"camera_id": 1}))
        self.assertEqual(json.loads(resp.content)["data"][0]["event_type"],
                         "intrusion")
        resp = offline_api.offline_stats(
            self.rf.get("/api/offline/stats", {"camera_id": 1}))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["data"]["total_events"], 1)

    def test_replay_endpoint(self):
        OfflineSceneEngine.network_available = False
        OfflineSceneEngine().intrusion_mode(1, _person_frame())
        OfflineSceneEngine.network_available = True
        resp = offline_api.offline_replay(
            self.rf.post("/api/offline/replay",
                         data=json.dumps({"camera_id": 1}),
                         content_type="application/json"))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["data"]["count"], 1)


# =====================================================================
# 三、设备联动中枢
# =====================================================================

class DeviceHubTests(TestCase):
    """DeviceHub 服务层测试。"""

    def setUp(self):
        self.hub = DeviceHub()
        DeviceHub._track_handoffs.clear()
        DeviceHub._topology.clear()
        DeviceHub._subscribers = {"*": []}

    def test_register_and_status(self):
        info = {"device_id": "cam-1", "name": "门口机", "type": "outdoor",
                "ip": "192.168.1.10", "battery": 80}
        data = self.hub.register_device(info)
        self.assertEqual(data["device_id"], "cam-1")
        status = self.hub.get_device_status("cam-1")
        self.assertTrue(status["registered"])
        self.assertEqual(status["battery"], 80)

    def test_status_unknown_device(self):
        status = self.hub.get_device_status("no-such")
        self.assertFalse(status["registered"])

    def test_register_requires_id(self):
        with self.assertRaises(ValueError):
            self.hub.register_device({"name": "x"})

    def test_commands_logged(self):
        r1 = self.hub.control_ptz("cam-1", "left", 90)
        r2 = self.hub.control_light("cam-1", True, 60)
        r3 = self.hub.play_audio("cam-1", "https://a/b.mp3")
        self.assertEqual(r1["result"], "ok")
        cmds = DeviceCommand.objects.filter(
            id__in=[r1["command_id"], r2["command_id"], r3["command_id"]])
        self.assertEqual(cmds.count(), 3)
        self.assertTrue(all(c.status == DeviceCommand.STATUS_SUCCESS for c in cmds))

    def test_command_failed_after_retries(self):
        """下发始终失败：命令重试 3 次后标记 failed。"""
        def _boom(device, command_type, payload):
            raise RuntimeError("device unreachable")
        self.hub._send_command = _boom
        r = self.hub.control_ptz("cam-1", "left", 90)
        self.assertTrue(r["result"].startswith("error"))
        cmd = DeviceCommand.objects.get(id=r["command_id"])
        self.assertEqual(cmd.status, DeviceCommand.STATUS_FAILED)
        self.assertIsNotNone(cmd.executed_at)

    def test_cross_camera_track_debounce(self):
        DeviceHub.set_camera_neighbors("cam-a", ["cam-b"])
        r1 = self.hub.cross_camera_track("cam-a", "track-1")
        self.assertEqual(r1["result"], "handoff")
        # 立即再次触发 → 防抖命中
        r2 = self.hub.cross_camera_track("cam-a", "track-1")
        self.assertEqual(r2["result"], "debounced")
        # 不同轨迹 → 正常执行
        r3 = self.hub.cross_camera_track("cam-a", "track-2")
        self.assertEqual(r3["result"], "handoff")

    def test_cross_camera_no_target(self):
        r = self.hub.cross_camera_track("cam-x", "track-9")
        self.assertEqual(r["result"], "no_target")

    def test_event_broadcast(self):
        received = []
        self.hub.subscribe("cam-b", lambda ev: received.append(ev))
        self.hub.event_broadcast({"type": "test", "targets": ["cam-b"]})
        self.assertEqual(len(received), 1)
        # broadcast 对目标设备留痕
        self.assertTrue(DeviceCommand.objects.filter(
            command_type="broadcast").exists())

    def test_command_history(self):
        self.hub.control_ptz("cam-1", "left", 10)
        history = DeviceHub.get_command_history(limit=10)
        self.assertGreaterEqual(len(history), 1)

    def test_with_retry_success_after_failures(self):
        """重试机制单元验证：前两次失败、第三次成功。"""
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise RuntimeError("temporary")
            return "done"

        self.assertEqual(
            with_retry(flaky, attempts=3, base_delay=0.01), "done")
        self.assertEqual(calls["n"], 3)


class DeviceApiTests(TestCase):
    """设备联动 API 测试。"""

    def setUp(self):
        self.rf = RequestFactory()
        DeviceHub._track_handoffs.clear()
        DeviceHub._topology.clear()
        DeviceHub._subscribers = {"*": []}

    def _post(self, path, payload):
        return self.rf.post(path, data=json.dumps(payload),
                            content_type="application/json")

    def test_register_and_list(self):
        resp = device_api.device_register(self._post(
            "/api/devices/register",
            {"device_id": "cam-1", "type": "4g", "name": "果园机"}))
        self.assertEqual(json.loads(resp.content)["code"], 200)
        resp = device_api.devices_list(self.rf.get("/api/devices"))
        body = json.loads(resp.content)
        # 0004 迁移会预置 3 台种子设备，按编号精确校验本次注册结果
        matched = [d for d in body["data"] if d["device_id"] == "cam-1"]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["name"], "果园机")

    def test_status_ptz_light_audio(self):
        device_api.device_register(self._post(
            "/api/devices/register", {"device_id": "cam-1"}))

        resp = device_api.device_status(
            self.rf.get("/api/devices/cam-1/status"), "cam-1")
        self.assertTrue(json.loads(resp.content)["data"]["registered"])

        resp = device_api.device_ptz(
            self._post("/api/devices/cam-1/ptz",
                       {"direction": "right", "angle": 45}), "cam-1")
        self.assertEqual(json.loads(resp.content)["code"], 200)

        resp = device_api.device_light(
            self._post("/api/devices/cam-1/light",
                       {"on_off": True, "brightness": 100}), "cam-1")
        self.assertEqual(json.loads(resp.content)["code"], 200)

        resp = device_api.device_audio(
            self._post("/api/devices/cam-1/audio",
                       {"audio_url": "https://a/b.mp3"}), "cam-1")
        self.assertEqual(json.loads(resp.content)["code"], 200)

    def test_commands_endpoint(self):
        device_api.device_register(self._post(
            "/api/devices/register", {"device_id": "cam-1"}))
        device_api.device_ptz(
            self._post("/api/devices/cam-1/ptz", {"direction": "up"}), "cam-1")
        resp = device_api.commands_list(
            self.rf.get("/api/devices/commands", {"device_id": "cam-1"}))
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["command_type"], "ptz")

    def test_cross_track_endpoint(self):
        DeviceHub.set_camera_neighbors("cam-a", ["cam-b"])
        resp = device_api.device_cross_track(
            self._post("/api/devices/cam-a/cross-track",
                       {"track_id": "t1"}), "cam-a")
        body = json.loads(resp.content)
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["data"]["result"], "handoff")
