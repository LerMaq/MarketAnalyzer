<template>
  <div class="home-wrapper fade-in">
    <div class="hero">
      <h1>Глубокий анализ товаров</h1>
      <p>Узнайте, что на самом деле думают покупатели, с помощью ИИ.</p>
    </div>

    <div class="search-container">
      <div class="search-box">
        <input
          v-model="urlOrId"
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

      <ul v-if="isFocused && recentIds.length > 0" class="suggestions-list">
        <li
          v-for="id in recentIds"
          :key="id"
          @mousedown="selectFromHistory(id)"
        >
          {{ id }}
        </li>
        <li class="clear-history-item" @mousedown="clearHistory">
          Очистить историю
        </li>
      </ul>
    </div>

    <div v-if="taskStatus && taskStatus !== 'completed'" class="loading-status">
      <div class="spinner"></div>
      <p v-if="taskStatus === 'pending'">Задача в очереди...</p>
      <p v-if="taskStatus === 'processing'">ИИ читает отзывы и формирует отчет...</p>
    </div>

    <div v-if="versions.length > 0" class="versions-section">
      <h3>Найдено {{ versions.length }} версии отчета:</h3>
      <div class="versions-grid">
        <div v-for="v in versions" :key="v.id" class="version-card">
          <div class="version-info">
            <span class="date">{{ new Date(v.date_added).toLocaleDateString() }}</span>
            <span class="time">{{ new Date(v.date_added).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}</span>
          </div>
          <button @click="$router.push(`/product/${getOzonId(urlOrId)}/${v.id}`)" class="open-btn">
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

const urlOrId = ref('')
const versions = ref([])
const isLoading = ref(false)
const taskStatus = ref(null)
const recentIds = ref([])
const isFocused = ref(false)
const topProducts = ref([])
const isTopProductsLoading = ref(true)

const getOzonId = (input) => {
  if (!input) return null;
  const match = input.match(/(\d{9,})/);
  return match ? match[0] : input;
};

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
  const saved = localStorage.getItem('recent_ozon_ids')
  if (saved) {
    recentIds.value = JSON.parse(saved)
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

const addToHistory = (id) => {
  if (!id) return
  const ozonId = getOzonId(id);
  if (!ozonId) return;

  const filtered = recentIds.value.filter(item => item !== ozonId)
  recentIds.value = [ozonId, ...filtered].slice(0, 5)
  localStorage.setItem('recent_ozon_ids', JSON.stringify(recentIds.value))
}

const selectFromHistory = (id) => {
  urlOrId.value = id
  isFocused.value = false
  handleSearch()
}

const clearHistory = () => {
  recentIds.value = []
  localStorage.removeItem('recent_ozon_ids')
  isFocused.value = false
}

const handleSearch = async () => {
  const ozonId = getOzonId(urlOrId.value);
  if (!ozonId) return;

  isFocused.value = false
  addToHistory(urlOrId.value)
  isLoading.value = true
  versions.value = []

  try {
    const res = await api.get(`/products/check/${ozonId}`)
    const foundVersions = res.data.versions || []

    if (foundVersions.length > 0) {
      versions.value = foundVersions
      isLoading.value = false
    } else {
      await startNewTask()
    }
  } catch (e) {
    console.error("Детали ошибки:", e)
    alert('Ошибка при связи с сервером')
    isLoading.value = false
  }
}

const startNewTask = async () => {
  try {
    const res = await api.post('/tasks/add', {
      url_or_id: urlOrId.value
    });
    const newTaskId = res.data.task_id;

    if (newTaskId) {
      pollTaskStatus(newTaskId);
    } else {
      console.error("Сервер не вернул ID задачи:", res.data);
    }
  } catch (e) {
    console.error("Ошибка при создании задачи:", e);
  }
}

const pollTaskStatus = (taskId) => {
  const interval = setInterval(async () => {
    try {
      const res = await api.get(`/tasks/status/${taskId}`);
      const taskData = res.data;
      taskStatus.value = taskData.status;

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
        alert("Анализ завершился ошибкой");
      }
    } catch (e) {
      console.error("Ошибка опроса статуса:", e);
    }
  }, 2000);
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

.suggestions-list li {
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  color: #333;
  font-size: 0.95rem;
}

.suggestions-list li:hover {
  background-color: #f0f6ff;
}

.clear-history-item {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee;
  color: #999 !important;
  font-size: 0.85rem !important;
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