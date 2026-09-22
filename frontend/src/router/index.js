import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import SceneConfig from '../views/SceneConfig.vue'
import AlertList from '../views/AlertList.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login },
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/scene', name: 'SceneConfig', component: SceneConfig, meta: { requiresAuth: true } },
  { path: '/alerts', name: 'AlertList', component: AlertList, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 登录守卫：未登录只允许进入登录页
router.beforeEach((to) => {
  const authed = !!localStorage.getItem('logged_in')
  if (to.meta.requiresAuth && !authed) {
    return { name: 'Login' }
  }
  if (to.name === 'Login' && authed) {
    return { name: 'Dashboard' }
  }
  return true
})

export default router
