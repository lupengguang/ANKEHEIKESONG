# -*- coding: utf-8 -*-
"""
摄像头管理器 — CameraManager（进程内单例）。

职责：
  - 统一持有 LocalCameraStream，避免 MJPEG 与分析引擎重复打开设备
  - 后台采集线程持续读帧，缓存最新帧与最新 JPEG
  - MJPEG 生成器在有新帧时推送（multipart/x-mixed-replace）
  - start/stop 联动 WelcomeSceneEngine
  - 摄像头不存在 / 被占用时返回友好错误，不抛异常、不崩溃
"""
import logging
import os
import threading
import time

import cv2

from app.services.video_stream import LocalCameraStream
from app.services.vlm_client import load_env_file

logger = logging.getLogger("services.camera_manager")


class CameraManager:
    """摄像头 + 迎宾引擎的统一管理器。"""

    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._initialized = False
                    cls._instance = obj
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.stream = None
        self.engine = None
        self._thread = None
        self._stop_event = threading.Event()
        self._new_frame = threading.Event()

        self._latest_frame = None
        self._latest_jpeg = None
        self.frame_count = 0
        self._read_fail_count = 0
        self.last_error = ""
        self.started_at = None

    # ----------------------- 启动 / 停止 -----------------------

    def start(self, camera_index=None):
        """打开摄像头并启动迎宾引擎。

        Returns:
            {"ok": bool, "message": str, "data": dict}
        """
        if self.is_running():
            return {"ok": True, "message": "摄像头已在运行",
                    "data": self.status()}

        load_env_file()
        if camera_index is None:
            camera_index = int(os.environ.get("CAMERA_INDEX", 0))

        self.stream = LocalCameraStream(camera_index)
        if not self.stream.is_opened():
            self.last_error = self.stream.last_error or "摄像头打开失败"
            self.stream = None
            return {"ok": False,
                    "message": f"无法启动：{self.last_error}"}

        # 重置计数 / 状态
        self._stop_event.clear()
        self._new_frame.clear()
        self.frame_count = 0
        self._read_fail_count = 0
        self.started_at = time.time()

        # 启动采集线程
        self._thread = threading.Thread(
            target=self._read_loop, name="camera-reader", daemon=True)
        self._thread.start()

        # 启动迎宾场景引擎
        from app.services.welcome_scene import WelcomeSceneEngine
        self.engine = WelcomeSceneEngine(self)
        self.engine.start()

        logger.info("摄像头与迎宾引擎已启动 cam_index=%d", camera_index)
        return {"ok": True, "message": "摄像头已启动",
                "data": self.status()}

    def stop(self):
        """停止引擎、采集线程并释放摄像头。"""
        if self.engine is not None:
            self.engine.stop()
            self.engine = None

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None

        if self.stream is not None:
            self.stream.release()
            self.stream = None

        self._latest_frame = None
        self._latest_jpeg = None
        logger.info("摄像头已停止")
        return {"ok": True, "message": "摄像头已停止"}

    def is_running(self):
        return self.stream is not None and self.stream.is_opened()

    # ----------------------- 采集线程 -----------------------

    def _read_loop(self):
        """持续读帧：更新最新帧/JPEG，通知 MJPEG 生成器。"""
        while not self._stop_event.is_set():
            ok, frame = self.stream.get_frame()
            if not ok or frame is None:
                self._read_fail_count += 1
                if self._read_fail_count > 50:
                    self.last_error = self.stream.last_error \
                        or "连续读取帧失败，摄像头可能已断开"
                    logger.error(self.last_error)
                    break
                time.sleep(0.05)
                continue

            self._read_fail_count = 0
            self._latest_frame = frame
            ok_jpg, buf = cv2.imencode(
                ".jpg", frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok_jpg:
                self._latest_jpeg = buf.tobytes()
            self.frame_count += 1
            # 通知等待者，并立即重置下一帧事件
            self._new_frame.set()

    # ----------------------- 帧访问 -----------------------

    def get_latest_frame(self):
        """返回最新 BGR 帧（numpy）。"""
        return self._latest_frame

    def get_latest_jpeg(self):
        """返回最新 JPEG 字节。"""
        return self._latest_jpeg

    # ----------------------- MJPEG -----------------------

    def mjpeg_stream(self):
        """MJPEG 生成器：运行时推送实时帧；未运行时循环推送占位图。"""
        boundary_logged = False
        while True:
            if self.is_running():
                self._new_frame.wait(timeout=10)
                self._new_frame.clear()
                jpeg = self._latest_jpeg
                if jpeg is None:
                    continue
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
                boundary_logged = True
            else:
                # 摄像头未启动：友好占位画面（1 帧/秒），前端仍可正常渲染
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n"
                       + self.placeholder_jpeg() + b"\r\n")
                time.sleep(1)

    @staticmethod
    def placeholder_jpeg():
        """生成“摄像头未启动”占位 JPEG。"""
        import numpy as np
        img = np.full((480, 640, 3), 245, dtype=np.uint8)
        cv2.putText(img, "Camera stopped", (170, 220),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (100, 116, 139), 2)
        cv2.putText(img, "Click 'Start' to open local camera",
                    (120, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (148, 163, 184), 1)
        ok, buf = cv2.imencode(".jpg", img)
        return buf.tobytes() if ok else b""

    # ----------------------- 状态 -----------------------

    def status(self):
        """摄像头状态：是否运行、分辨率、帧数、引擎触发次数等。"""
        running = self.is_running()
        width, height = self.stream.resolution if running else (0, 0)
        return {
            "running": running,
            "width": width,
            "height": height,
            "frame_count": self.frame_count,
            "uptime_sec": round(time.time() - self.started_at, 1)
            if self.started_at and running else 0,
            "trigger_count": self.engine.trigger_count
            if self.engine is not None else 0,
            "last_error": self.last_error,
        }
