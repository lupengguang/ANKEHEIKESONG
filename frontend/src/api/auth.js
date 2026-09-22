// 认证与系统级接口
import axios from 'axios'
import request from '../utils/request'

// VITE_API_BASE 形如 http://host:port/api → 去掉末尾 /api 得到站点根
const SITE_ORIGIN = String(import.meta.env.VITE_API_BASE || '')
  .replace(/\/api\/?$/, '')

// 健康检查
export function getHealth() {
  return request.get('/health')
}

// 获取 CSRF cookie：GET 登录页时 Django 会种下 csrftoken
export function fetchCsrfCookie() {
  return axios.get(`${SITE_ORIGIN}/login`, { withCredentials: true })
}

// 登录（后端 session 模式，返回 {code:1000,msg}）
export async function login(username, password) {
  await fetchCsrfCookie()
  return request.post(`${SITE_ORIGIN}/login`, { username, password })
}

// 退出登录（后端 GET /logout 后重定向，用裸 axios 跟随即可）
export async function logout() {
  try {
    await axios.get(`${SITE_ORIGIN}/logout`, { withCredentials: true })
  } catch (e) {
    // 忽略退出时的网络/重定向异常
  }
  localStorage.removeItem('logged_in')
  localStorage.removeItem('token')
}
