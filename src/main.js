import { createApp } from 'vue'
// import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { ElMessage } from 'element-plus'
import App from './App.vue'
import router from './router'
import store from './store'
require('@/assets/css/common.css')
require('@/assets/css/theme.css')
require('@/assets/css/themes.css')

const app = createApp(App)
app.use(router)
app.use(store)
// app.use(ElementPlus)

// Make store globally accessible for the input modal
window.GlobalStore = store

// Make ElMessage globally accessible for notifications
window.ElMessage = ElMessage

app.mount('#app')
