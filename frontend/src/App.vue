<template>
  <div class="app">
    <header v-if="isAuthed" class="app-header">
      <div class="app-title">{{ title }}</div>
      <nav class="app-nav">
        <router-link to="/" class="nav-link">实时监控</router-link>
        <router-link to="/scene" class="nav-link">场景配置</router-link>
        <router-link to="/alerts" class="nav-link">告警记录</router-link>
      </nav>
      <button class="btn btn-ghost" @click="onLogout">退出登录</button>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { logout } from './api/auth'

const route = useRoute()
const router = useRouter()
const title = import.meta.env.VITE_APP_TITLE || 'eufy AI HomeCare'
const isAuthed = computed(() => !!localStorage.getItem('logged_in'))

async function onLogout() {
  await logout()
  router.push('/login')
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  background: #f5f7fa;
  color: #1f2937;
}
.app-header {
  height: 56px;
  padding: 0 24px;
  background: #0f2e4d;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.app-title { font-size: 18px; font-weight: 600; }
.app-nav { display: flex; gap: 22px; }
.nav-link {
  color: #cbd5e1; text-decoration: none; font-size: 14px;
  padding: 4px 2px; border-bottom: 2px solid transparent;
}
.nav-link:hover { color: #fff; }
.nav-link.router-link-active {
  color: #fff; border-bottom-color: #60a5fa;
}
.app-main { min-height: calc(100vh - 56px); }
.btn {
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
}
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:hover { background: #1d4ed8; }
.btn-danger { background: #dc2626; color: #fff; }
.btn-danger:hover { background: #b91c1c; }
.btn-outline {
  background: #fff; color: #2563eb; border: 1px solid #93c5fd;
}
.btn-outline:hover { background: #eff6ff; }
.btn-ghost { background: transparent; color: #cbd5e1; border: 1px solid #475569; }
.btn-ghost:hover { color: #fff; border-color: #94a3b8; }
</style>
