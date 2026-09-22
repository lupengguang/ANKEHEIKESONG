// 本地摄像头控制接口
import request from '../utils/request'

// MJPEG / SSE 为长连接，取后端站点 origin，避免开发代理缓冲
export const SITE_ORIGIN = String(import.meta.env.VITE_API_BASE || '')
  .replace(/\/api\/?$/, '')

// MJPEG 实时画面地址
export const streamUrl = `${SITE_ORIGIN}/api/video/stream`
// SSE 实时事件地址
export const eventsUrl = `${SITE_ORIGIN}/api/events/stream`

// 摄像头状态
export function getCameraStatus() {
  return request.get('/camera/status')
}

// 启动摄像头 + 迎宾引擎
export function startCamera(cameraIndex) {
  return request.post('/camera/start',
    cameraIndex !== undefined ? { camera_index: cameraIndex } : {})
}

// 停止
export function stopCamera() {
  return request.post('/camera/stop')
}

// 模拟 PTZ：direction = up/down/left/right/center
export function ptzControl(direction) {
  return request.post('/camera/ptz', { direction })
}
