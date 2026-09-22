# -*- coding: utf-8 -*-
"""
无网场景 REST API — 函数式 View（统一返回 {code,data,message}）。

路由：
  GET  /api/offline/config?camera_id=
  PUT  /api/offline/config
  POST /api/offline/test-intrusion
  GET  /api/offline/events?camera_id=&start_time=&end_time=&event_type=&limit=
  GET  /api/offline/stats?camera_id=
  POST /api/offline/replay（手动触发离线补传，可选 camera_id）
"""
import json
import logging
from datetime import datetime, timedelta

from django.views.decorators.csrf import csrf_exempt

from app.views.ViewsBase import f_parseGetParams, f_parsePostParams, f_responseJson
from app.services.offline_scene import OfflineSceneEngine

logger = logging.getLogger("api.offline")


def _s(v):
    if v is None:
        return ""
    return str(v).strip()


def _ok(data=None, message="success"):
    return f_responseJson({"code": 200, "data": data, "message": message})


def _fail(message, code=400, data=None):
    return f_responseJson({"code": code, "data": data, "message": message})


def offline_config_dispatch(request):
    """GET/PUT /api/offline/config 方法分发。"""
    if request.method == "PUT":
        return offline_config_update(request)
    return offline_config(request)


def offline_config(request):
    """GET /api/offline/config?camera_id= — 查询生效配置 + 配置行。"""
    try:
        params = f_parseGetParams(request)
        camera_id = _s(params.get("camera_id", ""))
        if not camera_id:
            return _fail("camera_id 不能为空")

        engine = OfflineSceneEngine()
        rows = [_config_to_dict(c) for c in engine.get_configs(int(camera_id))]
        data = {
            "camera_id": int(camera_id),
            "effective": engine.get_effective_config(int(camera_id)),
            "scene_configs": rows,
        }
        return _ok(data)
    except Exception as e:
        logger.exception("offline_config 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def offline_config_update(request):
    """PUT /api/offline/config — 新增/更新配置（热更新，保存即生效）。

    body（JSON 或 Form）：
      camera_id(int), enabled(bool), config(dict)
    """
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id"))
        if not camera_id:
            return _fail("camera_id 必填")

        enabled = bool(params.get("enabled", True))
        cfg_data = params.get("config")
        if isinstance(cfg_data, str):
            try:
                cfg_data = json.loads(cfg_data)
            except Exception:
                cfg_data = {}
        if not isinstance(cfg_data, dict):
            cfg_data = {}

        obj = OfflineSceneEngine.upsert_config(
            camera_id=int(camera_id),
            enabled=enabled,
            config=cfg_data,
        )
        return _ok(_config_to_dict(obj))
    except Exception as e:
        logger.exception("offline_config_update 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def offline_test_intrusion(request):
    """POST /api/offline/test-intrusion — 手动测试入侵防御。body: camera_id。"""
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id"))
        if not camera_id:
            return _fail("camera_id 必填")

        result = OfflineSceneEngine().test_intrusion(int(camera_id))
        if not result.get("triggered"):
            return _fail("入侵防御未触发", code=400, data=result)
        return _ok(result)
    except Exception as e:
        logger.exception("offline_test_intrusion 异常: %s", e)
        return _fail(str(e), code=500)


def offline_events(request):
    """GET /api/offline/events — 事件查询。

    参数: camera_id, start_time(ISO), end_time(ISO), event_type,
          is_replayed, limit
    """
    try:
        from app.models import OfflineEvent
        params = f_parseGetParams(request)
        camera_id = _s(params.get("camera_id", ""))
        start_time = _s(params.get("start_time", ""))
        end_time = _s(params.get("end_time", ""))
        event_type = _s(params.get("event_type", ""))
        is_replayed = _s(params.get("is_replayed", ""))
        try:
            limit = min(int(params.get("limit", 100)), 500)
        except (TypeError, ValueError):
            limit = 100

        qs = OfflineEvent.objects.all()
        if camera_id:
            qs = qs.filter(camera_id=int(camera_id))
        if start_time:
            qs = qs.filter(timestamp__gte=_parse_iso(start_time))
        if end_time:
            qs = qs.filter(timestamp__lte=_parse_iso(end_time))
        if event_type:
            qs = qs.filter(event_type=event_type)
        if is_replayed in ("0", "1"):
            qs = qs.filter(is_replayed=int(is_replayed))

        qs = qs.order_by("-timestamp")[:limit]
        return _ok([_event_to_dict(e) for e in qs])
    except Exception as e:
        logger.exception("offline_events 异常: %s", e)
        return _fail(str(e), code=500, data=[])


def offline_stats(request):
    """GET /api/offline/stats?camera_id= — 流量与补传统计。"""
    try:
        params = f_parseGetParams(request)
        camera_id = _s(params.get("camera_id", ""))
        data = OfflineSceneEngine.get_stats(
            int(camera_id) if camera_id else None)
        return _ok(data)
    except Exception as e:
        logger.exception("offline_stats 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def offline_replay(request):
    """POST /api/offline/replay — 手动触发离线补传（网络恢复时也会自动调用）。"""
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id", ""))
        result = OfflineSceneEngine().offline_buffer_replay(
            int(camera_id) if camera_id else None)
        return _ok(result)
    except Exception as e:
        logger.exception("offline_replay 异常: %s", e)
        return _fail(str(e), code=500)


# ===================== 内部辅助 =====================

def _parse_iso(s):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.now() - timedelta(days=30)


def _config_to_dict(c):
    return {
        "id": c.id,
        "camera_id": c.camera_id,
        "enabled": bool(c.enabled),
        "config": c.config or {},
        "create_time": c.create_time.isoformat(),
        "last_update_time": c.last_update_time.isoformat(),
    }


def _event_to_dict(e):
    return {
        "id": e.id,
        "camera_id": e.camera_id,
        "event_type": e.event_type,
        "timestamp": e.timestamp.isoformat(),
        "snapshot_path": e.snapshot_path,
        "video_path": e.video_path,
        "is_replayed": e.is_replayed,
        "replayed_at": e.replayed_at.isoformat() if e.replayed_at else None,
    }
