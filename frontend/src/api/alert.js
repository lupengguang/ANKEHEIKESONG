// 告警记录接口
import request from '../utils/request'

// 告警列表（可按场景类型筛选）
export function listAlerts(params) {
  return request.get('/alerts', { params })
}
