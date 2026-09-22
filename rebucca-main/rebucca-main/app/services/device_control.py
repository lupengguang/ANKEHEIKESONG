# -*- coding: utf-8 -*-
"""
模拟设备控制 — MockDeviceControl。

不需要真实硬件：
  ptz_goto  打印日志并记录到 device_commands 表（命令留痕）
  light_on  打印日志
  tts_speak 打印日志

每个方法返回动作 dict（供 triggered_actions 落库）。
"""
import logging
from datetime import datetime

logger = logging.getLogger("services.device_control")


class MockDeviceControl:
    """设备能力模拟。"""

    def __init__(self, camera_id="local-cam"):
        self.camera_id = str(camera_id)

    def ptz_goto(self, camera_id, position):
        """PTZ 转向（position：up/down/left/right/center 等）。"""
        logger.info("[模拟PTZ] camera=%s 转向 -> %s", camera_id, position)
        command_id = self._record_command(camera_id, "ptz",
                                          {"position": str(position)})
        return {"action": "ptz", "camera_id": str(camera_id),
                "position": str(position), "result": "ok",
                "command_id": command_id}

    def light_on(self, camera_id, brightness):
        """补光灯/迎宾灯亮起。"""
        logger.info("[模拟灯光] camera=%s 亮度 -> %s%%", camera_id, brightness)
        return {"action": "light", "camera_id": str(camera_id),
                "brightness": int(brightness), "result": "ok"}

    def tts_speak(self, camera_id, text):
        """语音问候。"""
        logger.info("[模拟语音] camera=%s 内容 -> %s", camera_id, text)
        return {"action": "tts", "camera_id": str(camera_id),
                "text": str(text), "result": "ok"}

    @staticmethod
    def _record_command(camera_id, command_type, payload):
        """记录到 device_commands 表（设备未注册时 device 为空，同样留痕）。"""
        from app.models import Device, DeviceCommand
        dev = Device.objects.filter(device_id=str(camera_id)).first()
        cmd = DeviceCommand.objects.create(
            device=dev, command_type=command_type, payload=payload,
            status=DeviceCommand.STATUS_SUCCESS,
            executed_at=datetime.now(),
        )
        return cmd.id
