<template>
  <div class="alert-page">
    <div class="page-head">
      <h2 class="page-title">告警记录</h2>
      <div class="filters">
        <button v-for="f in filters" :key="f.value"
          class="filter-btn"
          :class="{ active: current === f.value }"
          @click="onFilter(f.value)">
          {{ f.label }}
        </button>
      </div>
    </div>

    <div v-if="alerts.length" class="timeline">
      <div v-for="a in alerts" :key="a.id" class="timeline-item">
        <div class="timeline-dot" :class="a.scene_type"></div>
        <div class="timeline-line"></div>

        <div class="alert-card">
          <div class="alert-head">
            <span class="scene-tag" :class="a.scene_type">
              {{ sceneLabel(a.scene_type) }}
            </span>
            <span class="alert-time">{{ fmtTime(a.timestamp) }}</span>
          </div>
          <div class="ai-desc">{{ a.ai_description || a.description }}</div>

          <div class="alert-foot">
            <img v-if="a.snapshot_url"
              :src="snapshotSrc(a.snapshot_url)"
              class="snapshot" alt="告警截图" />
            <div v-if="a.triggered_actions && a.triggered_actions.length"
              class="action-tags">
              <span v-for="(act, i) in a.triggered_actions" :key="i"
                class="action-tag">
                {{ actionLabel(act.action) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-box">
      <div class="empty-icon">📭</div>
      <div>{{ current ? '该场景下暂无告警记录' : '暂无告警记录' }}</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listAlerts } from '../api/alert'
import { SITE_ORIGIN } from '../api/camera'

const alerts = ref([])
const current = ref('')

const filters = [
  { value: '', label: '全部' },
  { value: 'welcome', label: '回家迎宾' },
  { value: 'elder', label: '老人看护' },
  { value: 'pet', label: '宠物陪伴' },
  { value: 'night', label: '夜间入侵' }
]

const SCENE_LABELS = {
  welcome: '回家迎宾', elder: '老人看护', pet: '宠物陪伴',
  night: '夜间入侵', intrusion: '区域入侵'
}
const ACTION_LABELS = { ptz: '云台转向', light: '灯光亮起', tts: '语音问候' }
const sceneLabel = (t) => SCENE_LABELS[t] || t || '告警'
const actionLabel = (t) => ACTION_LABELS[t] || t
const snapshotSrc = (u) => `${SITE_ORIGIN}${u}`
const fmtTime = (s) => {
  try { return new Date(s).toLocaleString('zh-CN') } catch { return s }
}

async function load() {
  const res = await listAlerts({
    limit: 50, ...(current.value ? { scene_type: current.value } : {})
  })
  alerts.value = res.data || []
}

function onFilter(v) {
  current.value = v
  load()
}

onMounted(load)
</script>

<style scoped>
.alert-page { padding: 20px 24px; max-width: 860px; margin: 0 auto; }
.page-head {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 12px; margin-bottom: 22px;
}
.page-title { font-size: 20px; }

.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.filter-btn {
  border: 1px solid #cbd5e1; background: #fff; color: #475569;
  border-radius: 16px; padding: 5px 14px; font-size: 13px; cursor: pointer;
}
.filter-btn.active {
  background: #2563eb; border-color: #2563eb; color: #fff;
}

/* 时间线 */
.timeline-item { position: relative; padding-left: 30px; }
.timeline-dot {
  position: absolute; left: 4px; top: 20px; width: 12px; height: 12px;
  border-radius: 50%; background: #2563eb; z-index: 1;
}
.timeline-dot.elder { background: #d97706; }
.timeline-dot.pet { background: #db2777; }
.timeline-dot.night, .timeline-dot.intrusion { background: #dc2626; }
.timeline-line {
  position: absolute; left: 9px; top: 32px; bottom: -20px; width: 2px;
  background: #e2e8f0;
}
.timeline-item:last-child .timeline-line { display: none; }

.alert-card {
  background: #fff; border-radius: 10px; padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .06); margin-bottom: 20px;
}
.alert-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.scene-tag {
  font-size: 12px; padding: 3px 10px; border-radius: 4px;
  background: #e0e7ff; color: #3730a3;
}
.scene-tag.elder { background: #fef3c7; color: #92400e; }
.scene-tag.pet { background: #fce7f3; color: #9d174d; }
.scene-tag.night, .scene-tag.intrusion { background: #fee2e2; color: #991b1b; }
.alert-time { font-size: 12px; color: #94a3b8; }

.ai-desc {
  font-size: 13.5px; color: #334155; line-height: 1.65;
}

.alert-foot {
  display: flex; gap: 14px; align-items: flex-end; margin-top: 12px;
  flex-wrap: wrap;
}
.snapshot {
  width: 160px; height: 100px; object-fit: cover; border-radius: 6px;
  border: 1px solid #e2e8f0; cursor: pointer;
}
.action-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.action-tag {
  font-size: 11px; background: #f1f5f9; color: #475569;
  padding: 3px 9px; border-radius: 4px;
}

.empty-box {
  text-align: center; color: #94a3b8; padding: 80px 0; font-size: 14px;
}
.empty-icon { font-size: 40px; margin-bottom: 12px; }
</style>
