# 作者：北小菜
# 官网：https://www.yuturuishi.com
# 微信：bilibili_bxc
# 哔哩哔哩主页：https://space.bilibili.com/487906612
# gitee地址：https://gitee.com/Vanishi/rebucca
# github地址：https://github.com/beixiaocai/rebucca
from django.db import models
from app.utils.Database import g_dbLock
import json


class ThreadSafetyManager(models.Manager):
    def get_queryset(self):
        with g_dbLock:
            ret = super(ThreadSafetyManager, self).get_queryset()
        return ret


class StreamModel(models.Model):
    """视频流模型（摄像头管理）"""
    objects = ThreadSafetyManager()

    user_id = models.IntegerField(verbose_name='用户')
    sort = models.IntegerField(verbose_name='排序')
    code = models.CharField(max_length=50, verbose_name='编号')
    app = models.CharField(max_length=50, verbose_name='流分组')
    name = models.CharField(max_length=50, verbose_name='流名称')
    pull_stream_url = models.CharField(max_length=300, verbose_name='视频流源地址')
    pull_stream_type = models.IntegerField(verbose_name='视频流来源类型')  # 0:未知,1:RTSP,2:RTMP,3:FLV,4:HLS,21:GB28181,31:被动RTSP,32:被动RTMP
    pull_stream_transfer_mode = models.IntegerField(verbose_name='视频流传输模式')  # 0:UDP,1:TCP被动,2:TCP主动
    pull_stream_ip = models.CharField(max_length=50, verbose_name='拉流IP')
    pull_stream_port = models.IntegerField(verbose_name='拉流端口')
    pull_stream_username = models.CharField(max_length=50, verbose_name='拉流用户名')
    pull_stream_password = models.CharField(max_length=50, verbose_name='拉流密码')
    nickname = models.CharField(max_length=200, verbose_name='视频流昵称')
    remark = models.CharField(max_length=200, verbose_name='备注')
    forward_state = models.IntegerField(verbose_name='转发状态')  # 0:未转发 1:转发中
    is_audio = models.IntegerField(default=0, verbose_name='音频传输类型')  # 0:静音 1:原始声音
    snap_filepath = models.CharField(max_length=200, verbose_name='快照文件路径')
    snap_time = models.DateTimeField(auto_now_add=True, verbose_name='快照时间')
    camera_sum_num = models.IntegerField(default=0, verbose_name='通道总数')
    camera_name = models.CharField(max_length=100, verbose_name='摄像头名称')
    camera_manufacturer = models.CharField(max_length=100, verbose_name='摄像头厂商')
    camera_owner = models.CharField(max_length=50, verbose_name='摄像头所属者')
    camera_model = models.CharField(max_length=50, verbose_name='摄像头型号')
    camera_device_id = models.CharField(max_length=50, verbose_name='GB28181设备ID')  # gb28181注册的client_id
    camera_parent_id = models.CharField(max_length=50, verbose_name='GB28181父设备ID')
    camera_civilcode = models.CharField(max_length=50, verbose_name='行政区划码')
    camera_last_keepalive_time = models.DateTimeField(auto_now_add=True, verbose_name='最近一次心跳时间')
    camera_last_register_time = models.DateTimeField(auto_now_add=True, verbose_name='最近一次注册时间')

    # 向上级联国标编号字段（v1.0新增）start
    cascade_device_id = models.CharField(max_length=50, default='', verbose_name='向上级联国标编号')  # 自定义向上级联的国标编号，为空则使用camera_device_id
    cascade_enable = models.IntegerField(default=0, verbose_name='是否启用向上级联')  # 0:不启用 1:启用
    # 向上级联国标编号字段 end

    # 视频分析字段（v1.0新增）start
    algorithm = models.ForeignKey('AlgorithmModel', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='streams', verbose_name='分析算法')  # null=走默认算法
    record_enable = models.IntegerField(default=0, verbose_name='启用24/7录像')  # 0:否 1:是
    # 视频分析字段 end

    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')
    add_type = models.IntegerField(default=0, verbose_name='添加类型')  # 0:手动添加 1:批量导入 10:接口添加 21:GB28181自动添加
    state = models.IntegerField(default=0, verbose_name='状态')

    def __repr__(self):
        return self.nickname

    def __str__(self):
        return self.nickname

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(StreamModel, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(StreamModel, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'av_stream'
        verbose_name = '视频流'
        verbose_name_plural = '视频流'


class AlgorithmModel(models.Model):
    """算法模型 — 检测算法的元数据与运行时参数（每路摄像头可独立选择）"""
    objects = ThreadSafetyManager()

    ENGINE_YOLO_PYTORCH = 'yolo_pytorch'
    ENGINE_ONNXRUNTIME = 'onnxruntime'
    ENGINE_OPENVINO = 'openvino'
    ENGINE_CHOICES = (
        (ENGINE_YOLO_PYTORCH, 'Yolo-PyTorch'),
        (ENGINE_ONNXRUNTIME, 'OnnxRuntime'),
        (ENGINE_OPENVINO, 'OpenVINO'),
    )

    # 算法类型：YOLO 检测系列 + ReID 特征系列
    ALGO_TYPE_YOLO5 = 'yolo5'
    ALGO_TYPE_YOLO8 = 'yolo8'
    ALGO_TYPE_YOLO11 = 'yolo11'
    ALGO_TYPE_YOLO26 = 'yolo26'
    ALGO_TYPE_OSNET = 'osnet'
    ALGO_TYPE_CHOICES = (
        (ALGO_TYPE_YOLO5, 'YOLOv5'),
        (ALGO_TYPE_YOLO8, 'YOLOv8'),
        (ALGO_TYPE_YOLO11, 'YOLOv11'),
        (ALGO_TYPE_YOLO26, 'YOLO26'),
        (ALGO_TYPE_OSNET, 'OSNet ReID'),
    )

    # 任务类型
    TASK_DETECT = 'detect'
    TASK_SEGMENT = 'segment'
    TASK_CLASSIFY = 'classify'
    TASK_POSE = 'pose'
    TASK_OBB = 'obb'
    TASK_REID = 'reid'
    TASK_CHOICES = (
        (TASK_DETECT, 'Detect'),
        (TASK_SEGMENT, 'Segment'),
        (TASK_CLASSIFY, 'Classify'),
        (TASK_POSE, 'Pose'),
        (TASK_OBB, 'OBB'),
        (TASK_REID, 'ReID'),
    )

    # 推理设备
    DEVICE_CPU = 'cpu'
    DEVICE_CUDA = 'cuda'
    DEVICE_GPU = 'gpu'
    DEVICE_CHOICES = (
        (DEVICE_CPU, 'CPU'),
        (DEVICE_CUDA, 'CUDA'),
        (DEVICE_GPU, 'GPU'),
    )

    name = models.CharField(max_length=100, verbose_name='算法名称')
    algorithm_type = models.CharField(max_length=30, default='yolo8', choices=ALGO_TYPE_CHOICES, verbose_name='算法类型')
    task_type = models.CharField(max_length=20, default=TASK_DETECT, choices=TASK_CHOICES, verbose_name='任务类型')
    inference_engine = models.CharField(max_length=20, default=ENGINE_YOLO_PYTORCH, choices=ENGINE_CHOICES, verbose_name='推理引擎')
    device = models.CharField(max_length=20, default=DEVICE_CPU, choices=DEVICE_CHOICES, verbose_name='推理设备')
    model_file = models.CharField(max_length=300, default='', verbose_name='模型文件相对路径')  # 相对 uploadDir/weight/
    model_file_size = models.IntegerField(default=0, verbose_name='模型文件大小(字节)')
    input_width = models.IntegerField(default=640, verbose_name='输入宽度')
    input_height = models.IntegerField(default=640, verbose_name='输入高度')
    conf_threshold = models.FloatField(default=0.4, verbose_name='置信度阈值')
    iou_threshold = models.FloatField(default=0.5, verbose_name='NMS IoU 阈值')
    labels = models.TextField(default='[]', verbose_name='支持类别JSON数组')  # ["person","car",...]
    is_default = models.IntegerField(default=0, verbose_name='是否默认算法')  # 1=全局兜底
    state = models.IntegerField(default=1, verbose_name='状态')  # 0=禁用 1=启用
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(AlgorithmModel, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(AlgorithmModel, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'av_algorithm'
        verbose_name = '小模型'
        verbose_name_plural = '小模型'


class BizAlgorithmModel(models.Model):
    """业务算法 — 小模型/大模型推理 + 后处理业务逻辑（布控绑定此表）"""
    objects = ThreadSafetyManager()

    FLOW_SMALL = 1
    FLOW_LLM = 2
    FLOW_BOTH = 3
    FLOW_DETECT_REID = 4
    FLOW_CHOICES = (
        (FLOW_SMALL, '小模型+后处理'),
        (FLOW_LLM, '大模型+后处理'),
        (FLOW_BOTH, '小模型+大模型+后处理'),
        (FLOW_DETECT_REID, '检测+ReID+后处理'),
    )

    POST_AREA = 'AREA'           # 区域入侵：目标中心在多边形内
    POST_LINE_CROSS = 'LINE_CROSS'  # 越线检测：轨迹跨过有向线段
    POST_LINE_COUNT = 'LINE_COUNT'  # 越线计数：正向/逆向分别累计，超阈值报警
    POST_DIRECTION = 'DIRECTION'  # 方向入侵：移动方向匹配设定方向
    POST_DENSITY = 'DENSITY'     # 密度报警：区域内目标数 >= 阈值
    POST_DWELL = 'DWELL'         # 滞留报警：在区域内停留 >= 阈值秒
    POST_CHOICES = (
        (POST_AREA, '区域入侵'),
        (POST_LINE_CROSS, '越线检测'),
        (POST_LINE_COUNT, '越线计数'),
        (POST_DIRECTION, '方向入侵'),
        (POST_DENSITY, '密度报警'),
        (POST_DWELL, '滞留报警'),
    )

    name = models.CharField(max_length=100, verbose_name='算法名称')
    flow_type = models.IntegerField(default=FLOW_SMALL, choices=FLOW_CHOICES, verbose_name='流程类型')
    small_model = models.ForeignKey(
        'AlgorithmModel', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='biz_algorithms', verbose_name='小模型',
    )
    detector_model = models.ForeignKey(
        'AlgorithmModel', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='biz_algorithms_as_detector', verbose_name='检测小模型(YOLO)',
    )
    target_labels = models.TextField(default='[]', verbose_name='目标类别JSON')  # ["person","car"]
    llm = models.ForeignKey(
        'LLMModel', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='biz_algorithms', verbose_name='大模型',
    )
    llm_prompt = models.TextField(default='', verbose_name='大模型提示词')
    llm_validate = models.TextField(default='', verbose_name='提示词校验值')  # 逗号分隔关键词
    post_process = models.CharField(max_length=30, default=POST_AREA, choices=POST_CHOICES, verbose_name='后处理逻辑')
    # DIRECTION 后处理参数：参考角度(0°=右,90°=下,180°=左,270°=上) 与容差
    ref_angle = models.FloatField(default=90.0, verbose_name='方向参考角度')
    angle_tolerance = models.FloatField(default=45.0, verbose_name='方向容差(度)')
    forward_count_threshold = models.IntegerField(default=0, verbose_name='正向计数报警阈值')  # 0=不报警
    reverse_count_threshold = models.IntegerField(default=0, verbose_name='逆向计数报警阈值')  # 0=不报警
    state = models.IntegerField(default=1, verbose_name='状态')  # 0=禁用 1=启用
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(BizAlgorithmModel, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(BizAlgorithmModel, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'av_biz_algorithm'
        verbose_name = '业务算法'
        verbose_name_plural = '业务算法'


class ZoneModel(models.Model):
    """摄像头区域（多边形）— 跨摄像头追踪/告警规则的区域定义"""
    objects = ThreadSafetyManager()

    stream = models.ForeignKey(StreamModel, on_delete=models.CASCADE, verbose_name='所属摄像头')
    name = models.CharField(max_length=100, verbose_name='区域名称')
    coordinates = models.TextField(verbose_name='多边形坐标')  # JSON: [[x1,y1],[x2,y2],...]
    is_required = models.IntegerField(default=1, verbose_name='是否必需区域')  # 1:目标必须在区域内才触发区域类后处理
    loiter_threshold = models.IntegerField(default=0, verbose_name='滞留阈值(秒)')  # 0=不检测滞留
    detect_interval_sec = models.FloatField(default=1.0, verbose_name='检测间隔(秒)')  # 每 N 秒
    detect_frames = models.IntegerField(default=1, verbose_name='检测帧数')  # 分析 M 帧，频率=M/N fps
    color = models.CharField(max_length=20, default='#169F85', verbose_name='显示颜色')
    # LINE_CROSS 后处理：警戒线段两端点(归一化坐标0~1)，JSON: [x,y]
    line_a = models.TextField(default='', verbose_name='警戒线端点A')  # JSON: [x,y] 归一化
    line_b = models.TextField(default='', verbose_name='警戒线端点B')  # JSON: [x,y] 归一化
    # DENSITY 后处理：密度报警阈值(区域内目标数)
    density_threshold = models.IntegerField(default=0, verbose_name='密度阈值')  # 0=不检测密度
    algorithms = models.ManyToManyField('BizAlgorithmModel', blank=True, related_name='zones', verbose_name='分析算法')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')
    state = models.IntegerField(default=1, verbose_name='状态')  # 1:启用 0:禁用

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(ZoneModel, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(ZoneModel, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'av_zone'
        verbose_name = '区域'
        verbose_name_plural = '区域'


class AlarmModel(models.Model):
    """报警记录 — 布控分析触发的报警事件"""
    objects = ThreadSafetyManager()

    EVENT_TYPES = (
        ('entered_zone', '进入区域'),
        ('loiter', '滞留告警'),
    )

    stream = models.ForeignKey(StreamModel, null=True, on_delete=models.CASCADE, verbose_name='摄像头')
    event_type = models.CharField(max_length=32, default='entered_zone', verbose_name='报警类型')
    description = models.CharField(max_length=300, default='', verbose_name='描述')
    timestamp = models.DateTimeField(verbose_name='发生时间')
    metadata = models.TextField(default='{}', verbose_name='元数据JSON')
    # ===== AI 升级新增字段 =====
    scene_type = models.CharField(max_length=50, default='', verbose_name='场景类型')  # welcome/intrusion/pet/elder
    ai_description = models.TextField(default='', verbose_name='AI分析文字')
    triggered_actions = models.JSONField(default=list, verbose_name='触发动作')
    snapshot_path = models.CharField(max_length=255, default='', verbose_name='截图路径')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    def __repr__(self):
        return self.event_type

    def __str__(self):
        return self.event_type

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(AlarmModel, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(AlarmModel, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'av_alarm'
        verbose_name = '报警'
        verbose_name_plural = '报警'
        indexes = [
            models.Index(fields=['-timestamp'], name='av_alarm_ts_idx'),
            models.Index(fields=['stream', 'timestamp'], name='av_alarm_st_idx'),
        ]


class RecordingModel(models.Model):
    """24/7 录像分段索引"""
    objects = ThreadSafetyManager()

    stream = models.ForeignKey(StreamModel, on_delete=models.CASCADE, verbose_name='摄像头')
    file_path = models.CharField(max_length=500, verbose_name='文件路径')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    duration = models.FloatField(default=0, verbose_name='时长(秒)')
    file_size = models.BigIntegerField(default=0, verbose_name='文件大小(字节)')
    has_motion = models.IntegerField(default=0, verbose_name='含运动')
    has_object = models.IntegerField(default=0, verbose_name='含目标')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    class Meta:
        db_table = 'av_recording'
        verbose_name = '录像分段'
        verbose_name_plural = '录像分段'
        indexes = [
            models.Index(fields=['stream', 'start_time'], name='av_recording_st_idx'),
        ]


class LLMModel(models.Model):
    """大模型配置（OpenAI 兼容 API）"""
    objects = ThreadSafetyManager()

    user_id = models.IntegerField(verbose_name='用户')
    sort = models.IntegerField(default=0, verbose_name='排序')
    code = models.CharField(max_length=50, verbose_name='编号')
    name = models.CharField(max_length=50, default='', verbose_name='名称')
    model_name = models.CharField(max_length=200, verbose_name='模型名称')
    api_url = models.CharField(max_length=500, verbose_name='API地址')
    api_key = models.CharField(max_length=200, default='', verbose_name='API密钥')
    timeout = models.IntegerField(default=30, verbose_name='超时时间(秒)')
    inference_tool = models.CharField(max_length=100, default='OpenAI', verbose_name='推理工具')
    remark = models.TextField(default='', verbose_name='备注')
    state = models.IntegerField(default=1, verbose_name='状态')  # 0=禁用 1=启用
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(LLMModel, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(LLMModel, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'av_llm'
        verbose_name = '大模型'
        verbose_name_plural = '大模型'


class LogModel(models.Model):
    """管理员操作日志"""
    objects = ThreadSafetyManager()

    user_id = models.IntegerField(verbose_name='用户ID')
    log_type = models.IntegerField(verbose_name='日志类型')  # 1:添加 2:编辑 3:删除 10:系统操作 100:系统重置
    content = models.CharField(max_length=200, verbose_name='日志内容')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    state = models.IntegerField(verbose_name='状态')  # 1:成功 0:失败

    def __repr__(self):
        return self.content

    def __str__(self):
        return self.content

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(LogModel, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(LogModel, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'av_log'
        verbose_name = '管理员日志'
        verbose_name_plural = '管理员日志'


# ===================== 脑中枢 / 语义理解 模型 =====================

class BrainEvent(models.Model):
    """脑中枢事件 — VLM 对单帧/单事件的语义理解结果"""
    objects = ThreadSafetyManager()

    camera_id = models.IntegerField(verbose_name='摄像头ID')
    timestamp = models.DateTimeField(verbose_name='事件发生时间')
    event_type = models.CharField(max_length=50, default='motion', verbose_name='事件类型')
    scene_description = models.TextField(default='', verbose_name='场景描述(VLM原始输出)')
    subject = models.CharField(max_length=100, default='', verbose_name='识别主体(人物/宠物/物品)')
    action = models.CharField(max_length=200, default='', verbose_name='主体行为')
    anomaly_score = models.FloatField(default=0.0, verbose_name='异常评分(0~1, 越高越可疑)')
    snapshot_path = models.CharField(max_length=500, default='', verbose_name='快照路径')
    video_clip_path = models.CharField(max_length=500, default='', verbose_name='视频片段路径')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    def __repr__(self):
        return f"BrainEvent#{self.id}"

    def __str__(self):
        return f"[{self.camera_id}] {self.subject} - {self.action}"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(BrainEvent, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(BrainEvent, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'brain_event'
        verbose_name = '脑中枢事件'
        verbose_name_plural = '脑中枢事件'
        indexes = [
            models.Index(fields=['camera_id', '-timestamp'], name='be_cam_ts_idx'),
            models.Index(fields=['-timestamp'], name='be_ts_idx'),
        ]


class BehaviorTrack(models.Model):
    """跨摄像头行为轨迹 — 同一个 track_id 对应多路摄像头的出现序列"""
    objects = ThreadSafetyManager()

    track_id = models.CharField(max_length=100, verbose_name='全局轨迹ID')
    camera_sequence = models.JSONField(default=list, verbose_name='出现摄像头序列')  # [{camera_id, timestamp}]
    start_time = models.DateTimeField(verbose_name='首次出现时间')
    end_time = models.DateTimeField(verbose_name='最后出现时间')
    total_duration = models.FloatField(default=0.0, verbose_name='总时长(秒)')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    def __repr__(self):
        return f"BehaviorTrack#{self.track_id}"

    def __str__(self):
        return f"track={self.track_id}"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(BehaviorTrack, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(BehaviorTrack, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'brain_behavior_track'
        verbose_name = '行为轨迹'
        verbose_name_plural = '行为轨迹'
        indexes = [
            models.Index(fields=['track_id'], name='bt_track_idx'),
        ]


class WeeklyReport(models.Model):
    """安全周报 — 每周汇总异常事件 / 行为统计"""
    objects = ThreadSafetyManager()

    week_start = models.DateField(verbose_name='周起始日(周一)')
    week_end = models.DateField(verbose_name='周结束日(周日)')
    summary = models.CharField(max_length=500, default='', verbose_name='简要摘要')
    anomaly_count = models.IntegerField(default=0, verbose_name='本周异常事件数')
    report_content = models.JSONField(default=dict, verbose_name='详细报告内容')  # LLM 生成的结构化内容
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __repr__(self):
        return f"WeeklyReport {self.week_start}~{self.week_end}"

    def __str__(self):
        return f"WeeklyReport {self.week_start}~{self.week_end}"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(WeeklyReport, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(WeeklyReport, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'brain_weekly_report'
        verbose_name = '安全周报'
        verbose_name_plural = '安全周报'
        indexes = [
            models.Index(fields=['-week_start'], name='wr_ws_idx'),
        ]


# ===================== 户外场景 模型 =====================

class OutdoorSceneConfig(models.Model):
    """户外场景配置 — 每路摄像头可配置触发哪些场景"""
    objects = ThreadSafetyManager()

    camera_id = models.IntegerField(verbose_name='摄像头ID')
    scene_type = models.CharField(max_length=50, verbose_name='场景类型')  # welcome/visitor/intrusion/delivery
    enabled = models.IntegerField(default=1, verbose_name='是否启用')  # 0=禁用 1=启用
    config = models.JSONField(default=dict, verbose_name='场景参数JSON')  # {ptz_preset, light_on, tts_text, ...}
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')

    def __repr__(self):
        return f"OutdoorSceneConfig#{self.id}"

    def __str__(self):
        return f"cam={self.camera_id} scene={self.scene_type}"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(OutdoorSceneConfig, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(OutdoorSceneConfig, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'outdoor_scene_config'
        verbose_name = '户外场景配置'
        verbose_name_plural = '户外场景配置'
        indexes = [
            models.Index(fields=['camera_id'], name='osc_cam_idx'),
        ]


class OutdoorEvent(models.Model):
    """户外场景事件 — 迎宾/访客/入侵等触发的事件记录"""
    objects = ThreadSafetyManager()

    camera_id = models.IntegerField(verbose_name='摄像头ID')
    event_type = models.CharField(max_length=50, verbose_name='事件类型')  # welcome/visitor/intrusion/delivery
    person_type = models.CharField(max_length=50, default='unknown', verbose_name='人员类型')  # family/visitor/stranger/delivery
    person_confidence = models.FloatField(default=0.0, verbose_name='人员识别置信度(0~1)')
    timestamp = models.DateTimeField(verbose_name='事件发生时间')
    snapshot_path = models.CharField(max_length=500, default='', verbose_name='快照路径')
    actions_taken = models.JSONField(default=list, verbose_name='已执行的动作')  # [{action, result}]
    notified = models.IntegerField(default=0, verbose_name='是否已通知')  # 0=未通知 1=已通知
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    def __repr__(self):
        return f"OutdoorEvent#{self.id}"

    def __str__(self):
        return f"[{self.camera_id}] {self.event_type} - {self.person_type}"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(OutdoorEvent, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(OutdoorEvent, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'outdoor_event'
        verbose_name = '户外事件'
        verbose_name_plural = '户外事件'
        indexes = [
            models.Index(fields=['camera_id', '-timestamp'], name='oe_cam_ts_idx'),
            models.Index(fields=['-timestamp'], name='oe_ts_idx'),
        ]


# ===================== 室内互动场景 模型 =====================

class IndoorSceneConfig(models.Model):
    """室内场景配置 — 每路摄像头可配置宠物/老人/儿童/夜间模式开关与参数"""
    objects = ThreadSafetyManager()

    camera_id = models.IntegerField(verbose_name='摄像头ID')
    scene_type = models.CharField(max_length=50, default='general', verbose_name='场景类型')  # general/pet/elder/child/night
    enabled = models.IntegerField(default=1, verbose_name='是否启用')  # 0=禁用 1=启用
    config = models.JSONField(default=dict, verbose_name='场景参数JSON')  # {pet_mode_enabled, night_start, sensitivity, ...}
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')

    def __repr__(self):
        return f"IndoorSceneConfig#{self.id}"

    def __str__(self):
        return f"cam={self.camera_id} scene={self.scene_type}"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(IndoorSceneConfig, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(IndoorSceneConfig, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'indoor_scene_config'
        verbose_name = '室内场景配置'
        verbose_name_plural = '室内场景配置'
        indexes = [
            models.Index(fields=['camera_id'], name='isc_cam_idx'),
        ]


class IndoorEvent(models.Model):
    """室内场景事件 — 宠物陪伴/老人看护/儿童看护/夜间模式触发的事件记录"""
    objects = ThreadSafetyManager()

    camera_id = models.IntegerField(verbose_name='摄像头ID')
    event_type = models.CharField(max_length=50, verbose_name='事件类型')  # pet_detected/fall/elder_stationary/danger_zone/night_wake/...
    scene_mode = models.CharField(max_length=50, default='', verbose_name='场景模式')  # pet/elder/child/night
    timestamp = models.DateTimeField(verbose_name='事件发生时间')
    snapshot_path = models.CharField(max_length=500, default='', verbose_name='快照路径')
    actions_taken = models.JSONField(default=list, verbose_name='已执行的动作')  # [{action, result}]
    notified = models.IntegerField(default=0, verbose_name='是否已通知')  # 0=未通知 1=已通知
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    def __repr__(self):
        return f"IndoorEvent#{self.id}"

    def __str__(self):
        return f"[{self.camera_id}] {self.event_type} ({self.scene_mode})"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(IndoorEvent, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(IndoorEvent, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'indoor_events'
        verbose_name = '室内事件'
        verbose_name_plural = '室内事件'
        indexes = [
            models.Index(fields=['camera_id', '-timestamp'], name='ie_cam_ts_idx'),
            models.Index(fields=['-timestamp'], name='ie2_ts_idx'),
        ]


# ===================== 无网场景 模型 =====================

class OfflineSceneConfig(models.Model):
    """无网场景配置 — 4G 摄像头的入侵/动物监测/低带宽/离线补传参数"""
    objects = ThreadSafetyManager()

    camera_id = models.IntegerField(verbose_name='摄像头ID')
    enabled = models.IntegerField(default=1, verbose_name='是否启用')  # 0=禁用 1=启用
    config = models.JSONField(default=dict, verbose_name='场景参数JSON')  # {intrusion_enabled, buffer_size_limit, ...}
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')

    def __repr__(self):
        return f"OfflineSceneConfig#{self.id}"

    def __str__(self):
        return f"cam={self.camera_id} offline-config"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(OfflineSceneConfig, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(OfflineSceneConfig, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'offline_scene_config'
        verbose_name = '无网场景配置'
        verbose_name_plural = '无网场景配置'
        indexes = [
            models.Index(fields=['camera_id'], name='ofsc_cam_idx'),
        ]


class OfflineEvent(models.Model):
    """无网场景事件 — 入侵/动物/补传事件，含视频路径与补传状态"""
    objects = ThreadSafetyManager()

    camera_id = models.IntegerField(verbose_name='摄像头ID')
    event_type = models.CharField(max_length=50, verbose_name='事件类型')  # intrusion/animal/keyframe/...
    timestamp = models.DateTimeField(verbose_name='事件发生时间')
    snapshot_path = models.CharField(max_length=500, default='', verbose_name='快照路径')
    video_path = models.CharField(max_length=500, default='', verbose_name='视频片段路径')
    is_replayed = models.IntegerField(default=0, verbose_name='是否已补传')  # 0=否 1=是
    replayed_at = models.DateTimeField(null=True, blank=True, verbose_name='补传时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    def __repr__(self):
        return f"OfflineEvent#{self.id}"

    def __str__(self):
        return f"[{self.camera_id}] {self.event_type}"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(OfflineEvent, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(OfflineEvent, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'offline_events'
        verbose_name = '无网事件'
        verbose_name_plural = '无网事件'
        indexes = [
            models.Index(fields=['camera_id', '-timestamp'], name='ofe_cam_ts_idx'),
            models.Index(fields=['-timestamp'], name='ofe_ts_idx'),
        ]


# ===================== 设备联动中枢 模型 =====================

class Device(models.Model):
    """注册设备 — NVR / 户外摄像头 / 室内摄像头 / 4G 摄像头"""
    objects = ThreadSafetyManager()

    TYPE_NVR = 'nvr'
    TYPE_OUTDOOR = 'outdoor'
    TYPE_INDOOR = 'indoor'
    TYPE_4G = '4g'
    TYPE_CHOICES = (
        (TYPE_NVR, 'NVR录像机'),
        (TYPE_OUTDOOR, '户外摄像头'),
        (TYPE_INDOOR, '室内摄像头'),
        (TYPE_4G, '4G摄像头'),
    )
    STATUS_ONLINE = 'online'
    STATUS_OFFLINE = 'offline'
    STATUS_CHOICES = (
        (STATUS_ONLINE, '在线'),
        (STATUS_OFFLINE, '离线'),
    )

    device_id = models.CharField(max_length=80, unique=True, verbose_name='设备编号')
    name = models.CharField(max_length=100, default='', verbose_name='设备名称')
    type = models.CharField(max_length=20, default=TYPE_OUTDOOR, choices=TYPE_CHOICES, verbose_name='设备类型')
    ip = models.CharField(max_length=50, default='', verbose_name='设备IP')
    status = models.CharField(max_length=20, default=STATUS_OFFLINE, choices=STATUS_CHOICES, verbose_name='在线状态')
    battery = models.IntegerField(default=-1, verbose_name='电量(%)')  # -1=有线设备/无电池
    firmware = models.CharField(max_length=50, default='', verbose_name='固件版本')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')

    def __repr__(self):
        return f"Device#{self.device_id}"

    def __str__(self):
        return f"{self.name or self.device_id}({self.status})"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(Device, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(Device, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'devices'
        verbose_name = '设备'
        verbose_name_plural = '设备'
        indexes = [
            models.Index(fields=['status'], name='dev_status_idx'),
        ]


class DeviceCommand(models.Model):
    """设备控制命令 — PTZ/灯光/音频等命令的状态留痕"""
    objects = ThreadSafetyManager()

    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = (
        (STATUS_PENDING, '待执行'),
        (STATUS_SUCCESS, '成功'),
        (STATUS_FAILED, '失败'),
    )

    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True,
                               db_column='device_id', verbose_name='目标设备')
    command_type = models.CharField(max_length=30, verbose_name='命令类型')  # ptz/light/audio/broadcast
    payload = models.JSONField(default=dict, verbose_name='命令载荷JSON')
    status = models.CharField(max_length=20, default=STATUS_PENDING, choices=STATUS_CHOICES, verbose_name='执行状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    executed_at = models.DateTimeField(null=True, blank=True, verbose_name='执行时间')

    def __repr__(self):
        return f"DeviceCommand#{self.id} {self.command_type}:{self.status}"

    def __str__(self):
        return f"{self.command_type} -> {self.status}"

    def delete(self, using=None, keep_parents=False):
        with g_dbLock:
            ret = super(DeviceCommand, self).delete(using=using, keep_parents=keep_parents)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with g_dbLock:
            ret = super(DeviceCommand, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        return ret

    class Meta:
        db_table = 'device_commands'
        verbose_name = '设备命令'
        verbose_name_plural = '设备命令'
        indexes = [
            models.Index(fields=['-created_at'], name='dc_created_idx'),
            models.Index(fields=['status'], name='dc_status_idx'),
        ]
