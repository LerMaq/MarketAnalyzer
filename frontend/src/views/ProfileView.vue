<template>
  <div class="profile-page">
    <h2>Профиль</h2>

    <section class="card">
      <h3>Основные данные</h3>
      <div class="field">
        <label>Имя</label>
        <input v-model="name" />
      </div>
      <div class="actions">
        <button @click="updateName">Сохранить имя</button>
      </div>
    </section>

    <section class="card">
      <h3>Смена пароля</h3>
      <div class="field">
        <label>Старый пароль</label>
        <input type="password" v-model="oldPassword" />
      </div>
      <div class="field">
        <label>Новый пароль</label>
        <input type="password" v-model="newPassword" />
      </div>
      <div class="actions">
        <button @click="changePassword">Сменить пароль</button>
      </div>
    </section>

    <section class="card">
      <button @click="logout" class="logout-btn">Выйти</button>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import auth from '../auth'
import { useRouter } from 'vue-router'

const name = ref('')
const oldPassword = ref('')
const newPassword = ref('')

const loadProfile = async () => {
  try {
    const res = await api.get('/user/me')
    name.value = res.data.name || ''
  } catch (e) {
    console.error('Ошибка загрузки профиля', e)
  }
}

const updateName = async () => {
  try {
    const res = await api.put('/user/me', { name: name.value })
    name.value = res.data.name
    alert('Имя обновлено')
  } catch (e) {
    console.error('Ошибка сохранения имени', e)
    alert('Не удалось сохранить имя')
  }
}

const changePassword = async () => {
  try {
    await api.put('/user/me/password', { old_password: oldPassword.value, new_password: newPassword.value })
    oldPassword.value = ''
    newPassword.value = ''
    alert('Пароль успешно изменён')
  } catch (e) {
    console.error('Ошибка смены пароля', e)
    alert(e.response?.data?.detail || 'Ошибка при смене пароля')
  }
}

onMounted(loadProfile)

const router = useRouter()

const logout = async () => {
  await auth.logout()
  router.push('/')
}
</script>

<style scoped>
.profile-page { max-width: 700px; margin: 20px auto; }
.card { background: white; padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #eee }
.field { display:flex; flex-direction:column; gap:6px; margin-bottom:8px }
.actions { margin-top: 8px }
input { padding:8px; border-radius:6px; border:1px solid #ddd }
button { padding:8px 12px; border-radius:6px; background:#005bff; color:white; border:none }
.logout-btn { background:#f00; }
</style>
