<template>
  <div class="auth-page fade-in">
    <h1>Регистрация</h1>
    <div class="field">
      <label>Имя</label>
      <input v-model="name" autocomplete="off" />
    </div>
    <div class="field">
      <label>Email</label>
      <input v-model="email" type="email" autocomplete="off" />
    </div>
    <div class="field">
      <label>Пароль</label>
      <div class="input-with-icon">
        <input v-model="password" :type="showRegPassword ? 'text' : 'password'" autocomplete="off" />
        <button type="button" class="eye-toggle" @click="showRegPassword = !showRegPassword">
          {{ showRegPassword ? '🙈' : '👁' }}
        </button>
      </div>
    </div>
    <div class="actions">
      <button @click="doRegister">Зарегистрироваться</button>
    </div>
    <p>Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import auth from '../auth'
import { useRouter } from 'vue-router'

const name = ref('')
const email = ref('')
const password = ref('')
const showRegPassword = ref(false)
const router = useRouter()

const doRegister = async () => {
  try {
    await auth.register(email.value, password.value, name.value)
    router.push('/profile')
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка регистрации')
  }
}
</script>

<style scoped>
.auth-page { max-width: 400px; margin: 40px auto; }
.field { display:flex; flex-direction:column; gap:6px; margin-bottom:12px }
.actions { margin:16px 0 }
input { padding:8px; border-radius:6px; border:1px solid #ddd }
button { padding:8px 12px; border-radius:6px; background:#005bff; color:white; border:none; cursor:pointer }

.input-with-icon { position: relative; }
.input-with-icon .eye-toggle { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1.2em; }
</style>
