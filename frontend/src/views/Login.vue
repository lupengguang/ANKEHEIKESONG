<template>
  <div class="login-wrap">
    <div class="login-card">
      <h1 class="login-title">{{ title }}</h1>
      <p class="login-sub">智能家庭安全看护平台</p>
      <form @submit.prevent="onSubmit">
        <div class="field">
          <label>账号</label>
          <input v-model="form.username" type="text" placeholder="请输入账号"
            autocomplete="username" />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="请输入密码"
            autocomplete="current-password" />
        </div>
        <button class="btn btn-primary login-btn" type="submit"
          :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>
      <p class="login-tip">默认账号：admin / admin888</p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api/auth'

const router = useRouter()
const title = import.meta.env.VITE_APP_TITLE || 'eufy AI HomeCare'
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin888' })

async function onSubmit() {
  if (!form.username || !form.password) return
  loading.value = true
  try {
    const res = await login(form.username, form.password)
    // 后端登录成功 code=1000
    if (res.code === 1000) {
      localStorage.setItem('logged_in', '1')
      router.push('/')
    }
  } catch (e) {
    // 错误提示由响应拦截器统一弹出
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f2e4d 0%, #1e4976 100%);
}
.login-card {
  width: 380px;
  background: #fff;
  border-radius: 12px;
  padding: 40px 36px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, .25);
}
.login-title { font-size: 24px; color: #0f2e4d; }
.login-sub { color: #64748b; font-size: 13px; margin: 6px 0 28px; }
.field { margin-bottom: 18px; }
.field label {
  display: block; font-size: 13px; color: #475569; margin-bottom: 6px;
}
.field input {
  width: 100%;
  height: 40px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0 12px;
  font-size: 14px;
  outline: none;
  transition: border-color .2s;
}
.field input:focus { border-color: #2563eb; }
.login-btn { width: 100%; height: 42px; margin-top: 6px; }
.login-btn:disabled { opacity: .6; cursor: not-allowed; }
.login-tip {
  margin-top: 18px; text-align: center;
  font-size: 12px; color: #94a3b8;
}
</style>
