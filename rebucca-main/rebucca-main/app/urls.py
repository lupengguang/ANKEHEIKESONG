# 作者：北小菜
# 官网：https://www.yuturuishi.com
# 微信：bilibili_bxc
# 哔哩哔哩主页：https://space.bilibili.com/487906612
# gitee地址：https://gitee.com/Vanishi/rebucca
# github地址：https://github.com/beixiaocai/rebucca
from django.urls import path
from django.views.generic import RedirectView
from django.views.decorators.csrf import csrf_exempt
from .views import UserView
from .views import IndexView
from .views import SystemView
from .views import StreamView
from .views import InnerlView
from .views import NvrView
from .views import StorageView
from .views import VersionView
from .views import AnalysisView
from .views import AlgorithmView
from .views import SmallModelView
from .views import LLMView
from .views import AlarmView
from .views import ControlView
from . import brain_api
from . import outdoor_api
from . import indoor_api
from . import offline_api
from . import device_api
from . import health_api
from . import camera_api

app_name = 'app'

urlpatterns = [
    # 主页功能
    path('', IndexView.index),
    path('setup/index', RedirectView.as_view(url='/stream/index', permanent=False)),
    path('index/openIndex', IndexView.api_openIndex),
    path('index/openGpuInfo', IndexView.api_openGpuInfo),
    path('index/openMediaStatus', IndexView.api_openMediaStatus),
    path('index/openMediaControl', IndexView.api_openMediaControl),
    path('forbidden', IndexView.forbidden),
    path('index/openSwitchLang', IndexView.api_openSwitchLang),

    # 登陆退出
    path('user/openCaptcha', UserView.api_openCaptcha),
    path('login', UserView.login),
    path('logout', UserView.logout),

    # 用户管理
    path('user/index', UserView.index),
    path('user/openIndex', UserView.api_openIndex),
    path('user/openAdd', UserView.api_openAdd),
    path('user/openEdit', UserView.api_openEdit),
    path('user/openInfo', UserView.api_openInfo),
    path('user/openDel', UserView.api_openDel),

    # 视频流功能
    path('stream/online', StreamView.online),
    path('stream/index', StreamView.index),
    path('stream/openIndex', StreamView.api_openIndex),
    path('stream/openHandleAllStreamProxy', StreamView.api_openHandleAllStreamProxy),
    path('stream/openImportFile', StreamView.api_openImportFile),
    path('stream/openExportFile', StreamView.api_openExportFile),
    path('stream/openAddContext', StreamView.api_openAddContext),
    path('stream/openAdd', StreamView.api_openAdd),
    path('stream/openEditContext', StreamView.api_openEditContext),
    path('stream/openStreamByAppAndName', StreamView.api_openStreamByAppAndName),
    path('stream/openEdit', StreamView.api_openEdit),
    path('stream/openDel', StreamView.api_openDel),
    path('stream/openPtz', StreamView.api_openPtz),
    path('stream/openPlayer', StreamView.api_openPlayer),
    path('stream/player', StreamView.player),
    path('stream/openAddStreamProxy', StreamView.api_openAddStreamProxy),
    path('stream/openDelStreamProxy', StreamView.api_openDelStreamProxy),
    path('open/getAllStreamData', StreamView.api_openGetAllStreamData),
    path('open/getStatisticsStream', StreamView.api_openGetStatisticsStream),
    path('version/openCheckVersion', VersionView.api_openCheckVersion),
    path('version/index', VersionView.index),

    # 被内部模块调用接口（ZLMediaKit 回调，CSRF 豁免）
    path('inner/on_media_update_stream', csrf_exempt(InnerlView.api_on_media_update_stream)),
    path('inner/on_media_delete_stream', csrf_exempt(InnerlView.api_on_media_delete_stream)),
    path('inner/on_publish', csrf_exempt(InnerlView.api_on_publish)),
    path('inner/on_stream_not_found', csrf_exempt(InnerlView.api_on_stream_not_found)),

    # 系统功能
    path('system/config', SystemView.config),
    path('system/openConfig', SystemView.api_openConfig),
    path('system/openSaveSettings', SystemView.api_openSaveSettings),
    path('system/settings', RedirectView.as_view(url='/', permanent=False)),
    path('system/openExportLogs', SystemView.api_openExportLogs),

    # NVR/录像
    path('record/index', NvrView.record_index),
    path('nvr/openVideoIsRecording', NvrView.api_openVideoIsRecording),
    path('nvr/openStartRecordVideo', NvrView.api_openStartRecordVideo),
    path('nvr/openStopRecordVideo', NvrView.api_openStopRecordVideo),
    path('nvr/openSnapShot', NvrView.api_openSnapShot),
    path('nvr/openSnap', NvrView.api_openSnap),
    path('nvr/openRecordIndex', NvrView.api_openRecordIndex),
    path('nvr/openRecordFile', NvrView.api_openRecordFile),
    path('nvr/openRecordDel', NvrView.api_openRecordDel),

    path('stream/openOnvifDiscover', StreamView.api_openOnvifDiscover),

    # 存储 存根接口（原 Storage 模块已移除，保留路由以兼容前端模板）
    path('storage/openInfo', StorageView.api_openInfo),
    path('storage/openDownload', StorageView.api_openDownload),

    # 系统授权（已移除）

    # 布控管理
    path('control/index', ControlView.control_index),
    path('control/openIndex', ControlView.control_openIndex),
    path('control/openPageData', ControlView.control_openPageData),
    path('control/openAdd', ControlView.control_openAdd),
    path('control/openEdit', ControlView.control_openEdit),
    path('control/openDel', ControlView.control_openDel),
    path('control/openToggleZone', ControlView.control_openToggleZone),
    path('control/openRecentAlarms', ControlView.control_openRecentAlarms),
    path('zone/index', RedirectView.as_view(url='/control/index', permanent=False)),
    # 旧 /zone/* API 别名（POST 与带参 GET 不可仅用 RedirectView）
    path('zone/openIndex', ControlView.control_openIndex),
    path('zone/openPageData', ControlView.control_openPageData),
    path('zone/openAdd', ControlView.control_openAdd),
    path('zone/openEdit', ControlView.control_openEdit),
    path('zone/openDel', ControlView.control_openDel),
    path('zone/openRecentAlarms', ControlView.control_openRecentAlarms),

    # 报警管理
    path('alarm/index', AlarmView.index),
    path('alarm/dashboard', AlarmView.dashboard),
    path('alarm/openStats', AlarmView.api_openStats),
    path('alarm/openIndex', AnalysisView.alarm_openIndex),
    path('alarm/openDel', AnalysisView.alarm_openDel),
    path('alarm/openBatchDel', AnalysisView.alarm_openBatchDel),
    path('alarm/openClearAlarms', AnalysisView.alarm_openClearAlarms),

    path('analysis/openStatus', AnalysisView.analysis_openStatus),
    path('analysis/openStart', AnalysisView.analysis_openStart),
    path('analysis/openStop', AnalysisView.analysis_openStop),
    path('analysis/openReloadZones', AnalysisView.analysis_openReloadZones),
    path('analysis/openUpdateInferenceConfig', AnalysisView.analysis_openUpdateInferenceConfig),
    path('analysis/openToggleAlgoInstance', AnalysisView.analysis_openToggleAlgoInstance),
    path('analysis/openRestartAlgoInstance', AnalysisView.analysis_openRestartAlgoInstance),
    path('analysis/openRestartInferencePool', AnalysisView.analysis_openRestartInferencePool),

    # 小模型管理（原算法模型 CRUD）
    path('smallmodel/index', SmallModelView.smallmodel_index),
    path('smallmodel/test', SmallModelView.smallmodel_test),
    path('smallmodel/openIndex', SmallModelView.smallmodel_openIndex),
    path('smallmodel/openDetail', SmallModelView.smallmodel_openDetail),
    path('smallmodel/openTestStart', SmallModelView.smallmodel_openTestStart),
    path('smallmodel/openTestStatus', SmallModelView.smallmodel_openTestStatus),
    path('smallmodel/openTestOutput', SmallModelView.smallmodel_openTestOutput),
    path('smallmodel/openTestClearTemp', SmallModelView.smallmodel_openTestClearTemp),
    path('smallmodel/openAdd', SmallModelView.smallmodel_openAdd),
    path('smallmodel/openEdit', SmallModelView.smallmodel_openEdit),
    path('smallmodel/openDel', SmallModelView.smallmodel_openDel),
    path('smallmodel/openUploadModel', SmallModelView.smallmodel_openUploadModel),
    path('smallmodel/openProbe', SmallModelView.smallmodel_openProbe),
    path('smallmodel/openEngines', SmallModelView.smallmodel_openEngines),
    path('smallmodel/openDetectors', SmallModelView.smallmodel_openDetectors),
    path('smallmodel/openSetActive', SmallModelView.smallmodel_openSetActive),
    path('smallmodel/openAssignStreams', SmallModelView.smallmodel_openAssignStreams),

    # 算法管理（业务逻辑：小模型/大模型 + 后处理）
    path('algorithm/index', AlgorithmView.algorithm_index),
    path('algorithm/openIndex', AlgorithmView.algorithm_openIndex),
    path('algorithm/openCheckModels', AlgorithmView.algorithm_openCheckModels),
    path('algorithm/openOptions', AlgorithmView.algorithm_openOptions),
    path('algorithm/openAdd', AlgorithmView.algorithm_openAdd),
    path('algorithm/openEdit', AlgorithmView.algorithm_openEdit),
    path('algorithm/openDel', AlgorithmView.algorithm_openDel),
    path('algorithm/openAssignContext', AlgorithmView.algorithm_openAssignContext),
    path('algorithm/openAssignZones', AlgorithmView.algorithm_openAssignZones),

    # 大模型管理
    path('llm/index', LLMView.index),
    path('llm/test', LLMView.test),
    path('llm/openIndex', LLMView.api_openIndex),
    path('llm/openAdd', LLMView.api_openAdd),
    path('llm/openEdit', LLMView.api_openEdit),
    path('llm/openInfo', LLMView.api_openInfo),
    path('llm/openDel', LLMView.api_openDel),
    path('llm/openTest', csrf_exempt(LLMView.api_openTest)),

    # ===== 中枢大脑升级 =====
    path('ai-upgrade', brain_api.ai_upgrade_page),
    path('api/brain/events', brain_api.brain_events),
    path('api/brain/tracks', brain_api.brain_tracks),
    path('api/brain/search', csrf_exempt(brain_api.brain_search)),
    path('api/brain/weekly-report', brain_api.brain_weekly_report),
    path('api/brain/generate-report', csrf_exempt(brain_api.brain_generate_report)),
    path('brain/page', brain_api.brain_page),

    # ===== 户外入口升级 =====
    path('api/outdoor/config', outdoor_api.outdoor_config),
    path('api/outdoor/config-update', csrf_exempt(outdoor_api.outdoor_config_update)),
    path('api/outdoor/trigger-welcome', csrf_exempt(outdoor_api.outdoor_trigger_welcome)),
    path('api/outdoor/trigger-intrusion', csrf_exempt(outdoor_api.outdoor_trigger_intrusion)),
    path('api/outdoor/events', outdoor_api.outdoor_events),
    path('outdoor/page', outdoor_api.outdoor_page),

    # ===== 室内互动升级 =====
    path('api/indoor/config', csrf_exempt(indoor_api.indoor_config_dispatch)),
    path('api/indoor/test-pet', csrf_exempt(indoor_api.indoor_test_pet)),
    path('api/indoor/test-elder', csrf_exempt(indoor_api.indoor_test_elder)),
    path('api/indoor/events', indoor_api.indoor_events),

    # ===== 无网场景升级 =====
    path('api/offline/config', csrf_exempt(offline_api.offline_config_dispatch)),
    path('api/offline/test-intrusion', csrf_exempt(offline_api.offline_test_intrusion)),
    path('api/offline/events', offline_api.offline_events),
    path('api/offline/stats', offline_api.offline_stats),
    path('api/offline/replay', csrf_exempt(offline_api.offline_replay)),

    # ===== 设备联动中枢 =====（字面量路由必须在 <device_id> 参数路由之前）
    path('api/devices', device_api.devices_list),
    path('api/devices/register', csrf_exempt(device_api.device_register)),
    path('api/devices/commands', device_api.commands_list),
    path('api/devices/<str:device_id>/status', device_api.device_status),
    path('api/devices/<str:device_id>/ptz', csrf_exempt(device_api.device_ptz)),
    path('api/devices/<str:device_id>/light', csrf_exempt(device_api.device_light)),
    path('api/devices/<str:device_id>/audio', csrf_exempt(device_api.device_audio)),
    path('api/devices/<str:device_id>/cross-track', csrf_exempt(device_api.device_cross_track)),

    # ===== 健康检查与接口文档 =====
    path('api/health', health_api.health),
    path('openapi.json', health_api.openapi_json),
    path('docs', health_api.swagger_docs),
    path('redoc', health_api.redoc_docs),

    # ===== 本地摄像头 + VLM 迎宾闭环 =====
    path('api/video/stream', camera_api.video_stream),
    path('api/camera/status', camera_api.camera_status),
    path('api/camera/start', csrf_exempt(camera_api.camera_start)),
    path('api/camera/stop', csrf_exempt(camera_api.camera_stop)),
    path('api/camera/ptz', csrf_exempt(camera_api.camera_ptz)),
    path('api/alerts', camera_api.alerts_list),
    path('api/scene/config', csrf_exempt(camera_api.scene_config_dispatch)),
    path('api/events/stream', camera_api.events_stream),
]

