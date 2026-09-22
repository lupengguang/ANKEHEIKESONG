// 户外场景相关接口
import request from '../utils/request'

// 查询场景配置
export function getOutdoorConfig(params) {
  return request.get('/outdoor/config', { params })
}

// 更新场景配置（后端路由为 config-update）
export function updateOutdoorConfig(data) {
  return request.put('/outdoor/config-update', data)
}

// 触发迎宾场景
export function triggerWelcome(data) {
  return request.post('/outdoor/trigger-welcome', data)
}

// 触发入侵防御
export function triggerIntrusion(data) {
  return request.post('/outdoor/trigger-intrusion', data)
}

// 户外事件查询
export function getOutdoorEvents(params) {
  return request.get('/outdoor/events', { params })
}
