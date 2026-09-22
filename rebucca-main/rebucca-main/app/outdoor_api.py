# 作者：北小菜
# 官网：https://www.yuturuishi.com
# 微信：bilibili_bxc
# 哔哩哔哩主页：https://space.bilibili.com/487906612
# gitee地址：https://gitee.com/Vanishi/rebucca
# github地址：https://github.com/beixiaocai/rebucca
"""
户外场景 REST API — 函数式 View。

路由（需在 urls.py 中引入此模块的函数）：
  GET  /api/outdoor/config?camera_id=
  PUT  /api/outdoor/config
  POST /api/outdoor/trigger-welcome
  POST /api/outdoor/trigger-intrusion
  GET  /api/outdoor/events?start_time=&end_time=
"""
import json
import logging
from datetime import datetime

from app.views.ViewsBase import f_parseGetParams, f_parsePostParams, f_responseJson
from app.services.outdoor_scene import OutdoorSceneEngine

logger = logging.getLogger("api.outdoor")


def _s(v):
    """安全地把参数值转为字符串并 strip（兼容 GET str 和 POST JSON int/float/bool）。"""
    if v is None:
        return ""
    return str(v).strip()


def outdoor_config(request):
    """GET /api/outdoor/config?camera_id= — 查询某摄像头的全部场景配置。"""
    try:
        params = f_parseGetParams(request)
        camera_id = _s(params.get("camera_id", ""))
        if not camera_id:
            return f_responseJson({"code": 0, "msg": "camera_id 不能为空", "data": []})

        configs = OutdoorSceneEngine.get_scene_configs(int(camera_id))
        data = [_scene_config_to_dict(c) for c in configs]
        return f_responseJson({"code": 1000, "msg": "success", "data": data})
    except Exception as e:
        logger.exception("outdoor_config 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": []})


def outdoor_config_update(request):
    """PUT /api/outdoor/config — 新增或更新场景配置。

    支持 body（JSON 或 Form）：
      camera_id(int), scene_type(str), enabled(bool), config(dict)
    """
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id"))
        scene_type = _s(params.get("scene_type"))
        if not camera_id or not scene_type:
            return f_responseJson({"code": 0, "msg": "camera_id / scene_type 必填", "data": None})

        enabled = bool(params.get("enabled", True))
        cfg_data = params.get("config")
        if isinstance(cfg_data, str):
            try:
                cfg_data = json.loads(cfg_data)
            except Exception:
                cfg_data = {}
        if not isinstance(cfg_data, dict):
            cfg_data = {}

        obj = OutdoorSceneEngine.upsert_scene_config(
            camera_id=int(camera_id),
            scene_type=scene_type,
            enabled=enabled,
            config=cfg_data,
        )
        return f_responseJson({
            "code": 1000, "msg": "success",
            "data": _scene_config_to_dict(obj),
        })
    except Exception as e:
        logger.exception("outdoor_config_update 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": None})


def outdoor_trigger_welcome(request):
    """POST /api/outdoor/trigger-welcome — 手动触发迎宾场景。"""
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id"))
        if not camera_id:
            return f_responseJson({"code": 0, "msg": "camera_id 必填", "data": None})

        engine = OutdoorSceneEngine()
        # 手动触发时，直接构造一个 person_info（默认家人），不依赖 VLM 识别
        person_info = params.get("person_info") or {"person_type": "family", "confidence": 1.0}
        actions = engine.trigger_welcome_scene(int(camera_id), person_info)

        # 同时落库
        from app.models import OutdoorEvent
        oe = OutdoorEvent.objects.create(
            camera_id=int(camera_id),
            event_type="welcome",
            person_type=person_info.get("person_type", "family"),
            person_confidence=float(person_info.get("confidence", 1.0)),
            timestamp=datetime.now(),
            snapshot_path="",
            actions_taken=actions,
            notified=0,
        )
        return f_responseJson({
            "code": 1000, "msg": "success",
            "data": {"event_id": oe.id, "actions": actions},
        })
    except Exception as e:
        logger.exception("outdoor_trigger_welcome 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": None})


def outdoor_trigger_intrusion(request):
    """POST /api/outdoor/trigger-intrusion — 手动触发入侵防御场景。"""
    try:
        params = f_parsePostParams(request)
        camera_id = _s(params.get("camera_id"))
        if not camera_id:
            return f_responseJson({"code": 0, "msg": "camera_id 必填", "data": None})

        engine = OutdoorSceneEngine()
        person_info = params.get("person_info") or {"person_type": "stranger", "confidence": 1.0}
        actions = engine.trigger_intrusion_scene(int(camera_id), person_info)

        from app.models import OutdoorEvent
        oe = OutdoorEvent.objects.create(
            camera_id=int(camera_id),
            event_type="intrusion",
            person_type=person_info.get("person_type", "stranger"),
            person_confidence=float(person_info.get("confidence", 1.0)),
            timestamp=datetime.now(),
            snapshot_path="",
            actions_taken=actions,
            notified=1,
        )
        return f_responseJson({
            "code": 1000, "msg": "success",
            "data": {"event_id": oe.id, "actions": actions},
        })
    except Exception as e:
        logger.exception("outdoor_trigger_intrusion 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": None})


def outdoor_events(request):
    """GET /api/outdoor/events?camera_id=&start_time=&end_time=&event_type=&limit="""
    try:
        from app.models import OutdoorEvent
        params = f_parseGetParams(request)
        camera_id = _s(params.get("camera_id", ""))
        start_time = _s(params.get("start_time", ""))
        end_time = _s(params.get("end_time", ""))
        event_type = _s(params.get("event_type", ""))
        limit = int(params.get("limit", 100))
        limit = min(limit, 500)

        qs = OutdoorEvent.objects.all()
        if camera_id:
            qs = qs.filter(camera_id=int(camera_id))
        if start_time:
            qs = qs.filter(timestamp__gte=_parse_iso(start_time))
        if end_time:
            qs = qs.filter(timestamp__lte=_parse_iso(end_time))
        if event_type:
            qs = qs.filter(event_type=event_type)

        qs = qs.order_by("-timestamp")[:limit]
        data = [_outdoor_event_to_dict(oe) for oe in qs]
        return f_responseJson({"code": 1000, "msg": "success", "data": data})
    except Exception as e:
        logger.exception("outdoor_events 异常: %s", str(e))
        return f_responseJson({"code": 0, "msg": str(e), "data": []})


# ===================== 内部辅助 =====================

def _parse_iso(s):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        from datetime import timedelta
        return datetime.now() - timedelta(days=30)


def _scene_config_to_dict(c):
    return {
        "id": c.id,
        "camera_id": c.camera_id,
        "scene_type": c.scene_type,
        "enabled": bool(c.enabled),
        "config": c.config or {},
        "create_time": c.create_time.isoformat(),
        "last_update_time": c.last_update_time.isoformat(),
    }


def _outdoor_event_to_dict(oe):
    return {
        "id": oe.id,
        "camera_id": oe.camera_id,
        "event_type": oe.event_type,
        "person_type": oe.person_type,
        "person_confidence": oe.person_confidence,
        "timestamp": oe.timestamp.isoformat(),
        "snapshot_path": oe.snapshot_path,
        "actions_taken": oe.actions_taken,
        "notified": bool(oe.notified),
    }


def outdoor_page(request):
    """户外场景前端页面渲染。
    路由: /outdoor/page
    使用 Vue 3 + Element Plus CDN 构建。
    """
    from django.shortcuts import render
    return render(request, "app/outdoor/index.html")
