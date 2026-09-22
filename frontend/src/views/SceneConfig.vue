<template>
  <div class="scene-page">
    <div class="page-head">
      <h2 class="page-title">场景配置</h2>
      <button class="btn btn-primary" :disabled="saving" @click="onSaveAll">
        {{ saving ? '保存中...' : '保存全部' }}
      </button>
    </div>

    <div class="scene-grid">
      <section v-for="s in scenes" :key="s.scene_type"
        class="scene-card" :class="{ off: !s.enabled }">
        <div class="scene-icon">{{ iconOf(s.scene_type) }}</div>
        <div class="scene-name">{{ s.label }}</div>
        <div class="scene-desc">{{ descOf(s.scene_type) }}</div>

        <label class="toggle">
          <input type="checkbox" v-model="s.enabled" />
          <span class="toggle-track"></span>
          <span>{{ s.enabled ? '已启用' : '已关闭' }}</span>
        </label>

        <div class="sensitivity">
          <div class="sensitivity-head">
            <span>灵敏度</span>
            <b>{{ s.sensitivity }}</b>
          </div>
          <input type="range" min="1" max="10" v-model.number="s.sensitivity" />
        </div>

        <button class="btn btn-outline test-btn" @click="onTest(s)">
          测试
        </button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getSceneConfig, saveSceneConfig } from '../api/scene'

const scenes = ref([])
const saving = ref(false)

const ICONS = { welcome: '🏠', elder: '👴', pet: '🐾', night: '🌙' }
const DESCS = {
  welcome: '检测到家人靠近家门，自动转向、亮灯并语音问候',
  elder: '老人长时间未活动或异常姿态时及时提醒',
  pet: '识别宠物活动，记录宠物陪伴瞬间',
  night: '夜间识别异常靠近，及时告警并保留证据'
}
const iconOf = (t) => ICONS[t] || '✨'
const descOf = (t) => DESCS[t] || ''

async function load() {
  const res = await getSceneConfig()
  scenes.value = res.data || []
}

async function onSaveAll() {
  saving.value = true
  try {
    await saveSceneConfig({ scenes: scenes.value })
  } finally {
    saving.value = false
  }
}

// 单卡测试：保存该场景配置（迎宾场景下一次分析立即生效）
async function onTest(s) {
  await saveSceneConfig({
    scene_type: s.scene_type, enabled: s.enabled,
    sensitivity: s.sensitivity
  })
}

onMounted(load)
</script>

<style scoped>
.scene-page { padding: 20px 24px; max-width: 1100px; margin: 0 auto; }
.page-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.page-title { font-size: 20px; }

.scene-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px;
}
.scene-card {
  background: #fff; border-radius: 12px; padding: 22px 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .06);
  display: flex; flex-direction: column; align-items: flex-start;
  transition: opacity .2s;
}
.scene-card.off { opacity: .65; }
.scene-icon { font-size: 32px; margin-bottom: 10px; }
.scene-name { font-size: 16px; font-weight: 600; margin-bottom: 6px; }
.scene-desc {
  font-size: 12.5px; color: #64748b; line-height: 1.6;
  min-height: 58px;
}

.toggle {
  display: flex; align-items: center; gap: 8px; font-size: 13px;
  color: #475569; cursor: pointer; margin: 6px 0 14px;
}
.toggle input { display: none; }
.toggle-track {
  width: 38px; height: 21px; border-radius: 11px;
  background: #cbd5e1; position: relative; transition: background .2s;
}
.toggle-track::after {
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 17px; height: 17px; border-radius: 50%;
  background: #fff; transition: left .2s;
}
.toggle input:checked + .toggle-track { background: #2563eb; }
.toggle input:checked + .toggle-track::after { left: 19px; }

.sensitivity { width: 100%; margin-bottom: 14px; }
.sensitivity-head {
  display: flex; justify-content: space-between; font-size: 13px;
  color: #475569; margin-bottom: 6px;
}
.sensitivity input { width: 100%; }

.test-btn { width: 100%; }

@media (max-width: 1000px) {
  .scene-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
  .scene-grid { grid-template-columns: 1fr; }
}
</style>
