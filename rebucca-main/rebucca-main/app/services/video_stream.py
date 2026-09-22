# -*- coding: utf-8 -*-
"""
本地摄像头视频流服务 — LocalCameraStream。

- 初始化时通过 cv2.VideoCapture(index) 打开本地摄像头
- get_frame() 读取一帧，返回 (ok: bool, frame: numpy.ndarray|None)
- release() 释放摄像头
- 摄像头打不开 / 读帧失败时给出明确错误信息（不抛出，由上层处理）
"""
import logging

import cv2

logger = logging.getLogger("services.video_stream")


class LocalCameraStream:
    """本地摄像头封装。"""

    def __init__(self, camera_index=0, width=1280, height=720):
        self.camera_index = int(camera_index)
        self.width = int(width)
        self.height = int(height)
        self.cap = None
        self.last_error = ""

        logger.info("正在打开本地摄像头 index=%d ...", self.camera_index)
        # Windows 下优先使用 MSMF 后端，失败时回退默认（CAP_ANY）
        for backend in (cv2.CAP_MSMF, cv2.CAP_ANY):
            cap = cv2.VideoCapture(self.camera_index, backend)
            if cap.isOpened():
                self.cap = cap
                break
            cap.release()

        if self.cap is None:
            self.last_error = (
                f"无法打开本地摄像头(index={self.camera_index})，"
                "请检查摄像头是否被占用、是否已授予应用摄像头权限")
            logger.error(self.last_error)
            return

        # 尽量设置分辨率（设备不支持时 OpenCV 会静默回退，以实际读取为准）
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        ok, frame = self.cap.read()
        if not ok or frame is None:
            self.last_error = (
                f"摄像头(index={self.camera_index})已打开，但读取首帧失败，"
                "请检查设备是否正常工作")
            logger.error(self.last_error)
            self.cap.release()
            self.cap = None
            return

        logger.info("摄像头已打开 index=%d 实际分辨率=%dx%d",
                    self.camera_index, frame.shape[1], frame.shape[0])

    def is_opened(self):
        """摄像头是否处于可用状态。"""
        return self.cap is not None and self.cap.isOpened()

    def get_frame(self):
        """读取一帧。

        Returns:
            (True, numpy.ndarray) 或 (False, None)
        """
        if not self.is_opened():
            self.last_error = "摄像头未打开或已断开"
            return False, None
        ok, frame = self.cap.read()
        if not ok or frame is None:
            self.last_error = "读取摄像头帧失败"
            logger.warning(self.last_error)
            return False, None
        return True, frame

    @property
    def resolution(self):
        """当前分辨率（宽, 高）；未打开时为 (0, 0)。"""
        if not self.is_opened():
            return 0, 0
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return w, h

    def release(self):
        """释放摄像头资源。"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("摄像头已释放 index=%d", self.camera_index)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
