# -*- coding: utf-8 -*-
"""
室内互动场景 REST API — 函数式 View（统一返回 {code,data,message}）。

路由：
  GET  /api/indoor/config?camera_id=
  PUT  /api/indoor/config
  POST /api/indoor/test-pet
  POST /api/indoor/test-elder
  GET  /api/indoor/events?camera_id=&start_time=&end_time=&event_type=&limit=
"""
import json
import logging
from datetime import datetime, timedelta

from django.views.decorators.csrf import csrf_exempt

from app.views.ViewsBase import f_parseGetParams, f_parsePostParams, f_responseJson
from app.services.indoor_scene import IndoorSceneEngine

logger = logging.getLogger("api.indoor")


def _s(v):
    """安全地把参数值转为字符串并 strip（兼容 GET str 和 POST JSON int/float/bool）。"""
    if v is None:
        return ""
    return str(v).strip()


def _ok(data=None, message="success"):
    return f_responseJson({"code": 200, "data": data, "message": message})


def _fail(message, code=400, data=None):
    return f_responseJson({"code": code, "data": data, "message": message})


def indoor_config_dispatch(request):
    """GET/PUT /api/indoor/config 方法分发。"""
    if request.method == "PUT":
        return indoor_config_update(request)
    return indoor_config(request)


def indoor_config(request):
    """GET /api/indoor/config?camera_id= — 查询生效配置 + 全部模式配置行。"""
    try:
        params = f_parseGetParams(request)
        camera_id = _s(params.get("camera_id", ""))
        if not camera_id:
            return _fail("camera_id 不能为空")

        engine = IndoorSceneEngine()
        rows = [_config_to_dict(c) for c in engine.get_configs(int(camera_id))]
        data = {
            "camera_id": int(camera_id),
            "effective": engine.get_effective_config(int(camera_id)),
            "scene_configs": rows,
        }
        return _ok(data)
    except Exception as e:
        logger.exception("indoor_config 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def indoor_config_update(request):
    """PUT /api/indoor/config — 新增/更新配置（热更新，保存即生效）。

    body（JSON 或 Form）：
      camera_id(int), scene_type(str 默认 general),
      enabled(bool), config(dict)
    """
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id"))
        if not camera_id:
            return _fail("camera_id 必填")

        scene_type = _s(params.get("scene_type")) or "general"
        enabled = bool(params.get("enabled", True))
        cfg_data = params.get("config")
        if isinstance(cfg_data, str):
            try:
                cfg_data = json.loads(cfg_data)
            except Exception:
                cfg_data = {}
        if not isinstance(cfg_data, dict):
            cfg_data = {}

        obj = IndoorSceneEngine.upsert_config(
            camera_id=int(camera_id),
            scene_type=scene_type,
            enabled=enabled,
            config=cfg_data,
        )
        return _ok(_config_to_dict(obj))
    except Exception as e:
        logger.exception("indoor_config_update 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def indoor_test_pet(request):
    """POST /api/indoor/test-pet — 手动测试宠物模式。body: camera_id。"""
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id"))
        if not camera_id:
            return _fail("camera_id 必填")

        result = IndoorSceneEngine().test_pet(int(camera_id))
        if not result.get("triggered"):
            return _fail("宠物模式未触发", code=400, data=result)
        return _ok(result)
    except Exception as e:
        logger.exception("indoor_test_pet 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def indoor_test_elder(request):
    """POST /api/indoor/test-elder — 手动测试老人模式。body: camera_id。"""
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id"))
        if not camera_id:
            return _fail("camera_id 必填")

        result = IndoorSceneEngine().test_elder(int(camera_id))
        if not result.get("triggered"):
            return _fail("老人模式未触发", code=400, data=result)
        return _ok(result)
    except Exception as e:
        logger.exception("indoor_test_elder 异常: %s", e)
        return _fail(str(e), code=500)


def indoor_events(request):
    """GET /api/indoor/events — 事件查询。

    参数: camera_id, start_time(ISO), end_time(ISO), event_type, scene_mode, limit
    """
    try:
        from app.models import IndoorEvent
        params = f_parseGetParams(request)
        camera_id = _s(params.get("camera_id", ""))
        start_time = _s(params.get("start_time", ""))
        end_time = _s(params.get("end_time", ""))
        event_type = _s(params.get("event_type", ""))
        scene_mode = _s(params.get("scene_mode", ""))
        try:
            limit = min(int(params.get("limit", 100)), 500)
        except (TypeError, ValueError):
            limit = 100

        qs = IndoorEvent.objects.all()
        if camera_id:
            qs = qs.filter(camera_id=int(camera_id))
        if start_time:
            qs = qs.filter(timestamp__gte=_parse_iso(start_time))
        if end_time:
            qs = qs.filter(timestamp__lte=_parse_iso(end_time))
        if event_type:
            qs = qs.filter(event_type=event_type)
        if scene_mode:
            qs = qs.filter(scene_mode=scene_mode)

        qs = qs.order_by("-timestamp")[:limit]
        return _ok([_event_to_dict(e) for e in qs])
    except Exception as e:
        logger.exception("indoor_events 异常: %s", e)
        return _fail(str(e), code=500, data=[])


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
        "scene_type": c.scene_type,
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
        "scene_mode": e.scene_mode,
        "timestamp": e.timestamp.isoformat(),
        "snapshot_path": e.snapshot_path,
        "actions_taken": e.actions_taken,
        "notified": bool(e.notified),
    }
