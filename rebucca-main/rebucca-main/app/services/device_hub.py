# -*- coding: utf-8 -*-
"""
设备联动中枢 — DeviceHub。

职责：
  - 设备注册 / 状态查询
  - PTZ / 灯光 / 音频控制（每条命令 DeviceCommand 留痕：pending→success/failed）
  - 跨摄像头联动跟踪（防抖窗口，避免频繁切换）
  - 事件广播（推送到所有相关设备）

通用机制：
  - with_retry：错误重试 + 指数退避
  - 配置热更新：所有引擎每次从 DB 读取最新配置，无需重启服务
"""
import logging
import time
from datetime import datetime

from app.models import Device, DeviceCommand

logger = logging.getLogger("services.device_hub")


def with_retry(fn, attempts=3, base_delay=0.2, exceptions=(Exception,), label=""):
    """带指数退避的错误重试。

    Args:
        fn: 无参可调用对象
        attempts: 最大尝试次数（含首次）
        base_delay: 首次重试间隔，后续按 2 倍递增
        label: 日志标识
    Returns:
        fn 的返回值
    Raises:
        最后一次尝试的异常
    """
    last_exc = None
    for i in range(attempts):
        try:
            return fn()
        except exceptions as e:
            last_exc = e
            logger.warning("%s 第 %d/%d 次尝试失败: %s", label or "call", i + 1, attempts, e)
            if i < attempts - 1:
                time.sleep(base_delay * (2 ** i))
    raise last_exc


class DeviceHub:
    """设备联动中枢。类级维护跨实例共享的防抖表、拓扑表、订阅表。"""

    # 跨摄像头联动防抖窗口（秒）：同一轨迹同一交接方向在窗口内不重复切换
    HANDOFF_DEBOUNCE_SEC = 3.0

    # track_id -> (source_camera, target_camera, timestamp)
    _track_handoffs = {}
    # camera_id -> [neighbor camera_id]（摄像头邻接拓扑，用于自动选择联动目标）
    _topology = {}
    # key('*' 或 camera_id) -> [callback(event)]
    _subscribers = {"*": []}

    # ----------------------- 设备注册 / 状态 -----------------------

    def register_device(self, device_info):
        """注册（或更新）一台设备。

        Args:
            device_info: {"device_id"(必填), "name", "type", "ip",
                          "status", "battery", "firmware"}
        Returns:
            dict: 设备信息
        """
        device_id = str(device_info.get("device_id", "")).strip()
        if not device_id:
            raise ValueError("device_id 不能为空")

        dev = Device.objects.filter(device_id=device_id).first()
        if dev is None:
            dev = Device(device_id=device_id)

        dev.name = str(device_info.get("name", dev.name or ""))
        dtype = str(device_info.get("type", dev.type or Device.TYPE_OUTDOOR))
        allowed_types = {c[0] for c in Device.TYPE_CHOICES}
        dev.type = dtype if dtype in allowed_types else Device.TYPE_OUTDOOR
        dev.ip = str(device_info.get("ip", dev.ip or ""))

        status = str(device_info.get("status", dev.status or Device.STATUS_OFFLINE))
        dev.status = status if status in {Device.STATUS_ONLINE, Device.STATUS_OFFLINE} \
            else Device.STATUS_OFFLINE

        battery = device_info.get("battery", dev.battery)
        try:
            dev.battery = int(battery)
        except (TypeError, ValueError):
            dev.battery = -1
        dev.firmware = str(device_info.get("firmware", dev.firmware or ""))
        dev.save()

        logger.info("设备已注册/更新 device_id=%s type=%s status=%s",
                    device_id, dev.type, dev.status)
        return self._device_to_dict(dev)

    def get_device_status(self, camera_id):
        """获取设备状态（在线/离线/电量）。未注册时返回 registered=False，不抛异常。"""
        dev = self._find_device(camera_id)
        if dev is None:
            return {
                "device_id": str(camera_id),
                "registered": False,
                "status": Device.STATUS_OFFLINE,
                "battery": None,
                "name": "", "type": "", "firmware": "", "ip": "",
            }
        data = self._device_to_dict(dev)
        data["registered"] = True
        return data

    # ----------------------- 设备控制（全部留痕） -----------------------

    def control_ptz(self, camera_id, direction, angle):
        """PTZ 控制。direction: left/right/up/down/preset/track；angle: 角度/预设位。"""
        return self._dispatch(camera_id, "ptz", {
            "direction": str(direction), "angle": angle,
        })

    def control_light(self, camera_id, on_off, brightness):
        """灯光控制。brightness: 0~100。"""
        return self._dispatch(camera_id, "light", {
            "on": bool(on_off), "brightness": int(brightness),
        })

    def play_audio(self, camera_id, audio_url):
        """播放音频（远程音频 URL 或 TTS 文本资源）。"""
        return self._dispatch(camera_id, "audio", {"audio_url": str(audio_url)})

    # ----------------------- 跨摄像头联动 -----------------------

    def cross_camera_track(self, camera_id, track_id, target_camera_id=None):
        """跨摄像头联动：目标从 A 摄像头区域移动到 B 摄像头区域时，B 自动转向跟踪。

        防抖：同一 track_id、同一 source→target 交接在 HANDOFF_DEBOUNCE_SEC 内只执行一次。

        Args:
            camera_id: 源摄像头（刚检测到目标离开/接力的摄像头）
            track_id: 全局轨迹 ID
            target_camera_id: 可选，显式指定联动目标；为空则查邻接拓扑
        Returns:
            dict: 执行结果（handoff / debounced / no_target）
        """
        source = str(camera_id)
        track_key = str(track_id)

        # 1. 选择联动目标
        target = None
        if target_camera_id is not None:
            target = str(target_camera_id)
        else:
            neighbors = self._topology.get(source) or []
            if neighbors:
                target = str(neighbors[0])
        if not target:
            logger.info("跨摄像头联动无目标 track=%s from=%s（未指定目标且无拓扑）",
                        track_key, source)
            return {"result": "no_target", "track_id": track_key, "source": source}

        # 2. 防抖判定
        now = time.time()
        last = self._track_handoffs.get(track_key)
        if last is not None:
            prev_from, prev_to, prev_ts = last
            if prev_from == source and prev_to == target \
                    and (now - prev_ts) < self.HANDOFF_DEBOUNCE_SEC:
                logger.info("联动防抖命中，跳过 track=%s %s→%s", track_key, source, target)
                return {
                    "result": "debounced", "track_id": track_key,
                    "source": source, "target": target,
                }

        # 3. 目标摄像头 PTZ 自动转向跟踪
        action = self.control_ptz(target, "track", {"track_id": track_key, "from": source})

        # 4. 记录交接并广播
        self._track_handoffs[track_key] = (source, target, now)
        event = {
            "type": "cross_camera_handoff",
            "track_id": track_key,
            "source_camera": source,
            "target_camera": target,
            "timestamp": datetime.now().isoformat(),
            "targets": [target],
        }
        self.event_broadcast(event)
        logger.info("跨摄像头联动执行 track=%s %s→%s", track_key, source, target)
        return {
            "result": "handoff", "track_id": track_key,
            "source": source, "target": target, "action": action,
        }

    # ----------------------- 事件广播 -----------------------

    def event_broadcast(self, event):
        """事件广播：推送到所有相关设备 + 通知内存订阅者。

        event 可含 "targets": [camera_id,...]；为空则只推通配订阅者。
        """
        targets = [str(t) for t in (event.get("targets") or [])]

        # 1. 对目标设备生成 broadcast 命令留痕（未注册设备同样记录，device 可空）
        for t in targets:
            try:
                self._dispatch(t, "broadcast", {"event_type": event.get("type"),
                                                "event": event})
            except Exception as e:
                logger.warning("广播命令下发失败 target=%s: %s", t, e)

        # 2. 内存订阅回调（通配 + 精确订阅）
        callbacks = list(self._subscribers.get("*", []))
        for t in targets:
            callbacks.extend(self._subscribers.get(t, []))
        for cb in callbacks:
            try:
                cb(event)
            except Exception as e:
                logger.warning("广播订阅回调异常: %s", e)

        logger.info("事件广播 type=%s targets=%s subscribers=%d",
                    event.get("type"), targets, len(callbacks))
        return {"broadcast": True, "targets": targets, "subscribers": len(callbacks)}

    def subscribe(self, key, callback):
        """订阅事件。key='*' 接收全部事件，或指定 camera_id。"""
        k = "*" if key in (None, "*") else str(key)
        self._subscribers.setdefault(k, []).append(callback)

    @classmethod
    def set_camera_neighbors(cls, camera_id, neighbors):
        """设置摄像头邻接拓扑（用于跨摄像头联动自动选目标）。"""
        cls._topology[str(camera_id)] = [str(n) for n in neighbors]

    # ----------------------- 命令历史 -----------------------

    @staticmethod
    def get_command_history(camera_id=None, limit=100):
        """查询设备命令历史，可按设备过滤。"""
        qs = DeviceCommand.objects.all()
        if camera_id is not None:
            dev = DeviceHub()._find_device(camera_id)
            if dev is not None:
                qs = qs.filter(device=dev)
        qs = qs.order_by("-created_at")[:max(1, min(int(limit), 500))]
        return [DeviceHub._command_to_dict(c) for c in qs]

    # ----------------------- 内部方法 -----------------------

    def _dispatch(self, camera_id, command_type, payload):
        """命令统一下发：建命令记录(pending) → 重试执行 → 更新状态/时间。"""
        dev = self._find_device(camera_id)
        target_label = dev.device_id if dev is not None else str(camera_id)

        cmd = DeviceCommand.objects.create(
            device=dev, command_type=command_type,
            payload=payload, status=DeviceCommand.STATUS_PENDING,
        )
        result = "ok"
        try:
            with_retry(
                lambda: self._send_command(dev, command_type, payload),
                label=f"{command_type}->{target_label}",
            )
            cmd.status = DeviceCommand.STATUS_SUCCESS
            # 命令成功：设备可触达 → 标记在线
            if dev is not None and dev.status != Device.STATUS_ONLINE:
                dev.status = Device.STATUS_ONLINE
                dev.save(update_fields=["status"])
        except Exception as e:
            cmd.status = DeviceCommand.STATUS_FAILED
            result = f"error:{e}"
            logger.exception("设备命令执行失败 %s -> %s: %s",
                             target_label, command_type, e)
        cmd.executed_at = datetime.now()
        cmd.save()

        return {
            "action": command_type,
            "device_id": target_label,
            "payload": payload,
            "result": result,
            "command_id": cmd.id,
        }

    def _send_command(self, device, command_type, payload):
        """实际下发到硬件/协议栈的位置（stub）。

        当前环境无真实设备：记录日志即视为成功。
        接入真实硬件时替换此方法（ONVIF / HomeKit / 4G 私有协议）。
        """
        target = device.device_id if device is not None else payload.get("device_id", "?")
        logger.info("[stub] 下发命令 %s -> %s payload=%s", command_type, target, payload)
        return True

    def _find_device(self, camera_id):
        """按 device_id 查找设备；兼容数字主键。"""
        s = str(camera_id)
        dev = Device.objects.filter(device_id=s).first()
        if dev is None:
            try:
                dev = Device.objects.filter(id=int(s)).first()
            except (TypeError, ValueError):
                dev = None
        return dev

    @staticmethod
    def _device_to_dict(dev):
        return {
            "id": dev.id,
            "device_id": dev.device_id,
            "name": dev.name,
            "type": dev.type,
            "ip": dev.ip,
            "status": dev.status,
            "battery": dev.battery,
            "firmware": dev.firmware,
            "registered_at": dev.registered_at.isoformat(),
        }

    @staticmethod
    def _command_to_dict(c):
        return {
            "id": c.id,
            "device_id": c.device.device_id if c.device is not None else None,
            "command_type": c.command_type,
            "payload": c.payload or {},
            "status": c.status,
            "created_at": c.created_at.isoformat(),
            "executed_at": c.executed_at.isoformat() if c.executed_at else None,
        }
