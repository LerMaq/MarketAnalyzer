<template>
  <div class="profile-page fade-in">
    <div v-if="isLoading" class="profile-loading-overlay">
      <div class="spinner"></div>
      <p>Загрузка профиля...</p>
    </div>

    <h2>Профиль</h2>
    <section class="card subscription-block">
      <h3>Подписка</h3>
      <div class="tariff-badge" :class="profile?.tariff || 'free'">
        {{ profile?.tariff === 'premium' ? 'Премиум' : 'Бесплатно' }}
      </div>
      <div class="limits-grid">
        <div class="limit-item">
          <div class="limit-label">Анализов осталось на сегодня</div>
          <div class="limit-value">{{ analysisLeft }} из {{ profile?.limits?.analysis ?? 0 }}</div>
          <div class="progress-bar">
            <div class="progress-fill analysis" :style="{ width: analysisProgress + '%' }"></div>
          </div>
        </div>
        <div class="limit-item">
          <div class="limit-label">Сообщений в чате осталось на сегодня</div>
          <div class="limit-value">{{ chatLeft }} из {{ profile?.limits?.chat ?? 0 }}</div>
          <div class="progress-bar">
            <div class="progress-fill chat" :style="{ width: chatProgress + '%' }"></div>
          </div>
        </div>
      </div>
      <router-link to="/tariffs" class="link-tariffs">Сменить тариф →</router-link>
    </section>

    <!-- Админ-панель (только для администраторов) -->
    <AdminPanel v-if="isAdmin" />

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
      <h3>История персональных запросов на анализ товаров</h3>
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
              <button @click="viewReport(task.ozon_id, task.product_id)">Посмотреть отчет</button>
            </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="account-actions">
        <button @click="logout" class="logout-btn">Выйти</button>
        <button @click="showDeleteModal = true" class="delete-btn">Удалить аккаунт</button>
      </div>
    </section>
  </div>

  <!-- Модальное окно подтверждения удаления аккаунта -->
  <Transition name="fade">
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="cancelDelete">
      <div class="modal-content delete-confirm-modal">
        <button @click="cancelDelete" class="close-modal modal-close-big">&times;</button>
        <header class="modal-header">
          <h3>Подтверждение удаления аккаунта</h3>
        </header>

        <div class="modal-body">
          <p>Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо — все ваши данные будут удалены без возможности восстановления.</p>

          <div class="modal-actions">
            <button type="button" @click="cancelDelete">Отмена</button>
            <button type="button" @click="confirmDelete" class="delete-confirm-btn">Удалить аккаунт</button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/client'
import auth from '../auth'
import { useRouter } from 'vue-router'
import AdminPanel from '../components/admin/AdminPanel.vue'

const name = ref('')
const oldPassword = ref('')
const newPassword = ref('')
const tasks = ref([])
const profile = ref(null)
const isLoading = ref(true)

const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showDeleteModal = ref(false)
const isAdmin = ref(false)

const loadProfile = async () => {
  try {
    const res = await api.get('/user/me')
    profile.value = res.data
    name.value = res.data.name || ''
    // Проверяем права администратора на основе permissions из ответа
    isAdmin.value = res.data.permissions?.includes('admin.panel') || false
  } catch (e) {
    console.error('Ошибка загрузки профиля', e)
  }
}

const analysisLeft = computed(() => {
  const lim = profile.value?.limits?.analysis ?? 0
  const used = profile.value?.usage?.analysis ?? 0
  return Math.max(0, lim - used)
})

const chatLeft = computed(() => {
  const lim = profile.value?.limits?.chat ?? 0
  const used = profile.value?.usage?.chat ?? 0
  return Math.max(0, lim - used)
})

const analysisProgress = computed(() => {
  const lim = profile.value?.limits?.analysis ?? 0
  if (lim === 0) return 0
  const used = profile.value?.usage?.analysis ?? 0
  return Math.min(100, (used / lim) * 100)
})

const chatProgress = computed(() => {
  const lim = profile.value?.limits?.chat ?? 0
  if (lim === 0) return 0
  const used = profile.value?.usage?.chat ?? 0
  return Math.min(100, (used / lim) * 100)
})

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
    fetching: 'Сбор данных',
    processing: 'В обработке',
    completed: 'Завершена',
    failed: 'Ошибка'
  }
  return statuses[status] || status
}

const viewReport = (ozonId, productId) => {
  router.push(`/product/${ozonId}/${productId}`)
}

onMounted(async () => {
  try {
    await Promise.all([loadProfile(), loadTasks()])
  } catch (e) {
    console.error('Ошибка загрузки данных профиля:', e)
  } finally {
    isLoading.value = false
  }
})

const router = useRouter()

const logout = async () => {
  await auth.logout()
  router.push('/')
}

const confirmDelete = async () => {
  try {
    await api.delete('/user/me')
    await auth.logout()
    router.push('/')
  } catch (e) {
    console.error('Ошибка удаления аккаунта', e)
    alert(e.response?.data?.detail || 'Ошибка при удалении аккаунта')
    showDeleteModal.value = false
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
}
</script>

<style scoped>
.profile-page {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
  position: relative;
}

.profile-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  color: #666;
}

.profile-loading-overlay .spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #005bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

.profile-page h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5em;
  justify-self: center;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  margin-top: 20px;
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

.account-actions {
  display: flex;
  gap: 12px;
}

.logout-btn {
  background: white;
  color: black;
  border: 2px solid #dc3545;
}

.logout-btn:hover {
  background: #f8f9fa;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.delete-btn:hover {
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

.status.fetching {
  background: #cce5ff;
  color: #004085;
}

.status.processing {
  background: #e8f4e8;
  color: #1e5f1e;
}

.status.failed {
  background: #f8d7da;
  color: #721c24;
}

.status.completed {
  background: #d4edda;
  color: #155724;
}

.task-actions button {
  background: #28a745;
}

.task-actions button:hover {
  background: #218838;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 500px;
  padding: 30px;
  position: relative;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.modal-close-big {
  position: absolute;
  top: 15px;
  right: 20px;
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #888;
}

.modal-body {
  padding: 0;
}

.modal-body p {
  line-height: 1.6;
  color: #444;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-actions button {
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 1em;
  transition: all 0.2s;
}

.modal-actions button[type="button"] {
  background: #f0f0f0;
  color: #333;
}

.modal-actions button[type="button"]:hover {
  background: #e0e0e0;
}

.delete-confirm-btn {
  background: #dc3545 !important;
  color: white;
}

.delete-confirm-btn:hover {
  background: #c82333 !important;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.subscription-block .tariff-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.subscription-block .tariff-badge.free {
  background: #e8e8e8;
  color: #555;
}

.subscription-block .tariff-badge.premium {
  background: #005bff;
  color: white;
}

.limits-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.limit-item .limit-label {
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 4px;
}

.limit-item .limit-value {
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.progress-bar {
  height: 8px;
  background: #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-fill.analysis {
  background: #28a745;
}

.progress-fill.chat {
  background: #007bff;
}

.link-tariffs {
  display: inline-block;
  margin-top: 16px;
  color: #005bff;
  text-decoration: none;
  font-weight: 500;
}

.link-tariffs:hover {
  text-decoration: underline;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}
</style>