# -*- coding: utf-8 -*-
"""
无网场景引擎 — OfflineSceneEngine（4G 摄像头）。

核心能力：
  intrusion_mode         远距离入侵防御：YOLO person → 100 流明补光 + PTZ 跟踪 + 语音驱离
  animal_monitor         动物异常监测：dog/cat/bird → 记录片段 + 推送通知
  low_bandwidth_optimize 低带宽优化：边缘端先做 AI，告警才传视频，正常只传关键帧
  offline_buffer_replay  离线补传：4G 断网本地缓存事件，网络恢复自动补传

热更新：配置每次从 DB 实时读取（OfflineSceneConfig），修改即生效，无需重启。
"""
import logging
from datetime import datetime

from app.models import OfflineSceneConfig, OfflineEvent
from app.services.device_hub import DeviceHub

logger = logging.getLogger("services.offline_scene")


class OfflineSceneEngine:
    """无网场景引擎：边缘 AI + 低带宽传输 + 断网缓存补传。"""

    DEFAULT_CONFIG = {
        "intrusion_enabled": True,
        "animal_monitor_enabled": True,
        "low_bandwidth_mode": True,
        "offline_buffer_enabled": True,
        "buffer_size_limit": 100,  # MB
    }

    AUDIO_INTRUSION = "tts://警告：这里是私人区域，请立即离开"

    # 流量估算（字节，stub 用于统计演示）
    SIZE_VIDEO_CLIP = 2_500_000
    SIZE_KEYFRAME = 120_000

    # 模拟网络状态（测试可直接改类属性或 monkeypatch is_network_ok）
    network_available = True

    # 流量/补传统计（类级共享）
    bytes_video_uploaded = 0
    bytes_keyframes_uploaded = 0
    alarms_count = 0
    replayed_count = 0

    # ----------------------- 统一入口 -----------------------

    def on_motion_detected(self, camera_id, frame=None, snapshot_path=""):
        """4G 摄像头运动事件入口：入侵 + 动物监测，低带宽策略决定上传内容。"""
        cfg = self.get_effective_config(camera_id)
        results = []

        if cfg.get("intrusion_enabled"):
            results.append(self.intrusion_mode(camera_id, frame, cfg=cfg))
        if cfg.get("animal_monitor_enabled"):
            results.append(self.animal_monitor(camera_id, frame, cfg=cfg))

        triggered = [r for r in results if r.get("triggered")]
        logger.info("4G 运动事件 cam=%s 告警 %d/%d",
                    camera_id, len(triggered), len(results))
        return {
            "camera_id": int(camera_id),
            "modes": results,
            "triggered_count": len(triggered),
        }

    # ----------------------- 入侵防御 -----------------------

    def intrusion_mode(self, camera_id, frame, cfg=None):
        """远距离入侵：person → 100 流明补光灯 + PTZ 跟踪 + 语音驱离。"""
        cfg = cfg or self.get_effective_config(camera_id)
        persons = self.detect_objects(frame, labels=("person",))
        if not persons:
            return {"mode": "intrusion", "triggered": False}

        target = persons[0]
        hub = DeviceHub()
        actions = [
            hub.control_light(camera_id, True, 100),   # 100 流明
            hub.control_ptz(camera_id, "track", target.get("bbox")),
            hub.play_audio(camera_id, self.AUDIO_INTRUSION),
        ]
        video_path = self._clip_path(camera_id, "intrusion")

        # 低带宽策略：边缘端先做 AI → 仅告警上传视频
        policy = self.low_bandwidth_optimize(cfg, is_alarm=True)
        event = self._register_event(
            camera_id, event_type="intrusion",
            snapshot_path="", video_path=video_path if policy["upload_video"] else "",
            cfg=cfg,
        )
        hub.event_broadcast({
            "type": "offline_intrusion",
            "camera_id": int(camera_id),
            "event_id": event.id,
            "timestamp": datetime.now().isoformat(),
            "targets": [],
        })

        type(self).alarms_count += 1
        logger.warning("入侵防御触发 cam=%s policy=%s", camera_id, policy)
        return {
            "mode": "intrusion", "triggered": True,
            "event_id": event.id, "actions": actions,
            "upload_policy": policy, "buffered": event.is_replayed == 0
            and not self.is_network_ok(),
        }

    # ----------------------- 动物异常监测 -----------------------

    def animal_monitor(self, camera_id, frame, cfg=None):
        """动物异常：dog/cat/bird → 记录片段 + 推送通知。"""
        cfg = cfg or self.get_effective_config(camera_id)
        animals = self.detect_objects(frame, labels=("dog", "cat", "bird"))
        if not animals:
            return {"mode": "animal", "triggered": False}

        target = animals[0]
        video_path = self._clip_path(camera_id, "animal")

        # 低带宽策略：动物事件视为非紧急 → 默认只传关键帧（省流量）
        policy = self.low_bandwidth_optimize(cfg, is_alarm=False)
        event = self._register_event(
            camera_id, event_type="animal",
            snapshot_path="", video_path=video_path if policy["upload_video"] else "",
            cfg=cfg,
        )

        hub = DeviceHub()
        hub.event_broadcast({
            "type": "offline_animal",
            "camera_id": int(camera_id),
            "animal": target.get("label"),
            "event_id": event.id,
            "timestamp": datetime.now().isoformat(),
            "targets": [],
        })
        logger.info("动物监测记录 cam=%s animal=%s policy=%s",
                    camera_id, target.get("label"), policy)
        return {
            "mode": "animal", "triggered": True,
            "animal": target.get("label"), "event_id": event.id,
            "upload_policy": policy,
        }

    # ----------------------- 低带宽优化 -----------------------

    def low_bandwidth_optimize(self, cfg, is_alarm):
        """边缘端 AI 先行的上传决策。

        Returns:
            dict: {"upload_video": bool, "keyframe_only": bool,
                   "bytes": int, "edge_filtered": bool}
        """
        low_mode = bool(cfg.get("low_bandwidth_mode", True))
        if not low_mode:
            # 未启用低带宽优化：视频照常上传
            type(self).bytes_video_uploaded += self.SIZE_VIDEO_CLIP
            return {"upload_video": True, "keyframe_only": False,
                    "bytes": self.SIZE_VIDEO_CLIP, "edge_filtered": False}

        if is_alarm:
            type(self).bytes_video_uploaded += self.SIZE_VIDEO_CLIP
            return {"upload_video": True, "keyframe_only": False,
                    "bytes": self.SIZE_VIDEO_CLIP, "edge_filtered": True}

        # 正常情况：只传关键帧
        type(self).bytes_keyframes_uploaded += self.SIZE_KEYFRAME
        return {"upload_video": False, "keyframe_only": True,
                "bytes": self.SIZE_KEYFRAME, "edge_filtered": True}

    # ----------------------- 离线缓存补传 -----------------------

    def offline_buffer_replay(self, camera_id=None):
        """网络恢复后补传本地缓存事件。

        无网络时直接返回 waiting；有网络时把 is_replayed=0 的事件标记为已补传。
        """
        if not self.is_network_ok():
            logger.info("网络未恢复，等待补传 cam=%s", camera_id)
            return {"replayed": False, "reason": "network_unavailable", "count": 0}

        qs = OfflineEvent.objects.filter(is_replayed=0)
        if camera_id is not None:
            qs = qs.filter(camera_id=int(camera_id))
        pending = list(qs)

        now = datetime.now()
        for ev in pending:
            ev.is_replayed = 1
            ev.replayed_at = now
            ev.save(update_fields=["is_replayed", "replayed_at"])

        type(self).replayed_count += len(pending)
        logger.info("离线补传完成 cam=%s 补传 %d 条", camera_id, len(pending))
        return {
            "replayed": True, "count": len(pending),
            "event_ids": [e.id for e in pending], "replayed_at": now.isoformat(),
        }

    def is_network_ok(self):
        """网络状态检查点（stub 返回类属性；接入时替换为真实链路检测）。"""
        return bool(type(self).network_available)

    # ----------------------- 检测 / 统计 -----------------------

    def detect_objects(self, frame, labels=("person",)):
        """目标检测：优先使用 frame(dict) 中上层已写入的 detections。"""
        wanted = {str(x).lower() for x in labels}
        if isinstance(frame, dict):
            return [d for d in (frame.get("detections") or [])
                    if str(d.get("label", "")).lower() in wanted]
        try:
            from app.analysis.detector import Detector  # noqa: F401
            # 预留：return Detector().infer(frame, labels=wanted)
        except Exception as e:
            logger.debug("YOLO 不可用，跳过检测: %s", e)
        return []

    @classmethod
    def get_stats(cls, camera_id=None):
        """流量与补传统计。"""
        qs = OfflineEvent.objects.all()
        if camera_id is not None:
            qs = qs.filter(camera_id=int(camera_id))

        total = qs.count()
        pending = qs.filter(is_replayed=0).count()
        replayed = qs.filter(is_replayed=1).count()
        intrusions = qs.filter(event_type="intrusion").count()
        animals = qs.filter(event_type="animal").count()

        cfg_limit = 100
        if camera_id is not None:
            row = OfflineSceneConfig.objects.filter(camera_id=int(camera_id)).first()
            if row is not None:
                cfg_limit = int((row.config or {}).get("buffer_size_limit", 100))
        # 缓存占用按待传事件估算（MB），不超过配置上限
        buffer_used = round(
            min(pending * cls.SIZE_VIDEO_CLIP / 1_000_000, cfg_limit), 2)

        return {
            "network_ok": cls().is_network_ok(),
            "total_events": total,
            "intrusion_events": intrusions,
            "animal_events": animals,
            "pending_replay": pending,
            "replayed_events": replayed,
            "bytes_video_uploaded": cls.bytes_video_uploaded,
            "bytes_keyframes_uploaded": cls.bytes_keyframes_uploaded,
            "edge_alarms": cls.alarms_count,
            "replayed_in_session": cls.replayed_count,
            "buffer_used_mb": buffer_used,
            "buffer_limit_mb": cfg_limit,
        }

    # ----------------------- 配置管理（热更新） -----------------------

    @classmethod
    def get_effective_config(cls, camera_id):
        """读取某摄像头生效配置：默认值 ← 配置行覆盖（每次实时查库）。"""
        cfg = dict(cls.DEFAULT_CONFIG)
        row = OfflineSceneConfig.objects.filter(camera_id=int(camera_id)).first()
        if row is not None:
            if not bool(row.enabled):
                cfg.update({"intrusion_enabled": False, "animal_monitor_enabled": False})
            if isinstance(row.config, dict):
                cfg.update(row.config)
        return cfg

    @staticmethod
    def get_configs(camera_id):
        return list(OfflineSceneConfig.objects.filter(camera_id=int(camera_id)))

    @staticmethod
    def upsert_config(camera_id, enabled=True, config=None):
        """新增或更新配置（热更新写入点，保存后立即生效）。"""
        obj = OfflineSceneConfig.objects.filter(camera_id=int(camera_id)).first()
        if obj is None:
            obj = OfflineSceneConfig(
                camera_id=int(camera_id),
                enabled=1 if enabled else 0, config=config or {},
            )
        else:
            obj.enabled = 1 if enabled else 0
            if config is not None:
                obj.config = config
            obj.last_update_time = datetime.now()
        obj.save()
        return obj

    # ----------------------- 测试入口 -----------------------

    def test_intrusion(self, camera_id):
        """手动测试入侵防御：注入合成 person 检测。"""
        synth = {"detections": [
            {"label": "person", "confidence": 0.97, "bbox": [60, 40, 420, 520]}]}
        return self.intrusion_mode(int(camera_id), synth)

    # ----------------------- 内部方法 -----------------------

    def _register_event(self, camera_id, event_type, snapshot_path,
                        video_path, cfg):
        """事件落库：断网且启用缓存 → is_replayed=0 待补传；否则视为已上传(1)。"""
        network_ok = self.is_network_ok()
        buffered = (not network_ok) and bool(cfg.get("offline_buffer_enabled", True))

        ev = OfflineEvent.objects.create(
            camera_id=int(camera_id),
            event_type=event_type,
            timestamp=datetime.now(),
            snapshot_path=snapshot_path or "",
            video_path=video_path or "",
            is_replayed=0 if buffered else 1,
            replayed_at=None if buffered else datetime.now(),
        )
        if buffered:
            logger.info("事件已本地缓存待补传 cam=%s type=%s", camera_id, event_type)
        return ev

    @staticmethod
    def _clip_path(camera_id, kind):
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"static/upload/clips/{kind}_cam{camera_id}_{ts}.mp4"
