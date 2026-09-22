<!--
脑中枢 Vue 单文件组件参考
这是源码参考（仅供参考，不直接被 Django 使用）
如需独立前端工程，可配合 Vite + Vue 3 + Element Plus 使用
-->

<template>
  <div class="brain-page">
    <!-- 顶部工具栏 -->
    <div class="brain-toolbar">
      <div class="search-wrap">
        <el-input
          v-model="searchQuery"
          placeholder="用自然语言搜索事件，例如：昨天下午在门口徘徊的人"
          clearable
          size="default"
          @keyup.enter="doSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" :loading="searchLoading" @click="doSearch">
          <el-icon><Search /></el-icon> 搜索
        </el-button>
      </div>
      <div class="action-group">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          size="default"
        />
        <el-button @click="loadEvents">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button type="success" :loading="reportGenerating" @click="generateWeeklyReport">
          <el-icon><EditPen /></el-icon> 生成周报
        </el-button>
        <el-button type="warning" @click="showWeeklyReport = true">
          <el-icon><Document /></el-icon> 查看周报
        </el-button>
      </div>
    </div>

    <!-- 主体三栏布局 -->
    <div class="brain-body">
      <!-- 左侧：事件时间线 -->
      <div class="brain-panel">
        <div class="brain-panel-header">
          <el-icon><List /></el-icon>
          事件时间线
          <span style="margin-left:auto;font-size:12px;color:#9ca3af;">共 {{ events.length }} 条</span>
        </div>
        <div class="brain-panel-body">
          <div v-if="eventsLoading" class="empty-state">
            <el-icon class="is-loading"><Loading /></el-icon>
            <div>加载中...</div>
          </div>
          <div v-else-if="events.length === 0" class="empty-state">
            <el-icon><Warning /></el-icon>
            <div>暂无事件</div>
          </div>
          <div v-else class="event-timeline">
            <div
              v-for="evt in events"
              :key="evt.id"
              class="event-card"
              :class="{ active: selectedEvent && selectedEvent.id === evt.id }"
              @click="selectEvent(evt)"
            >
              <div class="event-time">{{ formatTime(evt.timestamp) }}</div>
              <div class="event-desc">{{ evt.scene_description || '无描述' }}</div>
              <div class="event-meta">
                <el-tag size="small" type="info">{{ evt.subject || '-' }}</el-tag>
                <el-tag size="small" type="primary">{{ evt.action || '-' }}</el-tag>
                <el-tag
                  size="small"
                  :type="isAnomaly(evt.anomaly_score) ? 'danger' : 'success'"
                  effect="dark"
                >
                  {{ isAnomaly(evt.anomaly_score) ? '异常' : '正常' }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：详情展示 -->
      <div class="brain-panel">
        <div class="brain-panel-header">
          <el-icon><Picture /></el-icon>
          事件详情
          <span v-if="selectedEvent" style="margin-left:auto;font-size:12px;color:#9ca3af;">
            #{{ selectedEvent.id }}
          </span>
        </div>
        <div class="brain-panel-body">
          <div v-if="!selectedEvent" class="empty-state">
            <el-icon><Pointer /></el-icon>
            <div>请从左侧选择一个事件</div>
          </div>
          <template v-else>
            <!-- 快照图 -->
            <div class="detail-snapshot">
              <img
                v-if="selectedEvent.snapshot_path"
                :src="'/static/' + selectedEvent.snapshot_path"
                alt="snapshot"
                @error="onImgError"
              />
              <div v-else class="no-img">暂无快照</div>
            </div>

            <!-- 视频片段 -->
            <div v-if="selectedEvent.video_clip_path" class="detail-video">
              <video
                :src="'/static/' + selectedEvent.video_clip_path"
                :poster="selectedEvent.snapshot_path ? '/static/' + selectedEvent.snapshot_path : ''"
                controls
                style="width:100%;border-radius:8px;"
              ></video>
            </div>

            <!-- 详细信息 -->
            <div class="detail-info">
              <div class="info-item">
                <div class="info-label">场景描述</div>
                <div class="info-value">{{ selectedEvent.scene_description || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">主题</div>
                <div class="info-value">{{ selectedEvent.subject || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">动作</div>
                <div class="info-value">{{ selectedEvent.action || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">摄像头 ID</div>
                <div class="info-value">{{ selectedEvent.camera_id || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">事件时间</div>
                <div class="info-value">{{ formatTime(selectedEvent.timestamp) }}</div>
              </div>
              <div
                class="info-item"
                :class="isAnomaly(selectedEvent.anomaly_score) ? 'anomaly' : 'normal'"
              >
                <div class="info-label">异常分数</div>
                <div class="info-value">
                  {{ selectedEvent.anomaly_score != null ? Number(selectedEvent.anomaly_score).toFixed(2) : '-' }}
                  <el-tag
                    v-if="selectedEvent.anomaly_score != null"
                    size="small"
                    :type="isAnomaly(selectedEvent.anomaly_score) ? 'danger' : 'success'"
                    effect="dark"
                    style="margin-left:6px;"
                  >
                    {{ isAnomaly(selectedEvent.anomaly_score) ? '异常' : '正常' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 右侧：跨摄像头轨迹 -->
      <div class="brain-panel">
        <div class="brain-panel-header">
          <el-icon><Connection /></el-icon>
          跨摄像头行为轨迹
        </div>
        <div class="brain-panel-body">
          <div v-if="!selectedEvent" class="empty-state">
            <el-icon><Pointer /></el-icon>
            <div>选择事件后查看轨迹</div>
          </div>
          <div v-else-if="trackLoading" class="empty-state">
            <el-icon class="is-loading"><Loading /></el-icon>
            <div>加载轨迹中...</div>
          </div>
          <div v-else-if="tracks.length === 0" class="empty-state">
            <el-icon><Warning /></el-icon>
            <div>未发现跨摄像头轨迹</div>
          </div>
          <div v-else class="track-timeline">
            <div v-for="(node, idx) in tracks" :key="idx" class="track-node">
              <div class="track-dot" :class="{ anomaly: node.is_anomaly }">
                {{ idx + 1 }}
              </div>
              <div class="track-content">
                <div class="track-camera">{{ node.camera_name || ('摄像头 #' + (node.camera_id || '-')) }}</div>
                <div class="track-time">{{ formatTime(node.timestamp) }}</div>
                <div class="track-action">{{ node.action || node.description || '-' }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 周报查看弹窗 -->
    <el-dialog v-model="showWeeklyReport" title="安全周报" width="700px" destroy-on-close>
      <div v-if="weeklyReportLoading" class="empty-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <div>加载周报中...</div>
      </div>
      <div v-else-if="!weeklyReport" class="empty-state">
        <el-icon><Warning /></el-icon>
        <div>暂无周报，请先生成</div>
      </div>
      <div v-else>
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px;">
          <el-descriptions-item label="周期">
            {{ weeklyReport.week_start }} 至 {{ weeklyReport.week_end }}
          </el-descriptions-item>
          <el-descriptions-item label="异常数量">
            <el-tag type="danger" effect="dark">{{ weeklyReport.anomaly_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="摘要" :span="2">
            {{ weeklyReport.summary }}
          </el-descriptions-item>
        </el-descriptions>
        <div class="weekly-report-content">
          {{ weeklyReport.report_content }}
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * BrainCenter —— 脑中枢页面 Vue 组件
 * 功能：
 *  - 自然语言搜索脑中枢事件
 *  - 事件时间线展示与详情查看
 *  - 跨摄像头行为轨迹展示
 *  - 安全周报生成与查看
 */
import { ref, reactive, onMounted, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Search, Refresh, EditPen, Document, List, Picture,
  Connection, Loading, Warning, Pointer,
} from '@element-plus/icons-vue';

// ==================== 工具函数 ====================

/** 格式化时间：ISO -> YYYY-MM-DD HH:mm:ss */
function formatTime(ts) {
  if (!ts) return '';
  let s = String(ts).replace('T', ' ').trim();
  s = s.replace(/\.\d+$/, '');
  if (s.length > 19) s = s.substring(0, 19);
  return s;
}

/** 判断异常：分数 >= 0.6 视为异常 */
function isAnomaly(score) {
  if (score == null) return false;
  return Number(score) >= 0.6;
}

/** 统一的 fetch 请求封装（已带 CSRF） */
async function apiFetch(url, options = {}) {
  try {
    const opts = {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    };
    const resp = await fetch(url, opts);
    const data = await resp.json();
    if (data && data.code === 1000) {
      return data.data;
    } else {
      ElMessage.error((data && data.msg) || '请求失败');
      return null;
    }
  } catch (e) {
    ElMessage.error('网络错误：' + e.message);
    return null;
  }
}

// ==================== 状态 ====================

const searchQuery = ref('');
const dateRange = ref([]);
const events = ref([]);
const eventsLoading = ref(false);
const searchLoading = ref(false);
const selectedEvent = ref(null);

const tracks = ref([]);
const trackLoading = ref(false);

const showWeeklyReport = ref(false);
const weeklyReport = ref(null);
const weeklyReportLoading = ref(false);
const reportGenerating = ref(false);

// ==================== 方法 ====================

/** 加载事件列表 */
async function loadEvents() {
  eventsLoading.value = true;
  const params = new URLSearchParams();
  if (dateRange.value && dateRange.value.length === 2) {
    params.append('start_time', dateRange.value[0]);
    params.append('end_time', dateRange.value[1]);
  }
  const data = await apiFetch('/api/brain/events?' + params.toString());
  events.value = Array.isArray(data) ? data : [];
  eventsLoading.value = false;
}

/** 自然语言搜索 */
async function doSearch() {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索内容');
    return;
  }
  searchLoading.value = true;
  const data = await apiFetch('/api/brain/search', {
    method: 'POST',
    body: JSON.stringify({ query: searchQuery.value.trim() }),
  });
  if (Array.isArray(data)) {
    events.value = data;
    ElMessage.success('搜索完成，共 ' + data.length + ' 条结果');
  } else if (data && Array.isArray(data.events)) {
    events.value = data.events;
    ElMessage.success('搜索完成，共 ' + data.events.length + ' 条结果');
  } else {
    events.value = [];
  }
  searchLoading.value = false;
}

/** 选择事件：触发轨迹查询 */
function selectEvent(evt) {
  selectedEvent.value = evt;
  tracks.value = [];
  if (evt && evt.id) {
    loadTracks(evt.id);
  }
}

/** 加载跨摄像头轨迹 */
async function loadTracks(trackId) {
  trackLoading.value = true;
  const data = await apiFetch('/api/brain/tracks?track_id=' + encodeURIComponent(trackId));
  if (data) {
    if (Array.isArray(data)) tracks.value = data;
    else if (Array.isArray(data.path)) tracks.value = data.path;
    else if (Array.isArray(data.tracks)) tracks.value = data.tracks;
    else tracks.value = [];
  }
  trackLoading.value = false;
}

/** 查看周报 */
async function loadWeeklyReport() {
  weeklyReportLoading.value = true;
  const data = await apiFetch('/api/brain/weekly-report');
  weeklyReport.value = data || null;
  weeklyReportLoading.value = false;
}

/** 生成周报 */
async function generateWeeklyReport() {
  try {
    await ElMessageBox.confirm('确认生成最新一周的安全周报？', '提示', {
      confirmButtonText: '生成',
      cancelButtonText: '取消',
      type: 'warning',
    });
  } catch (_) {
    return;
  }
  reportGenerating.value = true;
  const data = await apiFetch('/api/brain/generate-report', { method: 'POST' });
  reportGenerating.value = false;
  if (data) {
    ElMessage.success('周报生成成功');
    loadWeeklyReport();
    showWeeklyReport.value = true;
  }
}

/** 图片加载失败处理 */
function onImgError(e) {
  e.target.style.display = 'none';
}

// ==================== 监听 & 生命周期 ====================

watch(showWeeklyReport, (val) => {
  if (val) loadWeeklyReport();
});

onMounted(() => {
  loadEvents();
});
</script>

<style scoped>
.brain-page {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.brain-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 16px 20px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.brain-toolbar .search-wrap {
  flex: 1;
  min-width: 280px;
  display: flex;
  gap: 8px;
}

.brain-toolbar .search-wrap .el-input {
  max-width: 520px;
}

.brain-toolbar .action-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.brain-body {
  display: grid;
  grid-template-columns: 4fr 10fr 4fr;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.brain-panel {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.brain-panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.brain-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* 左侧事件时间线 */
.event-timeline {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.event-card {
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.event-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.event-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.event-card .event-time {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
  font-family: monospace;
}

.event-card .event-desc {
  font-size: 13px;
  color: #1f2937;
  line-height: 1.5;
  margin-bottom: 8px;
}

.event-card .event-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* 中间详情面板 */
.detail-snapshot {
  position: relative;
  background: #111;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  margin-bottom: 12px;
}

.detail-snapshot img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.detail-snapshot .no-img {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
  font-size: 14px;
}

.detail-video {
  margin-bottom: 12px;
}

.detail-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.detail-info .info-item {
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.detail-info .info-item.anomaly {
  border-left-color: #f56c6c;
}

.detail-info .info-item.normal {
  border-left-color: #67c23a;
}

.detail-info .info-label {
  font-size: 11px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.detail-info .info-value {
  font-size: 14px;
  color: #1f2937;
  font-weight: 500;
}

/* 右侧跨摄像头轨迹 */
.track-timeline {
  padding: 8px 0;
}

.track-node {
  display: flex;
  gap: 10px;
  padding-bottom: 16px;
  position: relative;
}

.track-node::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 24px;
  bottom: 0;
  width: 2px;
  background: #e5e7eb;
}

.track-node:last-child::before {
  display: none;
}

.track-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
}

.track-dot.anomaly {
  background: #f56c6c;
}

.track-content {
  flex: 1;
  min-width: 0;
}

.track-content .track-camera {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.track-content .track-time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.track-content .track-action {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.weekly-report-content {
  padding: 10px 0;
  line-height: 1.8;
  white-space: pre-wrap;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #9ca3af;
}

.empty-state .el-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

@media (max-width: 1200px) {
  .brain-body {
    grid-template-columns: 1fr;
  }
}
</style>
