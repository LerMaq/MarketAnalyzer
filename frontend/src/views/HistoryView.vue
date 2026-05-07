<template>
  <div class="history-page fade-in">
    <div v-if="isLoading" class="history-loading-overlay">
      <div class="spinner"></div>
      <p>Загрузка истории...</p>
    </div>

    <h2 class="page-title">История анализов</h2>
    
    <div v-if="tasks.length === 0" class="no-tasks">
      У вас пока нет запросов на анализ.
    </div>
    <div v-else class="tasks-grid">
      <div v-for="task in tasks" :key="task.id" class="task-card">
        <!-- Если товар проанализирован -->
        <template v-if="task.status === 'completed' && task.product_id">
          <router-link 
            :to="`/product/${task.ozon_id}/${task.product_id}`"
            class="product-header-link"
            target="_blank"
          >
            <div class="product-header">
              <h3 class="product-name">
                {{ task.product_name || 'Товар проанализирован' }}
                <svg class="arrow-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </h3>
            </div>
          </router-link>
          
          <div class="product-details">
            <div class="detail-item" v-if="task.product_score !== null && task.product_score !== undefined">
              <span class="detail-label">Оценка:</span>
              <span class="score-value" :class="getScoreClass(task.product_score)">
                {{ task.product_score.toFixed(1) }}/10
              </span>
            </div>
            <div class="detail-item" v-if="task.product_price">
              <span class="detail-label">Цена:</span>
              <span class="detail-value price-with-warning">
                {{ formatPrice(task.product_price) }} ₽

              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Артикул:</span>
              <a 
                :href="`https://www.ozon.ru/product/${task.ozon_id}`" 
                target="_blank" 
                rel="noopener noreferrer"
                class="ozon-link"
              >
                {{ task.ozon_id }}
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                  <polyline points="15 3 21 3 21 9"></polyline>
                  <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
              </a>
            </div>
            <div class="detail-item">
              <span class="detail-label">Отзывов проанализировано:</span>
              <span class="detail-value">{{ task.review_count }}</span>
            </div>
          </div>
        </template>

        <!-- Если товар ещё не проанализирован -->
        <template v-else>
          <div class="task-header">
            <div class="task-id-badge">Задача #{{ task.id }}</div>
            <span class="status-badge" :class="task.status">{{ getStatusText(task.status) }}</span>
          </div>
          
          <div class="task-details">
            <div class="detail-item">
              <span class="detail-label">Артикул:</span>
              <a 
                :href="`https://www.ozon.ru/product/${task.ozon_id}`" 
                target="_blank" 
                rel="noopener noreferrer"
                class="ozon-link"
              >
                {{ task.ozon_id }}
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                  <polyline points="15 3 21 3 21 9"></polyline>
                  <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
              </a>
            </div>
            <div class="detail-item">
              <span class="detail-label">Отзывов:</span>
              <span class="detail-value">{{ task.review_count }}</span>
            </div>
          </div>

          <div class="task-status-message">
            {{ getStatusMessage(task.status) }}
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useRouter } from 'vue-router'

const tasks = ref([])
const isLoading = ref(true)
const router = useRouter()

const loadTasks = async () => {
  try {
    const res = await api.get('/tasks/my')
    tasks.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки задач', e)
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

const getStatusMessage = (status) => {
  const messages = {
    pending: 'Задача ожидает обработки в очереди',
    fetching: 'Идёт сбор данных с Ozon',
    processing: 'Анализируем отзывы и формируем отчёт',
    failed: 'Произошла ошибка при обработке'
  }
  return messages[status] || 'Обрабатывается...'
}

const getScoreClass = (score) => {
  if (score >= 8) return 'score-high'
  if (score >= 6) return 'score-medium'
  return 'score-low'
}

const formatPrice = (price) => {
  return new Intl.NumberFormat('ru-RU').format(price)
}

onMounted(async () => {
  try {
    await loadTasks()
  } catch (e) {
    console.error('Ошибка загрузки истории:', e)
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.history-page {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
  position: relative;
}


.page-title {
  text-align: center;
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 8px;
}

.history-loading-overlay {
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

.history-loading-overlay .spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #005bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

.history-page h2 {
  margin-top: 0;
  margin-bottom: 24px;
  color: #333;
  font-size: 1.8em;
  font-weight: 700;
}

.no-tasks {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
}

.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.task-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

/* Проанализированный товар */
.product-header-link {
  text-decoration: none;
  display: block;
  transition: all 0.2s ease;
}

.product-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.product-name {
  margin: 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #005bff;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s ease;
  position: relative;
  padding-right: 28px;
}

.product-header-link:hover .product-name {
  color: #0047cc;
  text-decoration: underline;
}

.arrow-icon {
  position: absolute;
  right: 0;
  top: 2px;
  flex-shrink: 0;
  color: #005bff;
  transition: all 0.3s ease;
}

.product-header-link:hover .arrow-icon {
  transform: translateX(4px);
  color: #0047cc;
}


.product-header-link:hover .click-hint {
  color: #005bff;
}


.score-value {
  font-size: 1.1em;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 8px;
}

.score-high {
  color: #28a745;
  background: #d4edda;
}

.score-medium {
  color: #ffc107;
  background: #fff3cd;
}

.score-low {
  color: #dc3545;
  background: #f8d7da;
}

.product-details,
.task-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95em;
}

.detail-label {
  color: #666;
  font-weight: 500;
}

.detail-value {
  color: #333;
  font-weight: 600;
}

.ozon-link {
  color: #005bff;
  text-decoration: none;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.ozon-link:hover {
  color: #0047cc;
  text-decoration: underline;
}

.ozon-link svg {
  flex-shrink: 0;
}

/* Непроанализированная задача */
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.task-id-badge {
  font-weight: 600;
  color: #333;
  font-size: 1.05em;
}

.status-badge {
  font-size: 0.85em;
  padding: 4px 10px;
  border-radius: 12px;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.fetching {
  background: #cce5ff;
  color: #004085;
}

.status-badge.processing {
  background: #d1ecf1;
  color: #0c5460;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.task-status-message {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #666;
  font-size: 0.9em;
  line-height: 1.5;
  margin-top: auto;
}

/* Адаптивность */
@media (max-width: 768px) {
  .tasks-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .history-page h2 {
    font-size: 1.5em;
  }
  
  .task-card {
    padding: 16px;
  }
  
  .product-name {
    font-size: 1em;
  }
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}
</style>
