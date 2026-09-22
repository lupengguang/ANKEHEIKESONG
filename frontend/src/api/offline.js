// 无网场景相关接口
import request from '../utils/request'

// 查询无网配置
export function getOfflineConfig(params) {
  return request.get('/offline/config', { params })
}

// 更新无网配置（热更新，保存即生效）
export function updateOfflineConfig(data) {
  return request.put('/offline/config', data)
}

// 测试入侵防御
export function testIntrusion(data) {
  return request.post('/offline/test-intrusion', data)
}

// 无网事件查询
export function getOfflineEvents(params) {
  return request.get('/offline/events', { params })
}

// 流量与补传统计
export function getOfflineStats(params) {
  return request.get('/offline/stats', { params })
}

// 手动触发离线补传
export function replayOffline(data) {
  return request.post('/offline/replay', data || {})
}
