// 室内场景相关接口
import request from '../utils/request'

// 查询室内配置（生效配置 + 各模式配置行）
export function getIndoorConfig(params) {
  return request.get('/indoor/config', { params })
}

// 更新室内配置（热更新，保存即生效）
export function updateIndoorConfig(data) {
  return request.put('/indoor/config', data)
}

// 测试宠物模式
export function testPet(data) {
  return request.post('/indoor/test-pet', data)
}

// 测试老人模式
export function testElder(data) {
  return request.post('/indoor/test-elder', data)
}

// 室内事件查询
export function getIndoorEvents(params) {
  return request.get('/indoor/events', { params })
}
