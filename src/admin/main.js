/**
 * Admin Panel Entry Point
 * Separate Vue application for the admin panel (admin.pythonide-classroom.tech)
 */

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import { ElMessage, ElMessageBox } from 'element-plus'
import App from './App.vue'
import router from './router'
import store from './store'
import './assets/admin.css'

const app = createApp(App)
app.use(router)
app.use(store)
app.use(ElementPlus)

// Make ElMessage and ElMessageBox globally accessible
window.ElMessage = ElMessage
window.ElMessageBox = ElMessageBox

app.mount('#app')
