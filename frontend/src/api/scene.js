// 场景配置接口
import request from '../utils/request'

// 获取四个场景（回家迎宾/老人看护/宠物陪伴/夜间入侵）的开关与灵敏度
export function getSceneConfig() {
  return request.get('/scene/config')
}

// 保存场景配置（支持单场景或批量）
export function saveSceneConfig(payload) {
  return request.put('/scene/config', payload)
}
