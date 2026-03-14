<template>
  <div class="home-wrapper fade-in">
    <div class="hero">
      <h1>Глубокий анализ товаров</h1>
      <p>Узнайте, что на самом деле думают покупатели, с помощью ИИ.</p>
    </div>

    <div class="search-container">
      <div class="search-box">
        <input
          v-model="urlOrQuery"
          placeholder="Вставьте ссылку на Ozon или артикул"
          @keyup.enter="handleSearch"
          @focus="isFocused = true"
          @blur="isFocused = false"
          :disabled="isLoading"
        />
        <button @click="handleSearch" :disabled="isLoading">
          <span v-if="!isLoading">Анализировать</span>
          <span v-else class="mini-spinner"></span>
        </button>
      </div>

      <ul v-if="isFocused && recentSearches.length > 0" class="suggestions-list">
        <li
          v-for="query in recentSearches"
          :key="query"
          class="suggestion-item"
          @mousedown.prevent="selectFromHistory(query)"
        >
          <span class="query-text">{{ query }}</span>
          <button class="paste-btn" title="Вставить в поле" @mousedown.stop.prevent="pasteFromHistory(query)">
            ⤴️
          </button>
        </li>
        <li class="clear-history-item" @mousedown="clearHistory">
          Очистить историю
        </li>
      </ul>
    </div>

    <div v-if="taskStatus && taskStatus !== 'completed' && taskStatus !== 'failed'" class="loading-status">
      <div class="spinner"></div>
      <p v-if="taskStatus === 'checking'">Подождите...</p>
      <p v-if="taskStatus === 'pending'">Задача в очереди...</p>
      <p v-if="taskStatus === 'fetching'">Собираем данные о товаре...</p>
      <p v-if="taskStatus === 'processing'">ИИ читает отзывы и формирует отчет...</p>
      <p
        v-if="taskRetryCount > 0 && (taskStatus === 'pending' || taskStatus === 'fetching')"
        class="retry-hint"
      >
        Повторная попытка анализа... (Попытка {{ taskRetryCount }}/3)
      </p>
    </div>

    <div v-if="taskStatus === 'failed'" class="error-status">
      <p class="error-message">Не удалось провести анализ. Попытка возвращена на баланс</p>
      <button @click="retryAfterFail" class="retry-btn">Попробовать снова</button>
    </div>

    <div v-if="versions.length > 0" class="versions-section">
      <h3>Найдено {{ versions.length }} версии отчета:</h3>
      <div class="versions-grid">
        <div v-for="v in versions" :key="v.id" class="version-card">
          <div class="version-info">
            <span class="date">{{ new Date(v.date_added).toLocaleDateString() }}</span>
            <span class="time">{{ new Date(v.date_added).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}</span>
          </div>
          <button @click="$router.push(`/product/${v.ozon_id}/${v.id}`)" class="open-btn">
            Открыть отчет
          </button>
        </div>

        <div class="version-card update-card" @click="startNewTask">
          <div class="plus-icon">+</div>
          <span>Обновить анализ</span>
        </div>
      </div>
    </div>

    <!-- Топ товаров -->
    <section class="top-section">
      <h2 class="top-title">🏆 Топ товаров 🏆</h2>
      <p class="top-subtitle">Рейтинг по средневзвешенной оценке ИИ</p>
      
      <div v-if="isTopProductsLoading" class="top-loading">
        <div class="spinner"></div>
        <p>Загрузка топ товаров...</p>
      </div>

      <div v-else-if="topProducts.length > 0" class="top-grid">
        <div
          v-for="(product, index) in topProducts"
          :key="product.id"
          class="top-card"
          @click="$router.push(`/product/${product.ozon_id}/${product.id}`)"
        >
          <div class="top-card-rank" :class="rankClass(index)">{{ index + 1 }}</div>
          <div class="top-card-body">
            <div class="top-card-name">{{ product.name }}</div>
            <div class="top-card-meta">
              <span class="top-card-score" :class="scoreClass(product.score)">
                {{ product.score.toFixed(1) }}
              </span>
              <span class="top-card-date">
                {{ new Date(product.date_added).toLocaleDateString() }}
              </span>
            </div>
          </div>
          <div class="top-card-arrow">→</div>
        </div>
      </div>

      <div v-else class="top-empty">
        <p>Топ товаров пока нет</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useRouter } from 'vue-router'

const router = useRouter()

const urlOrQuery = ref('')
const versions = ref([])
const isLoading = ref(false)
const taskStatus = ref(null)
const taskRetryCount = ref(0)
const recentSearches = ref([])
const isFocused = ref(false)
const topProducts = ref([])
const isTopProductsLoading = ref(true)

const scoreClass = (score) => {
  if (score >= 7) return 'score-good'
  if (score >= 4) return 'score-ok'
  return 'score-bad'
}

const rankClass = (index) => {
  if (index === 0) return 'rank-gold'
  if (index === 1) return 'rank-silver'
  if (index === 2) return 'rank-bronze'
  return ''
}

onMounted(async () => {
  const saved = localStorage.getItem('recent_searches')
  if (saved) {
    recentSearches.value = JSON.parse(saved)
  }

  try {
    const res = await api.get('/products/top')
    topProducts.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки топа товаров:', e)
  } finally {
    isTopProductsLoading.value = false
  }
})

const addToHistory = (query) => {
  if (!query) return

  const filtered = recentSearches.value.filter(item => item !== query)
  recentSearches.value = [query, ...filtered].slice(0, 5)
  localStorage.setItem('recent_searches', JSON.stringify(recentSearches.value))
}

const selectFromHistory = (query) => {
  urlOrQuery.value = query
  isFocused.value = false
  handleSearch()
}

const pasteFromHistory = (query) => {
  urlOrQuery.value = query
  isFocused.value = false
}

const clearHistory = () => {
  recentSearches.value = []
  localStorage.removeItem('recent_searches')
  isFocused.value = false
}

const handleSearch = async () => {
  const query = urlOrQuery.value.trim();
  if (!query) return;

  isFocused.value = false;
  addToHistory(query);
  isLoading.value = true;
  versions.value = [];
  taskStatus.value = 'checking';
  taskRetryCount.value = 0;

  try {
    const res = await api.post('/products/check', { url: query });
    const foundVersions = res.data.versions || [];

    if (foundVersions.length > 0) {
      versions.value = foundVersions;
      isLoading.value = false;
      taskStatus.value = null; // Сбрасываем статус, так как версии найдены
    } else {
      await startNewTask(); // Переходим к созданию задачи
    }
  } catch (e) {
    console.error("Детали ошибки:", e);
    alert('Ошибка при связи с сервером');
    isLoading.value = false;
    taskStatus.value = null; // Сбрасываем статус при ошибке
  }
}

const startNewTask = async () => {
  try {
    const res = await api.post('/tasks/add', {
      url_or_id: urlOrQuery.value
    });
    const newTaskId = res.data.task_id;
    const status = res.data.status;

    if (newTaskId) {
      taskStatus.value = status;
      taskRetryCount.value = 0;
      pollTaskStatus(newTaskId);
    } else {
      console.error("Сервер не вернул ID задачи:", res.data);
      isLoading.value = false;
      taskStatus.value = null;
    }
  } catch (e) {
    console.error("Ошибка при создании задачи:", e);
    isLoading.value = false;
    taskStatus.value = null;
  }
}

const pollTaskStatus = (taskId) => {
  const interval = setInterval(async () => {
    try {
      const res = await api.get(`/tasks/status/${taskId}`);
      const taskData = res.data;
      taskStatus.value = taskData.status;
      taskRetryCount.value = taskData.retry_count ?? 0;

      if (taskData.status === 'completed') {
        clearInterval(interval);
        isLoading.value = false;
        if (taskData.ozon_id && taskData.product_id) {
          router.push(`/product/${taskData.ozon_id}/${taskData.product_id}`);
        } else {
          console.error("Данные для редиректа отсутствуют:", taskData);
        }
      } else if (taskData.status === 'failed') {
        clearInterval(interval);
        isLoading.value = false;
      }
    } catch (e) {
      console.error("Ошибка опроса статуса:", e);
      clearInterval(interval);
      isLoading.value = false;
      taskStatus.value = null;
    }
  }, 2000);
};

const retryAfterFail = () => {
  taskStatus.value = null;
  taskRetryCount.value = 0;
  isLoading.value = false;
};
</script>

<style scoped>
.home-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding-top: 4rem;
}

.hero {
  text-align: center;
  margin-bottom: 3rem;
}

.hero h1 {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 1rem;
  color: #1a1a1a;
}

.hero p {
  color: #666;
  font-size: 1.1rem;
}

/* Search Container */
.search-container {
  position: relative;
  margin-bottom: 3rem;
}

.search-box {
  display: flex;
  gap: 12px;
  background: white;
  padding: 12px;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 91, 255, 0.1);
  position: relative;
  z-index: 10;
}

input {
  flex: 1;
  border: 1px solid #eee;
  padding: 16px;
  border-radius: 12px;
  font-size: 1rem;
  outline: none;
  transition: border 0.2s;
}

input:focus {
  border-color: #005bff;
}

button {
  background: #005bff;
  color: white;
  border: none;
  padding: 0 30px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

button:hover { background: #0046d5; }
button:disabled { background: #ccc; }

/* Suggestions List */
.suggestions-list {
  position: absolute;
  top: calc(100% - 16px);
  left: 0;
  right: 0;
  background: white;
  border-radius: 0 0 16px 16px;
  box-shadow: 0 20px 30px rgba(0, 91, 255, 0.1);
  list-style: none;
  padding: 28px 12px 12px 12px;
  margin: 0;
  z-index: 9;
  border-top: 1px solid #eee;
}

.suggestion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  color: #333;
  font-size: 0.95rem;
}

.suggestion-item:hover {
  background-color: #f0f6ff;
}

.query-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.paste-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: #999;
  padding: 0 5px;
}

.paste-btn:hover {
  color: #005bff;
}

.clear-history-item {
  margin-top: 8px;
  padding: 12px 16px;
  border-top: 1px solid #eee;
  color: #999 !important;
  font-size: 0.85rem !important;
  cursor: pointer;
}

.clear-history-item:hover {
  color: #f56c6c !important;
  background: none !important;
}

/* Версии */
.versions-section {
  margin-top: 3rem;
}

.versions-section h3 {
  margin-bottom: 1.5rem;
  color: #333;
}

.versions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.version-card {
  background: white;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid #eee;
  display: flex;
  flex-direction: column;
  gap: 15px;
  transition: transform 0.2s;
}

.version-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.05);
}

.version-info {
  display: flex;
  flex-direction: column;
}

.date { font-weight: 700; color: #1a1a1a; }
.time { font-size: 0.9rem; color: #888; }

.open-btn {
  padding: 10px;
  font-size: 0.9rem;
  background: #f0f6ff;
  color: #005bff;
}

.update-card {
  border: 2px dashed #005bff;
  background: transparent;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #005bff;
  font-weight: 600;
}

.plus-icon { font-size: 1.5rem; margin-bottom: 5px; }

/* Лоадер */
.loading-status {
  text-align: center;
  padding: 20px;
}

.error-status {
  text-align: center;
  padding: 24px;
  background: #fdeaea;
  border: 1px solid #f8d7da;
  border-radius: 12px;
  margin-bottom: 20px;
}

.error-message {
  color: #721c24;
  margin: 0 0 16px 0;
  font-weight: 500;
}

.retry-btn {
  display: block;
  margin: 0 auto;
  background: #dc3545;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #c82333;
}

.retry-hint {
  font-size: 0.85rem;
  color: #999;
  margin-top: 8px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #005bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin { 100% { transform: rotate(360deg); } }
.fade-in { animation: fadeIn 0.6s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Топ товаров */
.top-section {
  margin-top: 3rem;
}

.top-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 0.3rem;
  justify-self: center;
}

.top-subtitle {
  color: #888;
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
  justify-self: center;
}

.top-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.top-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  padding: 16px 20px;
  border-radius: 14px;
  border: 1px solid #eee;
  cursor: pointer;
  transition: all 0.2s ease;
}

.top-card:hover {
  transform: translateX(6px);
  box-shadow: 0 6px 20px rgba(0, 91, 255, 0.1);
  border-color: #d0e0ff;
}

.top-card-rank {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.95rem;
  color: #666;
  background: #f0f0f0;
  flex-shrink: 0;
}

.rank-gold {
  background: linear-gradient(135deg, #ffd700, #ffb800);
  color: white;
  box-shadow: 0 3px 10px rgba(255, 184, 0, 0.3);
}

.rank-silver {
  background: linear-gradient(135deg, #c0c0c0, #a8a8a8);
  color: white;
  box-shadow: 0 3px 10px rgba(168, 168, 168, 0.3);
}

.rank-bronze {
  background: linear-gradient(135deg, #cd7f32, #b5651d);
  color: white;
  box-shadow: 0 3px 10px rgba(181, 101, 29, 0.3);
}

.top-card-body {
  flex: 1;
  min-width: 0;
}

.top-card-name {
  font-weight: 600;
  color: #1a1a1a;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.top-card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-card-score {
  font-weight: 800;
  font-size: 0.9rem;
  padding: 2px 10px;
  border-radius: 8px;
}

.score-good {
  color: #0d9e5f;
  background: #e6f9f0;
}

.score-ok {
  color: #d4a017;
  background: #fef9e7;
}

.score-bad {
  color: #e74c3c;
  background: #fdeaea;
}

.top-card-date {
  color: #999;
  font-size: 0.8rem;
}

.top-card-arrow {
  color: #ccc;
  font-size: 1.2rem;
  flex-shrink: 0;
  transition: color 0.2s;
}

.top-card:hover .top-card-arrow {
  color: #005bff;
}

/* Стили для лоадера топ товаров */
.top-loading {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.top-loading .spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #005bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

.top-empty {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-style: italic;
}
</style>