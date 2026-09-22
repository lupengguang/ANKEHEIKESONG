# -*- coding: utf-8 -*-
"""
实时事件总线 — 进程内发布/订阅（供 SSE 推送到前端）。

项目未安装 Django Channels，因此使用 SSE（Server-Sent Events）实现
“WebSocket 级”的服务端主动推送：
  - 发布方：publish(event_dict)
  - 订阅方：subscribe() 得到 Queue，用完 unsubscribe(q)
  - HTTP：GET /api/events/stream，前端用 EventSource 监听
"""
import json
import logging
import queue
import threading
import time

logger = logging.getLogger("services.event_bus")


class EventBus:
    """线程安全的进程内事件总线（单例）。"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._subscribers = []
                    obj._sub_lock = threading.Lock()
                    cls._instance = obj
        return cls._instance

    def subscribe(self):
        """订阅事件，返回一个 queue.Queue。"""
        q = queue.Queue(maxsize=100)
        with self._sub_lock:
            self._subscribers.append(q)
        logger.info("SSE 新订阅者，当前订阅数=%d", len(self._subscribers))
        return q

    def unsubscribe(self, q):
        """取消订阅。"""
        with self._sub_lock:
            if q in self._subscribers:
                self._subscribers.remove(q)
        logger.info("SSE 订阅者退出，当前订阅数=%d", len(self._subscribers))

    def publish(self, event):
        """向所有订阅者发布事件（队列满时丢弃最旧事件，不阻塞业务）。"""
        payload = json.dumps(event, ensure_ascii=False, default=str)
        with self._sub_lock:
            subscribers = list(self._subscribers)
        for q in subscribers:
            try:
                q.put_nowait(payload)
            except queue.Full:
                try:
                    q.get_nowait()
                    q.put_nowait(payload)
                except Exception:
                    pass

    def stream(self):
        """SSE 生成器：输出 event 数据帧 + 15 秒心跳。"""
        q = self.subscribe()
        try:
            # 连接建立事件，便于前端确认链路
            yield ": connected\n\n"
            while True:
                try:
                    payload = q.get(timeout=15)
                    yield f"data: {payload}\n\n"
                except queue.Empty:
                    # 心跳，防止代理/浏览器断开空闲连接
                    yield f": heartbeat {int(time.time())}\n\n"
        finally:
            self.unsubscribe(q)
