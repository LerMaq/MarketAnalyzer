<template>
  <div class="auth-page">
    <h1>Вход в систему</h1>
    <div class="field">
      <label>Email</label>
      <input v-model="email" type="email" autocomplete="email" />
    </div>
    <div class="field">
      <label>Пароль</label>
      <input v-model="password" type="password" autocomplete="current-password" />
    </div>
    <div class="actions">
      <button @click="doLogin">Войти</button>
    </div>
    <p>Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link></p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import auth from '../auth'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const router = useRouter()

const doLogin = async () => {
  try {
    await auth.login(email.value, password.value)
    router.push('/profile')
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка входа')
  }
}
</script>

<style scoped>
.auth-page { max-width: 400px; margin: 40px auto; }
.field { display:flex; flex-direction:column; gap:6px; margin-bottom:12px }
.actions { margin:16px 0 }
input { padding:8px; border-radius:6px; border:1px solid #ddd }
button { padding:8px 12px; border-radius:6px; background:#005bff; color:white; border:none; cursor:pointer }
</style>