# 作者：北小菜
# 官网：https://www.yuturuishi.com
# 微信：bilibili_bxc
# 哔哩哔哩主页：https://space.bilibili.com/487906612
# gitee地址：https://gitee.com/Vanishi/rebucca
# github地址：https://github.com/beixiaocai/rebucca
"""
脑中枢服务 — 调用 VLM 大模型对摄像头画面做语义理解，
生成事件级语义描述、跨摄像头行为轨迹追踪、每周安全周报。
"""
import base64
import json
import logging
from datetime import datetime, timedelta, date

from app.models import BrainEvent, BehaviorTrack, WeeklyReport, LLMModel
from app.utils.LLMUtils import LLMUtils

logger = logging.getLogger("services.brain_center")

# VLM 固定 Prompt 模板
_VLM_PROMPT = (
    "这是家庭监控摄像头的画面，请描述画面中发生了什么，"
    "识别出人物/宠物/物品的状态和行为。"
    "请严格返回 JSON 格式，字段如下："
    '{"scene": "客厅", "subject": "老人", "action": "坐着", '
    '"duration": "2小时", "anomaly": false}'
)


class BrainCenter:
    """脑中枢：统一调度 VLM 语义理解、事件存储、跨摄像头追踪、周报生成。"""

    def __init__(self, llm_model=None):
        """
        llm_model: LLMModel 实例或 None（None 时自动取第一个启用的）
        """
        self._llm_model = llm_model
        self._llm_utils = self._build_llm_utils(llm_model)

    # ----------------------- 内部工具 -----------------------

    @staticmethod
    def _build_llm_utils(llm_model):
        """根据 LLMModel 构造 LLMUtils，未指定则取第一个启用的大模型。"""
        try:
            if llm_model is None:
                llm_model = LLMModel.objects.filter(state=1).first()
            if llm_model is None:
                logger.warning("未找到启用的 LLMModel，BrainCenter 将无法调用 VLM")
                return None
            return LLMUtils(
                api_url=llm_model.api_url,
                api_key=llm_model.api_key,
                timeout=getattr(llm_model, 'timeout', 15) or 15,
                inference_tool=llm_model.inference_tool,
                model=llm_model.model_name,
            )
        except Exception as e:
            logger.warning("构建 LLMUtils 失败: %s", str(e))
            return None

    @staticmethod
    def _parse_vlm_json(text):
        """从 VLM 返回文本中解析 JSON（容忍 markdown 代码块包裹等）。"""
        if not text:
            return {}
        # 去掉可能的 markdown 代码块包裹
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else lines[0]
        try:
            return json.loads(cleaned)
        except Exception:
            # 兜底：尝试直接截取第一个 {...} 块
            try:
                start = cleaned.index("{")
                end = cleaned.rindex("}") + 1
                return json.loads(cleaned[start:end])
            except Exception:
                logger.warning("VLM 返回无法解析为 JSON: %s", text[:200])
                return {}

    # ----------------------- 1. 处理单帧事件 -----------------------

    def process_event(self, camera_id, frame, event_type="motion",
                      track_id=None, snapshot_path="", video_clip_path=""):
        """接收摄像头运动事件，调用 VLM 理解画面，写入 BrainEvent。

        Args:
            camera_id: 摄像头ID（int）
            frame: 图像数据 — 可以是 bytes，或文件路径(str)，或 base64(str)
            event_type: 事件类型（motion/intrusion/fall 等）
            track_id: 可选，跨摄像头轨迹ID
            snapshot_path: 可选，快照文件路径
            video_clip_path: 可选，视频片段路径

        Returns:
            dict: {"brain_event_id": int, "vlm_result": dict, "anomaly_score": float}
        """
        vlm_result = {}
        anomaly_score = 0.0

        # 读取 frame 为 bytes（兼容 bytes / 文件路径 / base64 字符串三种输入）
        image_bytes = self._normalize_frame(frame)

        # 调用 VLM
        if image_bytes is not None and self._llm_utils is not None:
            try:
                raw = self._llm_utils.infer(_VLM_PROMPT, image_bytes)
                vlm_result = self._parse_vlm_json(raw)
            except Exception as e:
                logger.warning("VLM 推理失败 cam=%s: %s", camera_id, str(e))

        # 计算异常评分：VLM 返回 anomaly=true 记 0.8，结合 event_type 加分
        anomaly_flag = vlm_result.get("anomaly", False)
        if anomaly_flag:
            anomaly_score = 0.8
        if event_type in ("intrusion", "fall", "scream"):
            anomaly_score = max(anomaly_score, 0.95)

        # 写入 BrainEvent
        try:
            be = BrainEvent.objects.create(
                camera_id=int(camera_id),
                timestamp=datetime.now(),
                event_type=event_type or "motion",
                scene_description=json.dumps(vlm_result, ensure_ascii=False),
                subject=vlm_result.get("subject", ""),
                action=vlm_result.get("action", ""),
                anomaly_score=anomaly_score,
                snapshot_path=snapshot_path or "",
                video_clip_path=video_clip_path or "",
            )
            logger.info("BrainEvent 入库 id=%s cam=%s subject=%s action=%s anomaly=%.2f",
                        be.id, camera_id, be.subject, be.action, anomaly_score)

            # 如提供了 track_id，则更新/创建 BehaviorTrack
            if track_id:
                self._upsert_behavior_track(track_id, camera_id)

            return {
                "brain_event_id": be.id,
                "vlm_result": vlm_result,
                "anomaly_score": anomaly_score,
            }
        except Exception as e:
            logger.exception("BrainEvent 入库失败: %s", str(e))
            raise

    @staticmethod
    def _normalize_frame(frame):
        """将 frame 归一化为 bytes（失败返回 None）。"""
        if frame is None:
            return None
        if isinstance(frame, (bytes, bytearray)):
            return bytes(frame)
        if isinstance(frame, str):
            # 文件路径
            try:
                with open(frame, "rb") as f:
                    return f.read()
            except (OSError, IOError):
                pass
            # base64 字符串
            try:
                return base64.b64decode(frame)
            except Exception:
                return None
        return None

    # ----------------------- 2. 跨摄像头轨迹追踪 -----------------------

    @staticmethod
    def _upsert_behavior_track(track_id, camera_id):
        """内部工具：追加一个新摄像头到 BehaviorTrack，不存在则创建。"""
        now = datetime.now()
        track = BehaviorTrack.objects.filter(track_id=track_id).first()
        if track is None:
            BehaviorTrack.objects.create(
                track_id=track_id,
                camera_sequence=[{"camera_id": int(camera_id), "timestamp": now.isoformat()}],
                start_time=now,
                end_time=now,
                total_duration=0.0,
            )
            return
        seq = track.camera_sequence or []
        seq.append({"camera_id": int(camera_id), "timestamp": now.isoformat()})
        track.camera_sequence = seq
        track.end_time = now
        # 根据时间差估算总时长
        dur = (now - track.start_time).total_seconds()
        track.total_duration = dur
        track.save()

    def track_subject_across_cameras(self, track_id):
        """查询 BehaviorTrack 返回轨迹详情。"""
        try:
            track = BehaviorTrack.objects.filter(track_id=track_id).first()
            if track is None:
                return None
            return {
                "track_id": track.track_id,
                "camera_sequence": track.camera_sequence,
                "start_time": track.start_time.isoformat(),
                "end_time": track.end_time.isoformat(),
                "total_duration": track.total_duration,
            }
        except Exception as e:
            logger.warning("查询 BehaviorTrack 失败 track_id=%s: %s", track_id, str(e))
            return None

    # ----------------------- 3. 生成每周安全周报 -----------------------

    def generate_weekly_report(self, week_start=None):
        """汇总本周异常事件，生成 WeeklyReport。

        week_start: date，周起始日（周一），None 则取本周一。
        """
        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        start_dt = datetime.combine(week_start, datetime.min.time())
        end_dt = datetime.combine(week_end, datetime.max.time())

        # 异常事件筛选：anomaly_score >= 0.7 视为异常
        anomaly_events = BrainEvent.objects.filter(
            timestamp__gte=start_dt, timestamp__lte=end_dt, anomaly_score__gte=0.7
        ).order_by("-timestamp")

        anomaly_count = anomaly_events.count()

        # 构造报告摘要（TOP 异常摄像头 / 高频主体 / 高频行为）
        from django.db.models import Count
        top_cameras = list(anomaly_events.values("camera_id").annotate(
            c=Count("id")).order_by("-c")[:5])
        top_subjects = list(anomaly_events.values("subject").annotate(
            c=Count("id")).order_by("-c")[:5])
        top_actions = list(anomaly_events.values("action").annotate(
            c=Count("id")).order_by("-c")[:5])

        # 尝试让 LLM 生成自然语言摘要（可用时）
        llm_summary = ""
        if self._llm_utils is not None:
            try:
                top_examples = list(anomaly_events[:5].values(
                    "camera_id", "subject", "action", "anomaly_score"
                ))
                prompt = (
                    f"请根据以下监控异常事件，生成一段 100 字以内的中文安全周报摘要："
                    f"总异常数={anomaly_count}, 本周范围={week_start}~{week_end}。"
                    f"TOP 摄像头={top_cameras}, TOP 主体={top_subjects}, TOP 行为={top_actions}。"
                    f"异常样例={top_examples}。"
                )
                raw = self._llm_utils.infer(prompt, b"")
                llm_summary = (raw or "").strip().strip("```").strip()
            except Exception as e:
                logger.warning("LLM 生成周报摘要失败: %s", str(e))

        summary = llm_summary or (
            f"本周 {week_start}~{week_end} 共检测到 {anomaly_count} 条异常事件，"
            f"高风险时段已标记，请关注。"
        )

        report_content = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "anomaly_count": anomaly_count,
            "total_events": BrainEvent.objects.filter(
                timestamp__gte=start_dt, timestamp__lte=end_dt
            ).count(),
            "top_cameras": top_cameras,
            "top_subjects": top_subjects,
            "top_actions": top_actions,
            "llm_summary": llm_summary,
            "generated_at": datetime.now().isoformat(),
        }

        # 覆盖生成同一周的旧报告
        WeeklyReport.objects.filter(week_start=week_start).delete()
        wr = WeeklyReport.objects.create(
            week_start=week_start,
            week_end=week_end,
            summary=summary[:500],
            anomaly_count=anomaly_count,
            report_content=report_content,
        )
        logger.info("WeeklyReport 生成 id=%s week=%s~%s anomaly=%d",
                    wr.id, week_start, week_end, anomaly_count)
        return {
            "id": wr.id,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "summary": summary,
            "anomaly_count": anomaly_count,
        }

    # ----------------------- 4. 自然语言搜索 -----------------------

    def natural_language_search(self, query):
        """用 LLM 解析自然语言，再对 BrainEvent 做模糊匹配。

        策略：
        1) LLM 将自然语言解析为结构化 JSON：{subject, action, scene, keyword}
        2) 根据解析结果对 BrainEvent 做多条件 OR 模糊匹配
        3) 未启用 LLM 时，直接用 query 全文在 scene_description/subject/action 中模糊匹配
        """
        parsed = {}
        if self._llm_utils is not None:
            try:
                parse_prompt = (
                    f"请把下面的自然语言查询解析为 JSON 搜索条件，"
                    f"字段允许缺失。返回严格 JSON："
                    f'{{"subject": "", "action": "", "scene": "", "keyword": ""}}\n'
                    f"查询：{query}"
                )
                raw = self._llm_utils.infer(parse_prompt, b"")
                parsed = self._parse_vlm_json(raw)
            except Exception as e:
                logger.warning("LLM 解析搜索查询失败: %s", str(e))
                parsed = {}

        # 构造 Q 过滤条件
        from django.db.models import Q
        qs = BrainEvent.objects.all()
        q = Q()
        hit = False

        # 原始 query 做全字段 LIKE
        original_q = (query or "").strip()
        if original_q:
            q |= Q(scene_description__icontains=original_q)
            q |= Q(subject__icontains=original_q)
            q |= Q(action__icontains=original_q)
            hit = True

        # LLM 解析出的结构化条件（精确字段）
        subject = (parsed.get("subject") or "").strip()
        action = (parsed.get("action") or "").strip()
        scene = (parsed.get("scene") or "").strip()
        keyword = (parsed.get("keyword") or "").strip()
        if subject:
            q |= Q(subject__icontains=subject); hit = True
        if action:
            q |= Q(action__icontains=action); hit = True
        if scene:
            q |= Q(scene_description__icontains=scene); hit = True
        if keyword:
            q |= Q(scene_description__icontains=keyword); hit = True

        if hit:
            qs = qs.filter(q).order_by("-timestamp")[:100]
        else:
            qs = qs.none()

        results = []
        for be in qs:
            results.append({
                "id": be.id,
                "camera_id": be.camera_id,
                "timestamp": be.timestamp.isoformat(),
                "event_type": be.event_type,
                "subject": be.subject,
                "action": be.action,
                "anomaly_score": be.anomaly_score,
                "snapshot_path": be.snapshot_path,
            })
        return {
            "parsed_query": parsed,
            "results_count": len(results),
            "results": results,
        }
