# 作者：北小菜
# 官网：https://www.yuturuishi.com
# 微信：bilibili_bxc
# 哔哩哔哩主页：https://space.bilibili.com/487906612
# gitee地址：https://gitee.com/Vanishi/rebucca
# github地址：https://github.com/beixiaocai/rebucca
"""
脑中枢相关单元测试 — Django TestCase。

运行：python manage.py test app.tests_brain -v 2
"""
import io
import json
from datetime import datetime, timedelta, date

from django.test import TestCase

from app.models import BrainEvent, BehaviorTrack, WeeklyReport
from app.services.brain_center import BrainCenter


class BrainCenterProcessEventTests(TestCase):
    """测试 process_event：无真实 VLM 时应兜底写入 BrainEvent。"""

    def setUp(self):
        self.bc = BrainCenter()  # 未配置 LLMModel 也能跑（VLM 返回空）

    def test_process_event_returns_id(self):
        result = self.bc.process_event(
            camera_id=1,
            frame=None,
            event_type="motion",
            track_id=None,
        )
        self.assertIn("brain_event_id", result)
        self.assertGreater(result["brain_event_id"], 0)

    def test_process_event_db_persist(self):
        before = BrainEvent.objects.count()
        self.bc.process_event(camera_id=2, frame=None, event_type="intrusion")
        after = BrainEvent.objects.count()
        self.assertEqual(after, before + 1)

        be = BrainEvent.objects.order_by("-id").first()
        self.assertEqual(be.camera_id, 2)
        self.assertEqual(be.event_type, "intrusion")
        # intrusion 应该让 anomaly_score 达到 0.95
        self.assertGreaterEqual(be.anomaly_score, 0.95)

    def test_process_event_with_track_id_updates_behavior_track(self):
        self.bc.process_event(camera_id=3, frame=None, track_id="track-abc")
        track = BehaviorTrack.objects.filter(track_id="track-abc").first()
        self.assertIsNotNone(track)
        self.assertEqual(track.camera_sequence[0]["camera_id"], 3)

    def test_process_event_with_invalid_frame_tolerates(self):
        """传入非法 frame（非文件非 bytes），应容忍并不抛异常。"""
        result = self.bc.process_event(camera_id=4, frame=123, event_type="motion")
        self.assertIn("brain_event_id", result)


class BrainCenterTrackQueryTests(TestCase):
    """测试 track_subject_across_cameras。"""

    def test_returns_none_when_not_found(self):
        bc = BrainCenter()
        self.assertIsNone(bc.track_subject_across_cameras("not-exist"))

    def test_returns_track_info(self):
        bc = BrainCenter()
        bc._upsert_behavior_track("track-xyz", 1)
        bc._upsert_behavior_track("track-xyz", 2)
        info = bc.track_subject_across_cameras("track-xyz")
        self.assertIsNotNone(info)
        self.assertEqual(info["track_id"], "track-xyz")
        self.assertEqual(len(info["camera_sequence"]), 2)


class BrainCenterWeeklyReportTests(TestCase):
    """测试 generate_weekly_report。"""

    def setUp(self):
        # 先造几条异常事件
        now = datetime.now()
        BrainEvent.objects.create(
            camera_id=1, timestamp=now, event_type="intrusion",
            subject="陌生人", action="翻墙", anomaly_score=0.95,
        )
        BrainEvent.objects.create(
            camera_id=2, timestamp=now, event_type="fall",
            subject="老人", action="摔倒", anomaly_score=0.9,
        )
        BrainEvent.objects.create(
            camera_id=1, timestamp=now, event_type="motion",
            subject="家人", action="散步", anomaly_score=0.2,  # 非异常
        )

    def test_generate_weekly_report_creates_record(self):
        bc = BrainCenter()
        result = bc.generate_weekly_report()
        self.assertIn("id", result)
        self.assertGreater(result["anomaly_count"], 0)

        wr = WeeklyReport.objects.get(id=result["id"])
        # anomaly_count 应为 2（score >= 0.7 的那两条）
        self.assertEqual(wr.anomaly_count, 2)

    def test_generate_weekly_report_overwrites_same_week(self):
        bc = BrainCenter()
        r1 = bc.generate_weekly_report()
        r2 = bc.generate_weekly_report()
        self.assertEqual(r1["week_start"], r2["week_start"])
        self.assertEqual(WeeklyReport.objects.count(), 1)


class BrainCenterNaturalLanguageSearchTests(TestCase):
    """测试 natural_language_search（无真实 LLM 时走 LIKE 兜底）。"""

    def setUp(self):
        BrainEvent.objects.create(
            camera_id=1, timestamp=datetime.now(), event_type="motion",
            subject="老人", action="摔倒", scene_description="客厅老人摔倒", anomaly_score=0.9,
        )
        BrainEvent.objects.create(
            camera_id=2, timestamp=datetime.now(), event_type="motion",
            subject="陌生人", action="翻墙", scene_description="院子陌生人翻墙", anomaly_score=0.95,
        )

    def test_search_finds_by_subject(self):
        bc = BrainCenter()
        result = bc.natural_language_search("老人")
        self.assertGreaterEqual(result["results_count"], 1)

    def test_search_finds_by_action(self):
        bc = BrainCenter()
        result = bc.natural_language_search("翻墙")
        self.assertGreaterEqual(result["results_count"], 1)

    def test_search_empty(self):
        bc = BrainCenter()
        result = bc.natural_language_search("不存在的关键词xyz")
        self.assertEqual(result["results_count"], 0)


class BrainCenterVLMParsingTests(TestCase):
    """测试 VLM JSON 解析工具。"""

    def test_parse_clean_json(self):
        self.assertEqual(
            BrainCenter._parse_vlm_json('{"subject":"猫","action":"睡觉"}'),
            {"subject": "猫", "action": "睡觉"},
        )

    def test_parse_markdown_wrapped_json(self):
        text = "```json\n{\"subject\":\"狗\",\"action\":\"叫\"}\n```"
        self.assertEqual(
            BrainCenter._parse_vlm_json(text),
            {"subject": "狗", "action": "叫"},
        )

    def test_parse_invalid_json_fallback(self):
        self.assertEqual(BrainCenter._parse_vlm_json("hello"), {})
        self.assertEqual(BrainCenter._parse_vlm_json(""), {})
        self.assertEqual(BrainCenter._parse_vlm_json(None), {})

    def test_parse_truncated_fallback(self):
        """即使 VLM 输出带其它文本，也能截取第一个 {...}。"""
        text = "好的，画面是这样的：{\"scene\":\"厨房\"} 希望对你有帮助。"
        self.assertEqual(BrainCenter._parse_vlm_json(text), {"scene": "厨房"})


class BrainAPITests(TestCase):
    """测试 brain_api 函数式 View（不依赖真实 session）。"""

    def setUp(self):
        # 先造一条脑中枢事件
        self.be = BrainEvent.objects.create(
            camera_id=1, timestamp=datetime.now(), event_type="motion",
            subject="猫", action="睡觉", anomaly_score=0.1,
        )

    def test_brain_events_view(self):
        from django.test import RequestFactory
        from app import brain_api
        rf = RequestFactory()
        req = rf.get("/api/brain/events")
        resp = brain_api.brain_events(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 1000)
        self.assertGreater(len(data["data"]), 0)

    def test_brain_search_view(self):
        from django.test import RequestFactory
        from app import brain_api
        rf = RequestFactory()
        req = rf.post("/api/brain/search",
                      data=json.dumps({"query": "猫"}),
                      content_type="application/json")
        resp = brain_api.brain_search(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(data["code"], 1000)
