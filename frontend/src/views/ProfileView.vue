<template>
  <div class="profile-page">
    <h2>Профиль</h2>

    <section class="card">
      <h3>Основные данные</h3>
      <div class="field">
        <label>Имя</label>
        <input v-model="name" autocomplete="off" />
      </div>
      <div class="actions">
        <button @click="updateName">Сохранить имя</button>
      </div>
    </section>

    <section class="card">
      <h3>Смена пароля</h3>
      <div class="field">
        <label>Старый пароль</label>
        <div class="input-with-icon">
          <input :type="showOldPassword ? 'text' : 'password'" v-model="oldPassword" autocomplete="off" />
          <button type="button" class="eye-toggle" @click="showOldPassword = !showOldPassword">
            {{ showOldPassword ? '🙈' : '👁' }}
          </button>
        </div>
      </div>
      <div class="field">
        <label>Новый пароль</label>
        <div class="input-with-icon">
          <input :type="showNewPassword ? 'text' : 'password'" v-model="newPassword" autocomplete="off" />
          <button type="button" class="eye-toggle" @click="showNewPassword = !showNewPassword">
            {{ showNewPassword ? '🙈' : '👁' }}
          </button>
        </div>
      </div>
      <div class="actions">
        <button @click="changePassword">Сменить пароль</button>
      </div>
    </section>

    <section class="card">
      <h3>История запросов на анализ товаров</h3>
      <div v-if="tasks.length === 0" class="no-tasks">
        У вас пока нет запросов на анализ.
      </div>
      <div v-else class="tasks-list">
        <div v-for="task in tasks" :key="task.id" class="task-item">
          <div class="task-info">
            <span class="task-id">Задача #{{ task.id }}</span>
            <span class="ozon-id">Ozon ID: {{ task.ozon_id }}</span>
            <span class="status" :class="task.status">{{ getStatusText(task.status) }}</span>
          </div>
          <div v-if="task.product_id" class="task-actions">
            <button @click="viewReport(task.product_id)">Посмотреть отчет</button>
          </div>
        </div>
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
const tasks = ref([])

// visibility toggles for password fields
const showOldPassword = ref(false)
const showNewPassword = ref(false)

const loadProfile = async () => {
  try {
    const res = await api.get('/user/me')
    name.value = res.data.name || ''
  } catch (e) {
    console.error('Ошибка загрузки профиля', e)
  }
}

const loadTasks = async () => {
  try {
    const res = await api.get('/tasks/my')
    tasks.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки задач', e)
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

const getStatusText = (status) => {
  const statuses = {
    pending: 'Ожидает',
    processing: 'В обработке',
    completed: 'Завершена',
    failed: 'Ошибка'
  }
  return statuses[status] || status
}

const viewReport = (productId) => {
  router.push(`/product/${productId}`)
}

onMounted(() => {
  loadProfile()
  loadTasks()
})

const router = useRouter()

const logout = async () => {
  await auth.logout()
  router.push('/')
}
</script>

<style scoped>
.profile-page {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card h3 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #333;
  font-size: 1.2em;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.field label {
  font-weight: 500;
  color: #555;
}

input {
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ddd;
  font-size: 1em;
}

input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.input-with-icon {
  position: relative;
}

.input-with-icon .eye-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2em;
}

.actions {
  margin-top: 16px;
}

button {
  padding: 10px 16px;
  border-radius: 8px;
  background: #007bff;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.2s;
}

button:hover {
  background: #0056b3;
}

.logout-btn {
  background: #dc3545;
}

.logout-btn:hover {
  background: #c82333;
}

.no-tasks {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-id {
  font-weight: bold;
  color: #333;
}

.ozon-id {
  color: #666;
  font-size: 0.9em;
}

.status {
  font-size: 0.9em;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  font-weight: 500;
}

.status.pending {
  background: #fff3cd;
  color: #856404;
}

.status.processing {
  background: #cce5ff;
  color: #004085;
}

.status.completed {
  background: #d4edda;
  color: #155724;
}

.status.failed {
  background: #f8d7da;
  color: #721c24;
}

.task-actions button {
  background: #28a745;
}

.task-actions button:hover {
  background: #218838;
}
</style>
