// Axios 请求统一封装
// - baseURL 读取 VITE_API_BASE
// - 请求拦截：自动携带 token；非安全方法附带 Django CSRF token
// - 响应拦截：统一错误码处理（401 跳登录，500 弹错误提示）
// - 超时 10 秒
import axios from 'axios'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE, // 接口基址
  timeout: 10000,                        // 超时时间 10s
  withCredentials: true                  // 允许携带 cookie（session）
})

// ----------------------- 工具 -----------------------

function getCookie(name) {
  const match = document.cookie.match(
    new RegExp('(^|;\\s*)' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[2]) : ''
}

// 轻量错误提示（无需额外 UI 库）
function showToast(message) {
  let el = document.getElementById('app-toast')
  if (!el) {
    el = document.createElement('div')
    el.id = 'app-toast'
    el.style.cssText = [
      'position:fixed', 'top:72px', 'left:50%', 'transform:translateX(-50%)',
      'background:#dc2626', 'color:#fff', 'padding:10px 20px',
      'border-radius:6px', 'font-size:14px', 'z-index:9999',
      'box-shadow:0 4px 12px rgba(0,0,0,.15)', 'max-width:80vw'
    ].join(';')
    document.body.appendChild(el)
  }
  el.textContent = message
  clearTimeout(el._timer)
  el._timer = setTimeout(() => el.remove(), 3000)
}

function goLogin() {
  localStorage.removeItem('logged_in')
  // 避免在登录页重复跳转
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

// ----------------------- 请求拦截器 -----------------------

service.interceptors.request.use(
  (config) => {
    // 自动携带 token（如启用 token 鉴权）
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // Django session 模式：POST/PUT/PATCH/DELETE 需带 CSRF token
    const method = (config.method || 'get').toLowerCase()
    if (!['get', 'head', 'options'].includes(method)) {
      const csrf = getCookie('csrftoken')
      if (csrf) {
        config.headers['X-CSRFToken'] = csrf
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ----------------------- 响应拦截器 -----------------------

service.interceptors.response.use(
  (response) => {
    const res = response.data

    // 后端对未登录请求返回 302 并跳转到登录页，axios 跟随拿到 HTML：
    // 识别为会话失效，跳转登录
    if (typeof res === 'string') {
      if (res.includes('<!DOCTYPE html>') || res.includes('<html')) {
        goLogin()
        return Promise.reject(new Error('登录已失效，请重新登录'))
      }
      return res
    }

    // 统一业务码：200 / 1000（旧模块）均视为成功
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code === 200 || res.code === 1000) {
        return res
      }
      if (res.code === 401) {
        goLogin()
        return Promise.reject(new Error('未登录或登录已过期'))
      }
      const message = res.message || res.msg || '请求失败'
      showToast(message)
      return Promise.reject(new Error(message))
    }
    return res
  },
  (error) => {
    const status = error.response && error.response.status

    if (status === 401) {
      goLogin()
      showToast('未登录或登录已过期，请重新登录')
    } else if (status === 403) {
      showToast('没有访问权限（403）')
    } else if (status >= 500) {
      // 500 统一弹错误提示
      showToast(`服务器开小差了（${status}），请稍后重试`)
    } else if (error.code === 'ECONNABORTED') {
      showToast('请求超时，请检查网络后重试')
    } else if (!error.response) {
      showToast('网络异常，无法连接服务器')
    } else {
      const msg = (error.response.data &&
        (error.response.data.message || error.response.data.msg)) || error.message
      showToast(msg)
    }
    return Promise.reject(error)
  }
)

export default service
