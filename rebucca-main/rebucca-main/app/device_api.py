# -*- coding: utf-8 -*-
"""
设备联动中枢 REST API — 函数式 View（统一返回 {code,data,message}）。

路由：
  GET  /api/devices                         设备列表
  POST /api/devices/register                注册设备
  GET  /api/devices/commands                命令历史
  GET  /api/devices/<device_id>/status      设备状态
  POST /api/devices/<device_id>/ptz         PTZ 控制
  POST /api/devices/<device_id>/light       灯光控制
  POST /api/devices/<device_id>/audio       播放音频
  POST /api/devices/<device_id>/cross-track 跨摄像头联动
"""
import logging

from django.views.decorators.csrf import csrf_exempt

from app.views.ViewsBase import f_parseGetParams, f_parsePostParams, f_responseJson
from app.services.device_hub import DeviceHub

logger = logging.getLogger("api.devices")


def _s(v):
    if v is None:
        return ""
    return str(v).strip()


def _ok(data=None, message="success"):
    return f_responseJson({"code": 200, "data": data, "message": message})


def _fail(message, code=400, data=None):
    return f_responseJson({"code": code, "data": data, "message": message})


def devices_list(request):
    """GET /api/devices?type=&status= — 设备列表。"""
    try:
        from app.models import Device
        params = f_parseGetParams(request)
        dtype = _s(params.get("type", ""))
        status = _s(params.get("status", ""))

        qs = Device.objects.all()
        if dtype:
            qs = qs.filter(type=dtype)
        if status:
            qs = qs.filter(status=status)
        qs = qs.order_by("-registered_at")
        return _ok([DeviceHub._device_to_dict(d) for d in qs])
    except Exception as e:
        logger.exception("devices_list 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def device_register(request):
    """POST /api/devices/register — 注册（或更新）设备。

    body: {"device_id"(必填), "name", "type", "ip", "status", "battery", "firmware"}
    """
    try:
        params = f_parsePostParams(request)
        if not _s(params.get("device_id")):
            return _fail("device_id 必填")
        data = DeviceHub().register_device(params)
        return _ok(data)
    except ValueError as e:
        return _fail(str(e))
    except Exception as e:
        logger.exception("device_register 异常: %s", e)
        return _fail(str(e), code=500)


def device_status(request, device_id):
    """GET /api/devices/<device_id>/status — 设备状态（在线/离线/电量）。"""
    try:
        return _ok(DeviceHub().get_device_status(device_id))
    except Exception as e:
        logger.exception("device_status 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def device_ptz(request, device_id):
    """POST /api/devices/<device_id>/ptz — PTZ 控制。

    body: {"direction": "left/right/up/down/preset/track", "angle": 90}
    """
    try:
        params = f_parsePostParams(request)
        direction = _s(params.get("direction")) or "right"
        angle = params.get("angle", 90)
        return _ok(DeviceHub().control_ptz(device_id, direction, angle))
    except Exception as e:
        logger.exception("device_ptz 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def device_light(request, device_id):
    """POST /api/devices/<device_id>/light — 灯光控制。

    body: {"on_off": true, "brightness": 0~100}
    """
    try:
        params = f_parsePostParams(request)
        on_off = bool(params.get("on_off", True))
        try:
            brightness = int(params.get("brightness", 100))
        except (TypeError, ValueError):
            brightness = 100
        return _ok(DeviceHub().control_light(device_id, on_off, brightness))
    except Exception as e:
        logger.exception("device_light 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def device_audio(request, device_id):
    """POST /api/devices/<device_id>/audio — 播放音频。

    body: {"audio_url": "https://..."}
    """
    try:
        params = f_parsePostParams(request)
        audio_url = _s(params.get("audio_url"))
        if not audio_url:
            return _fail("audio_url 必填")
        return _ok(DeviceHub().play_audio(device_id, audio_url))
    except Exception as e:
        logger.exception("device_audio 异常: %s", e)
        return _fail(str(e), code=500)


@csrf_exempt
def device_cross_track(request, device_id):
    """POST /api/devices/<device_id>/cross-track — 跨摄像头联动（自带防抖）。

    body: {"track_id": "t1", "target_camera_id": "cam-b"(可选)}
    """
    try:
        params = f_parsePostParams(request)
        track_id = _s(params.get("track_id"))
        if not track_id:
            return _fail("track_id 必填")
        target = params.get("target_camera_id")
        result = DeviceHub().cross_camera_track(
            device_id, track_id,
            target_camera_id=target if target is not None else None)
        return _ok(result)
    except Exception as e:
        logger.exception("device_cross_track 异常: %s", e)
        return _fail(str(e), code=500)


def commands_list(request):
    """GET /api/devices/commands?device_id=&limit= — 命令历史。"""
    try:
        params = f_parseGetParams(request)
        device_id = _s(params.get("device_id", ""))
        try:
            limit = int(params.get("limit", 100))
        except (TypeError, ValueError):
            limit = 100
        data = DeviceHub.get_command_history(
            camera_id=device_id if device_id else None, limit=limit)
        return _ok(data)
    except Exception as e:
        logger.exception("commands_list 异常: %s", e)
        return _fail(str(e), code=500)
