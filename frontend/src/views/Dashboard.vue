<template>
  <div class="monitor">
    <!-- 顶部：标题 + 启动/停止 + 灯光开关 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <h2 class="page-title">实时监控</h2>
        <span class="state-chip" :class="running ? 'on' : 'off'">
          {{ running ? '运行中' : '待机' }}
        </span>
      </div>
      <div class="toolbar-right">
        <label class="light-switch">
          <input type="checkbox" v-model="lightOn" />
          <span class="switch-track"><span class="switch-thumb"></span></span>
          <span class="light-label">模拟灯光 {{ lightOn ? '开' : '关' }}</span>
        </label>
        <button v-if="!running" class="btn btn-primary"
          :disabled="busy" @click="onStart">
          {{ busy ? '启动中...' : '启动摄像头' }}
        </button>
        <button v-else class="btn btn-danger" :disabled="busy" @click="onStop">
          停止摄像头
        </button>
      </div>
    </div>

    <!-- 主区域：左画面 / 右状态与告警 -->
    <div class="main-grid">
      <section class="video-card">
        <img :src="videoSrc" alt="实时画面"
          @error="onImgError" />
      </section>

      <aside class="side">
        <section class="card">
          <div class="card-title">当前场景状态</div>
          <div class="status-list">
            <div class="status-row">
              <span>引擎状态</span>
              <b :class="running ? 'text-green' : 'text-gray'">
                {{ running ? '运行中' : '待机' }}
              </b>
            </div>
            <div class="status-row">
              <span>分辨率</span>
              <b>{{ status.width }} × {{ status.height }}</b>
            </div>
            <div class="status-row">
              <span>已处理帧数</span>
              <b>{{ status.frame_count }}</b>
            </div>
            <div class="status-row">
              <span>迎宾触发次数</span>
              <b class="text-green">{{ status.trigger_count }}</b>
            </div>
            <div v-if="status.last_error" class="status-error">
              {{ status.last_error }}
            </div>
          </div>
        </section>

        <section class="card">
          <div class="card-title">
            最新告警
            <span class="card-link" @click="$router.push('/alerts')">
              查看全部
            </span>
          </div>
          <div v-if="latestAlerts.length" class="alert-mini-list">
            <div v-for="a in latestAlerts" :key="a.id" class="alert-mini">
              <span class="scene-tag" :class="a.scene_type">
                {{ sceneLabel(a.scene_type) }}
              </span>
              <div class="alert-mini-body">
                <div class="alert-mini-desc">
                  {{ a.ai_description || a.description }}
                </div>
                <div class="alert-mini-time">{{ fmtTime(a.timestamp) }}</div>
              </div>
            </div>
          </div>
          <div v-else class="empty">暂无告警，人员靠近摄像头后将自动迎宾</div>
        </section>
      </aside>
    </div>

    <!-- 底部：PTZ 十字控制 -->
    <section class="card ptz-card">
      <div class="card-title">PTZ 云台控制（模拟）</div>
      <div class="ptz-pad">
        <button class="ptz-btn" @click="onPtz('up')">▲</button>
        <div class="ptz-mid">
          <button class="ptz-btn" @click="onPtz('left')">◀</button>
          <button class="ptz-btn ptz-center" @click="onPtz('center')">居中</button>
          <button class="ptz-btn" @click="onPtz('right')">▶</button>
        </div>
        <button class="ptz-btn" @click="onPtz('down')">▼</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import {
  streamUrl, eventsUrl, getCameraStatus, startCamera, stopCamera, ptzControl
} from '../api/camera'
import { listAlerts } from '../api/alert'

const running = ref(false)
const busy = ref(false)
const lightOn = ref(false)
const videoSrc = ref(`${streamUrl}?t=${Date.now()}`)
const latestAlerts = ref([])
const status = reactive({
  width: 0, height: 0, frame_count: 0, trigger_count: 0, last_error: ''
})

let eventSource = null
let statusTimer = null

const SCENE_LABELS = {
  welcome: '迎宾', elder: '老人', pet: '宠物', night: '夜间', intrusion: '入侵'
}
const sceneLabel = (t) => SCENE_LABELS[t] || t || '告警'
const fmtTime = (s) => {
  try { return new Date(s).toLocaleString('zh-CN') } catch { return s }
}

async function refreshStatus() {
  try {
    const res = await getCameraStatus()
    Object.assign(status, res.data)
    running.value = res.data.running
  } catch (e) {
    // 错误提示由拦截器处理
  }
}

async function refreshAlerts() {
  try {
    const res = await listAlerts({ limit: 5 })
    latestAlerts.value = res.data || []
  } catch (e) {
    // 忽略
  }
}

async function onStart() {
  busy.value = true
  try {
    const res = await startCamera()
    if (res.code === 200) {
      running.value = true
      // 重启流连接，避免浏览器缓存旧连接
      videoSrc.value = `${streamUrl}?t=${Date.now()}`
    }
  } finally {
    busy.value = false
  }
}

async function onStop() {
  busy.value = true
  try {
    await stopCamera()
    running.value = false
    await refreshStatus()
  } finally {
    busy.value = false
  }
}

async function onPtz(direction) {
  await ptzControl(direction)
}

function onImgError() {
  // 占位画面也由后端持续输出；真异常时稍后自动重连
  setTimeout(() => {
    videoSrc.value = `${streamUrl}?t=${Date.now()}`
  }, 2000)
}

// SSE：服务端实时推送告警
function connectSSE() {
  eventSource = new EventSource(eventsUrl, { withCredentials: true })
  eventSource.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data)
      if (data.type === 'welcome_alert') {
        refreshAlerts()
        refreshStatus()
      }
    } catch (e) {
      // 忽略心跳等非 JSON
    }
  }
  eventSource.onerror = () => {
    // 浏览器会自动重连，无需处理
  }
}

onMounted(() => {
  refreshStatus()
  refreshAlerts()
  connectSSE()
  // 兜底：每 3 秒轮询一次状态（SSE 正常时数据也是最新的）
  statusTimer = setInterval(refreshStatus, 3000)
})

onBeforeUnmount(() => {
  if (eventSource) eventSource.close()
  if (statusTimer) clearInterval(statusTimer)
})
</script>

<style scoped>
.monitor { padding: 20px 24px; max-width: 1200px; margin: 0 auto; }

/* 工具栏 */
.toolbar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 18px;
}
.toolbar-left { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 20px; }
.state-chip {
  font-size: 12px; padding: 3px 10px; border-radius: 12px;
}
.state-chip.on { background: #dcfce7; color: #15803d; }
.state-chip.off { background: #e5e7eb; color: #6b7280; }
.toolbar-right { display: flex; align-items: center; gap: 16px; }

/* 灯光开关 */
.light-switch { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.light-switch input { display: none; }
.switch-track {
  width: 40px; height: 22px; border-radius: 11px;
  background: #cbd5e1; position: relative; transition: background .2s;
}
.switch-thumb {
  position: absolute; top: 2px; left: 2px; width: 18px; height: 18px;
  border-radius: 50%; background: #fff; transition: left .2s;
}
.light-switch input:checked + .switch-track { background: #f59e0b; }
.light-switch input:checked + .switch-track .switch-thumb { left: 20px; }
.light-label { font-size: 13px; color: #475569; }

/* 主区域 */
.main-grid {
  display: grid; grid-template-columns: 1.6fr 1fr; gap: 18px;
}
.video-card {
  background: #0b1220; border-radius: 10px; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  min-height: 360px;
}
.video-card img { width: 100%; display: block; }

.side { display: flex; flex-direction: column; gap: 18px; }
.card {
  background: #fff; border-radius: 10px; padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .06);
}
.card-title {
  font-size: 15px; font-weight: 600; margin-bottom: 14px;
  display: flex; justify-content: space-between; align-items: center;
}
.card-link { font-size: 12px; color: #2563eb; cursor: pointer; font-weight: 400; }

.status-row {
  display: flex; justify-content: space-between; font-size: 13px;
  padding: 7px 0; border-bottom: 1px solid #f1f5f9;
}
.text-green { color: #16a34a; }
.text-gray { color: #9ca3af; }
.status-error {
  margin-top: 10px; font-size: 12px; color: #dc2626;
}

.alert-mini { display: flex; gap: 10px; padding: 8px 0; }
.alert-mini + .alert-mini { border-top: 1px solid #f1f5f9; }
.scene-tag {
  flex-shrink: 0; font-size: 11px; height: 22px; line-height: 22px;
  padding: 0 8px; border-radius: 4px; background: #e0e7ff; color: #3730a3;
}
.scene-tag.elder { background: #fef3c7; color: #92400e; }
.scene-tag.pet { background: #fce7f3; color: #9d174d; }
.scene-tag.night, .scene-tag.intrusion { background: #fee2e2; color: #991b1b; }
.alert-mini-desc {
  font-size: 12.5px; color: #334155; line-height: 1.5;
}
.alert-mini-time { font-size: 11px; color: #94a3b8; margin-top: 3px; }
.empty { font-size: 13px; color: #94a3b8; padding: 12px 0; }

/* PTZ */
.ptz-card { margin-top: 18px; }
.ptz-pad {
  width: 190px; margin: 0 auto; text-align: center;
}
.ptz-mid { display: flex; justify-content: space-between; margin: 6px 0; }
.ptz-btn {
  width: 56px; height: 44px; border: 1px solid #cbd5e1; border-radius: 8px;
  background: #f8fafc; cursor: pointer; font-size: 15px; color: #334155;
  transition: all .15s;
}
.ptz-btn:hover { background: #2563eb; color: #fff; border-color: #2563eb; }
.ptz-center { font-size: 13px; }

@media (max-width: 900px) {
  .main-grid { grid-template-columns: 1fr; }
}
</style>
