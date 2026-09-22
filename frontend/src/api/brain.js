// 中枢大脑相关接口
import request from '../utils/request'

// 事件查询（camera_id/start_time/end_time/limit）
export function getBrainEvents(params) {
  return request.get('/brain/events', { params })
}

// 跨摄像头行为轨迹（track_id 必填）
export function getBrainTracks(params) {
  return request.get('/brain/tracks', { params })
}

// 自然语言搜索事件
export function searchBrainEvents(data) {
  return request.post('/brain/search', data)
}

// 周报数据
export function getWeeklyReport(params) {
  return request.get('/brain/weekly-report', { params })
}

// 生成报告
export function generateReport(data) {
  return request.post('/brain/generate-report', data || {})
}
