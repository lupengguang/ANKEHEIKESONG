import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 页面标题读环境变量
document.title = import.meta.env.VITE_APP_TITLE || 'eufy AI HomeCare'

createApp(App).use(router).mount('#app')
