# -*- coding: utf-8 -*-
"""
本地摄像头 / 迎宾场景 REST API — 函数式 View（统一 {code,data,message}）。

路由：
  GET  /api/video/stream          MJPEG 实时画面（<img> 直接显示）
  GET  /api/camera/status         摄像头状态
  POST /api/camera/start           启动摄像头 + 迎宾引擎
  POST /api/camera/stop            停止
  POST /api/camera/ptz             模拟 PTZ（body: direction）
  GET  /api/alerts                 告警列表（可按 scene_type 筛选）
  GET  /api/scene/config           四个场景的开关/灵敏度
  PUT  /api/scene/config           保存场景配置
  GET  /api/events/stream          SSE 实时事件推送
"""
import json
import logging

from django.http import StreamingHttpResponse

from app.views.ViewsBase import f_parseGetParams, f_parsePostParams, f_responseJson
from app.services.camera_manager import CameraManager
from app.services.event_bus import EventBus
from app.services.device_control import MockDeviceControl

logger = logging.getLogger("api.camera")


def _s(v):
    if v is None:
        return ""
    return str(v).strip()


def _ok(data=None, message="success"):
    return f_responseJson({"code": 200, "data": data, "message": message})


def _fail(message, code=400, data=None):
    return f_responseJson({"code": code, "data": data, "message": message})


# ===================== 视频流 / 摄像头 =====================

def video_stream(request):
    """GET /api/video/stream — MJPEG 流，前端 <img> 直接显示。"""
    manager = CameraManager()
    response = StreamingHttpResponse(
        manager.mjpeg_stream(),
        content_type="multipart/x-mixed-replace; boundary=frame")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # 防止反向代理缓冲
    return response


def camera_status(request):
    """GET /api/camera/status — 摄像头状态（开关、分辨率等）。"""
    return _ok(CameraManager().status())


def camera_start(request):
    """POST /api/camera/start — 启动摄像头 + 迎宾场景引擎。"""
    try:
        params = f_parsePostParams(request)
        index = _s(params.get("camera_index"))
        result = CameraManager().start(
            camera_index=int(index) if index else None)
        if result["ok"]:
            return _ok(result.get("data"), message=result["message"])
        return _fail(result["message"])
    except Exception as e:
        logger.exception("camera_start 异常: %s", e)
        return _fail(f"启动失败：{e}", code=500)


def camera_stop(request):
    """POST /api/camera/stop。"""
    result = CameraManager().stop()
    return _ok(message=result["message"])


def camera_ptz(request):
    """POST /api/camera/ptz — 模拟 PTZ。body: {"direction":"up/down/left/right"}"""
    try:
        params = f_parsePostParams(request)
        direction = _s(params.get("direction")) or "center"
        action = MockDeviceControl().ptz_goto("local-cam", direction)
        return _ok(action)
    except Exception as e:
        logger.exception("camera_ptz 异常: %s", e)
        return _fail(str(e), code=500)


# ===================== 告警列表 =====================

def alerts_list(request):
    """GET /api/alerts?scene_type=&limit= — 告警记录（时间倒序）。"""
    try:
        from app.models import AlarmModel
        params = f_parseGetParams(request)
        scene_type = _s(params.get("scene_type", ""))
        try:
            limit = min(int(params.get("limit", 20)), 200)
        except (TypeError, ValueError):
            limit = 20

        qs = AlarmModel.objects.all()
        if scene_type:
            qs = qs.filter(scene_type=scene_type)
        qs = qs.order_by("-timestamp")[:limit]
        return _ok([_alert_to_dict(a) for a in qs])
    except Exception as e:
        logger.exception("alerts_list 异常: %s", e)
        return _fail(str(e), code=500)


# ===================== 场景配置 =====================

# 四个可配置场景（复用 indoor_scene_config 表 camera_id=0 存储）
SCENE_DEFINITIONS = [
    ("welcome", "回家迎宾"),
    ("elder", "老人看护"),
    ("pet", "宠物陪伴"),
    ("night", "夜间入侵"),
]


def scene_config_dispatch(request):
    """GET/PUT /api/scene/config 方法分发。"""
    if request.method == "PUT":
        return scene_config_update(request)
    return scene_config_get(request)


def scene_config_get(request):
    """GET /api/scene/config — 返回四个场景的开关与灵敏度。"""
    return _ok(_read_scene_configs())


def scene_config_update(request):
    """PUT /api/scene/config — 保存场景配置。

    支持单个场景：
      {"scene_type":"welcome","enabled":true,"sensitivity":7}
    或批量保存：
      {"scenes":[{...}, {...}]}
    """
    try:
        from app.models import IndoorSceneConfig
        params = f_parsePostParams(request)

        items = params.get("scenes")
        if not isinstance(items, list):
            items = [params]

        for item in items:
            scene_type = _s(item.get("scene_type"))
            if scene_type not in {s[0] for s in SCENE_DEFINITIONS}:
                continue
            enabled = bool(item.get("enabled", True))
            try:
                sensitivity = int(item.get("sensitivity", 5))
            except (TypeError, ValueError):
                sensitivity = 5
            sensitivity = max(1, min(sensitivity, 10))

            row = IndoorSceneConfig.objects.filter(
                camera_id=0, scene_type=scene_type).first()
            if row is None:
                IndoorSceneConfig.objects.create(
                    camera_id=0, scene_type=scene_type,
                    enabled=1 if enabled else 0,
                    config={"sensitivity": sensitivity})
            else:
                row.enabled = 1 if enabled else 0
                row.config = {"sensitivity": sensitivity}
                row.save()

        return _ok(_read_scene_configs(), message="场景配置已保存")
    except Exception as e:
        logger.exception("scene_config_update 异常: %s", e)
        return _fail(str(e), code=500)


def _read_scene_configs():
    """读取四个场景配置（无配置行使用默认值：启用、灵敏度 5）。"""
    from app.models import IndoorSceneConfig
    result = []
    for scene_type, label in SCENE_DEFINITIONS:
        row = IndoorSceneConfig.objects.filter(
            camera_id=0, scene_type=scene_type).first()
        sensitivity = 5
        enabled = True
        if row is not None:
            enabled = bool(row.enabled)
            try:
                sensitivity = int((row.config or {}).get("sensitivity", 5))
            except (TypeError, ValueError):
                sensitivity = 5
        result.append({
            "scene_type": scene_type,
            "label": label,
            "enabled": enabled,
            "sensitivity": sensitivity,
        })
    return result


# ===================== SSE 事件推送 =====================

def events_stream(request):
    """GET /api/events/stream — SSE 实时事件（前端 EventSource）。"""
    response = StreamingHttpResponse(
        EventBus().stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ===================== 辅助 =====================

def _alert_to_dict(a):
    return {
        "id": a.id,
        "event_type": a.event_type,
        "scene_type": a.scene_type,
        "description": a.description,
        "ai_description": a.ai_description,
        "triggered_actions": a.triggered_actions or [],
        "snapshot_path": a.snapshot_path,
        "snapshot_url": f"/upload/{a.snapshot_path}" if a.snapshot_path else "",
        "timestamp": a.timestamp.isoformat(),
    }
