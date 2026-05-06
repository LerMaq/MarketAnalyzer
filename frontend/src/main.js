import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import auth from './auth'

// Проверяем авторизацию при загрузке приложения
auth.loadUser()

createApp(App).use(router).mount('#app')