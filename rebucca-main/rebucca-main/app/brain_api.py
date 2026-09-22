# 作者：北小菜
# 官网：https://www.yuturuishi.com
# 微信：bilibili_bxc
# 哔哩哔哩主页：https://space.bilibili.com/487906612
# gitee地址：https://gitee.com/Vanishi/rebucca
# github地址：https://github.com/beixiaocai/rebucca
"""
脑中枢 REST API — 函数式 View。

路由（需在 urls.py 中引入此模块的函数）：
  GET  /api/brain/events?camera_id=&start_time=&end_time=
  GET  /api/brain/tracks?track_id=
  POST /api/brain/search
  GET  /api/brain/weekly-report
  POST /api/brain/generate-report
"""
import logging

from app.views.ViewsBase import f_parseGetParams, f_parsePostParams, f_responseJson
from app.services.brain_center import BrainCenter

logger = logging.getLogger("api.brain")


def brain_events(request):
    """GET /api/brain/events — 按条件查询脑中枢事件列表。"""
    try:
        params = f_parseGetParams(request)
        camera_id = params.get("camera_id", "").strip()
        start_time = params.get("start_time", "").strip()
        end_time = params.get("end_time", "").strip()
        limit = int(params.get("limit", 100))
        limit = min(limit, 500)

        from app.models import BrainEvent
        qs = BrainEvent.objects.all()

        if camera_id:
            qs = qs.filter(camera_id=int(camera_id))
        if start_time:
            qs = qs.filter(timestamp__gte=_parse_iso(start_time))
        if end_time:
            qs = qs.filter(timestamp__lte=_parse_iso(end_time))

        qs = qs.order_by("-timestamp")[:limit]
        data = [_brain_event_to_dict(be) for be in qs]
        return f_responseJson({"code": 1000, "msg": "success", "data": data})
    except Exception as e:
        logger.exception("brain_events 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": []})


def brain_tracks(request):
    """GET /api/brain/tracks?track_id= — 查询跨摄像头行为轨迹。"""
    try:
        params = f_parseGetParams(request)
        track_id = params.get("track_id", "").strip()
        if not track_id:
            return f_responseJson({"code": 0, "msg": "track_id 不能为空", "data": None})
        bc = BrainCenter()
        result = bc.track_subject_across_cameras(track_id)
        return f_responseJson({"code": 1000, "msg": "success", "data": result})
    except Exception as e:
        logger.exception("brain_tracks 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": None})


def brain_search(request):
    """POST /api/brain/search — 自然语言搜索脑中枢事件。"""
    try:
        params = f_parsePostParams(request)
        query = (params.get("query") or "").strip()
        if not query:
            return f_responseJson({"code": 0, "msg": "query 不能为空", "data": None})
        bc = BrainCenter()
        result = bc.natural_language_search(query)
        return f_responseJson({"code": 1000, "msg": "success", "data": result})
    except Exception as e:
        logger.exception("brain_search 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": None})


def brain_weekly_report(request):
    """GET /api/brain/weekly-report — 读取最新的安全周报。"""
    try:
        from app.models import WeeklyReport
        wr = WeeklyReport.objects.order_by("-week_start").first()
        if wr is None:
            return f_responseJson({"code": 1000, "msg": "暂无周报", "data": None})
        data = {
            "id": wr.id,
            "week_start": wr.week_start.isoformat(),
            "week_end": wr.week_end.isoformat(),
            "summary": wr.summary,
            "anomaly_count": wr.anomaly_count,
            "report_content": wr.report_content,
            "create_time": wr.create_time.isoformat(),
        }
        return f_responseJson({"code": 1000, "msg": "success", "data": data})
    except Exception as e:
        logger.exception("brain_weekly_report 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": None})


def brain_generate_report(request):
    """POST /api/brain/generate-report — 手动触发生成周报。"""
    try:
        params = f_parsePostParams(request)
        week_start_str = (params.get("week_start") or "").strip() or None
        week_start = None
        if week_start_str:
            from datetime import date
            week_start = date.fromisoformat(week_start_str)
        bc = BrainCenter()
        result = bc.generate_weekly_report(week_start=week_start)
        return f_responseJson({"code": 1000, "msg": "success", "data": result})
    except Exception as e:
        logger.exception("brain_generate_report 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": None})


# ===================== 内部辅助 =====================

def _parse_iso(s):
    """解析 ISO 格式时间字符串，解析失败返回当前时间前 30 天。"""
    try:
        return datetime.fromisoformat(s)
    except Exception:
        from datetime import timedelta
        return datetime.now() - timedelta(days=30)


def _brain_event_to_dict(be):
    return {
        "id": be.id,
        "camera_id": be.camera_id,
        "timestamp": be.timestamp.isoformat(),
        "event_type": be.event_type,
        "scene_description": be.scene_description,
        "subject": be.subject,
        "action": be.action,
        "anomaly_score": be.anomaly_score,
        "snapshot_path": be.snapshot_path,
        "video_clip_path": be.video_clip_path,
    }


def brain_page(request):
    """脑中枢前端页面渲染。
    路由: /brain/page
    使用 Vue 3 + Element Plus CDN 构建。
    """
    from django.shortcuts import render
    return render(request, "app/brain/index.html")


def ai_upgrade_page(request):
    """AI 智能升级介绍页渲染。
    路由: /ai-upgrade
    使用 Vue 3 + Element Plus CDN 构建。
    """
    from django.shortcuts import render
    return render(request, "app/ai_upgrade/index.html")
