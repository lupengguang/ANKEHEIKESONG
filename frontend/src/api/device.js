// 设备联动中枢相关接口
import request from '../utils/request'

// 设备列表（可按 type/status 过滤）
export function listDevices(params) {
  return request.get('/devices', { params })
}

// 注册 / 更新设备
export function registerDevice(data) {
  return request.post('/devices/register', data)
}

// 命令历史（可按 device_id 过滤）
export function listCommands(params) {
  return request.get('/devices/commands', { params })
}

// 设备状态
export function getDeviceStatus(deviceId) {
  return request.get(`/devices/${deviceId}/status`)
}

// PTZ 控制：{ direction, angle }
export function controlPtz(deviceId, data) {
  return request.post(`/devices/${deviceId}/ptz`, data)
}

// 灯光控制：{ on_off, brightness }
export function controlLight(deviceId, data) {
  return request.post(`/devices/${deviceId}/light`, data)
}

// 播放音频：{ audio_url }
export function playAudio(deviceId, audioUrl) {
  return request.post(`/devices/${deviceId}/audio`, { audio_url: audioUrl })
}

// 跨摄像头联动：{ track_id, target_camera_id? }
export function crossCameraTrack(deviceId, data) {
  return request.post(`/devices/${deviceId}/cross-track`, data)
}
