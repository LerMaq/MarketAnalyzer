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

        <div
          ref="reviewSelectRef"
          class="review-select"
          :class="{ open: isReviewMenuOpen, disabled: !canChooseReviewCount }"
        >
          <button
            type="button"
            class="review-trigger"
            :disabled="isLoading"
            @click="toggleReviewMenu"
            :title="canChooseReviewCount ? 'Количество отзывов для анализа' : 'Доступно только с Premium'"
          >
            <span class="review-trigger-label">Отзывов</span>
            <span class="review-trigger-value">{{ reviewCount }}</span>
            <svg class="chevron" :class="{ rotated: isReviewMenuOpen }" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
              <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <Transition name="review-menu">
            <ul v-if="isReviewMenuOpen && canChooseReviewCount" class="review-menu">
              <li
                v-for="opt in REVIEW_OPTIONS"
                :key="opt"
                class="review-option"
                :class="{ active: opt === reviewCount }"
                @click="selectReviewCount(opt)"
              >
                <span>{{ opt }}</span>
                <span v-if="opt === reviewCount" class="review-check">✓</span>
              </li>
            </ul>
          </Transition>
          <Transition name="review-menu">
            <div v-if="showPremiumHint" class="review-tooltip">
              Доступно только с подпиской Premium
            </div>
          </Transition>
        </div>

        <button @click="handleSearch" :disabled="isLoading">
          <span v-if="!isLoading">Анализировать</span>
          <span v-else class="mini-spinner"></span>
        </button>
      </div>

      <Transition name="fade">
        <div v-if="errorMessage" class="modal-overlay" @click.self="clearError">
          <div class="modal-content error-modal">
            <button @click="clearError" class="close-modal modal-close-big">&times;</button>
            <header class="modal-header">
              <h3>Ошибка</h3>
            </header>
            <div class="modal-body">
              <p>{{ errorMessage }}</p>
              <div class="modal-actions">
                <button class="btn-primary" @click="clearError">Понятно</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>

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

    <div v-if="!isBackground && taskStatus && taskStatus !== 'completed' && taskStatus !== 'failed'" class="loading-status">
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
          <button class="bg-btn" @click="minimizeAnalysis">Оставить в фоне</button>
    </div>

    <div v-if="isBackground && taskStatus && taskStatus !== 'completed' && taskStatus !== 'failed'" class="background-hint">
      Анализ идёт в фоне. Мы уведомим, когда он завершится.
      <button class="link-btn" @click="restoreAnalysis">Показать статус</button>
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
            <span class="version-meta">{{ v.review_count ?? 0 }} отзывов</span>
          </div>
          <button @click="openProductReport(v)" class="open-btn">
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
          @click="openProductReport(product)"
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

    <!-- Modal for unauthenticated users when no reports found -->
    <Transition name="fade">
      <div v-if="showLoginPrompt" class="modal-overlay" @click.self="showLoginPrompt = false">
        <div class="modal-content auth-prompt-modal">
          <button @click="showLoginPrompt = false" class="close-modal modal-close-big">&times;</button>
          <header class="modal-header">
            <h3>Анализ не найден</h3>
          </header>
          <div class="modal-body">
            <div class="prompt-icon">🔍</div>
            <p>Этот товар еще не был проанализирован нашей нейросетью.</p>
            <p>Чтобы запустить глубокий анализ отзывов и характеристик, необходимо <strong>авторизоваться</strong>.</p>
            <div class="modal-actions">
              <button @click="showLoginPrompt = false" class="btn-secondary">Отмена</button>
              <button @click="$router.push('/login')" class="btn-primary">Войти и начать</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
</div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import auth from '../auth'
import { addTask, updateTaskOptions, tasks as backgroundTasks } from '../analysisTracker'

const router = useRouter()
const urlOrQuery = ref('')
const versions = ref([])
const isLoading = ref(false)
const taskStatus = ref(null)
const taskRetryCount = ref(0)
const currentTaskId = ref(null)
const recentSearches = ref([])
const checkedOzonId = ref(null)
const isFocused = ref(false)
const topProducts = ref([])
const isTopProductsLoading = ref(true)
const showLoginPrompt = ref(false)
const errorMessage = ref('')
const isBackground = ref(false)

const REVIEW_OPTIONS = [50, 100, 150, 200]
const reviewCount = ref(50)
const isReviewMenuOpen = ref(false)
const showPremiumHint = ref(false)
let premiumHintTimer = null
const reviewSelectRef = ref(null)

const handleClickOutside = (event) => {
  if (reviewSelectRef.value && !reviewSelectRef.value.contains(event.target)) {
    isReviewMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const canChooseReviewCount = computed(() => {
  return auth.user.value?.permissions?.includes('task.priority_queue') || false
})

const toggleReviewMenu = () => {
  if (!canChooseReviewCount.value) {
    isReviewMenuOpen.value = false
    showPremiumHint.value = true
    if (premiumHintTimer) clearTimeout(premiumHintTimer)
    premiumHintTimer = setTimeout(() => {
      showPremiumHint.value = false
    }, 2200)
    return
  }
  isReviewMenuOpen.value = !isReviewMenuOpen.value
}

const selectReviewCount = (value) => {
  reviewCount.value = value
  isReviewMenuOpen.value = false
}

watch(canChooseReviewCount, (val) => {
  if (!val) reviewCount.value = 50
})

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

const currentTask = computed(() => {
  return backgroundTasks.value.find(t => t.id === currentTaskId.value) || null
})

watch(
  currentTask,
  (task) => {
    if (task) {
      taskStatus.value = task.status
      taskRetryCount.value = task.retry_count ?? 0
    } else if (currentTaskId.value) {
      taskStatus.value = null
      taskRetryCount.value = 0
      currentTaskId.value = null
      isBackground.value = false
    }
  },
  { deep: true }
)

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

const normalizeArticle = (value) => {
  if (value === null || value === undefined) return null
  const normalized = String(value).trim()
  if (!normalized || normalized === 'undefined' || normalized === 'null') return null
  return normalized
}

const getReportArticle = (report, fallbackArticle = null) => {
  const directArticle = normalizeArticle(
    report?.ozon_id ?? report?.article ?? report?.ozon_article ?? report?.product_ozon_id
  )
  return directArticle || normalizeArticle(fallbackArticle)
}

const openProductReport = (report) => {
  if (!report?.id) return
  const article = getReportArticle(report, checkedOzonId.value) || 'unknown'
  router.push(`/product/${article}/${report.id}`)
}

const handleSearch = async () => {
  const query = urlOrQuery.value.trim();
  if (!query) return;

  isFocused.value = false;
  errorMessage.value = '';
  currentTaskId.value = null;
  checkedOzonId.value = null;
  addToHistory(query);
  isLoading.value = true;
  versions.value = [];
  taskStatus.value = 'checking';
  taskRetryCount.value = 0;
  isBackground.value = false;

  try {
    const res = await api.post('/products/check', { url: query });
    checkedOzonId.value = normalizeArticle(res.data?.ozon_id);
    const foundVersions = res.data.versions || [];

    if (foundVersions.length > 0) {
      versions.value = foundVersions;
      isLoading.value = false;
      taskStatus.value = null; // Сбрасываем статус, так как версии найдены
    } else {
      // Если версий нет и пользователь не авторизован — показываем модалку
      if (!auth.user.value) {
        isLoading.value = false;
        taskStatus.value = null;
        showLoginPrompt.value = true;
      } else {
        await startNewTask(); // Переходим к созданию задачи
      }
    }
  } catch (e) {
    console.error("Детали ошибки:", e);
    const status = e.response?.status;
    const detail = e.response?.data?.detail;

    if (status === 400) {
      errorMessage.value = detail || 'Ссылка или артикул не распознаны. Проверьте, что вы вставили ссылку Ozon или корректный артикул.';
    } else if (status === 401) {
      errorMessage.value = 'Для запуска анализа нужно войти в аккаунт.';
      showLoginPrompt.value = true;
    } else if (status === 429) {
      errorMessage.value = detail || 'Дневной лимит запросов отчета исчерпан. Проверьте лимиты в профиле.';
    } else {
      errorMessage.value = 'Не удалось связаться с сервером. Попробуйте ещё раз позже.';
    }
    isLoading.value = false;
    taskStatus.value = null; // Сбрасываем статус при ошибке
  }
}

const startNewTask = async () => {
  try {
    const res = await api.post('/tasks/add', {
      url_or_id: urlOrQuery.value,
      review_count: canChooseReviewCount.value ? reviewCount.value : 50
    });
    const newTaskId = res.data.task_id;
    const status = res.data.status;

    if (newTaskId) {
      currentTaskId.value = newTaskId;
      taskStatus.value = status;
      taskRetryCount.value = 0;
      isBackground.value = false;
      isLoading.value = false;
      addTask(newTaskId, { openOnComplete: true });
    } else {
      console.error("Сервер не вернул ID задачи:", res.data);
      isLoading.value = false;
      taskStatus.value = null;
    }
  } catch (e) {
    console.error("Ошибка при создании задачи:", e);
    const status = e.response?.status;
    const detail = e.response?.data?.detail;

    if (status === 400) {
      errorMessage.value = detail || 'Ссылка или артикул не распознаны. Проверьте, что вы вставили ссылку Ozon или корректный артикул.';
    } else if (status === 401) {
      errorMessage.value = 'Для запуска анализа нужно войти в аккаунт.';
      showLoginPrompt.value = true;
    } else if (status === 403) {
      errorMessage.value = detail || 'Недостаточно прав для запуска анализа на текущем тарифе.';
    } else if (status === 429) {
      errorMessage.value = detail || 'Дневной лимит анализов исчерпан. Проверьте лимиты в профиле.';
    } else {
      errorMessage.value = 'Не удалось создать задачу на анализ. Попробуйте позже.';
    }
    isLoading.value = false;
    taskStatus.value = null;
  }
}


const retryAfterFail = () => {
  taskStatus.value = null;
  taskRetryCount.value = 0;
  currentTaskId.value = null;
  isLoading.value = false;
  errorMessage.value = '';
  isBackground.value = false;
};

const clearError = () => {
  errorMessage.value = ''
}

const minimizeAnalysis = () => {
  isBackground.value = true
  if (currentTaskId.value) {
    updateTaskOptions(currentTaskId.value, { openOnComplete: false })
  }
}

const restoreAnalysis = () => {
  isBackground.value = false
  if (currentTaskId.value) {
    updateTaskOptions(currentTaskId.value, { openOnComplete: true })
  }
}
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

.search-box input {
  flex: 1;
  border: 1px solid #eee;
  padding: 16px;
  border-radius: 12px;
  font-size: 1rem;
  outline: none;
  transition: border 0.2s;
  min-width: 0;
}

.search-box input:focus {
  border-color: #005bff;
}

.search-box button {
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
  white-space: nowrap;
  flex-shrink: 0;
}

.search-box button:hover { background: #0046d5; }
.search-box button:disabled { background: #ccc; }

/* Кастомный селектор количества отзывов */
.review-select {
  position: relative;
  flex-shrink: 0;
}

button.review-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
  padding: 0 14px;
  border: 1px solid #e2e4ea;
  border-radius: 12px;
  background-color: #f3f4f7; /* Same as disabled state */
  color: #1a1a1a; /* Darker text for contrast */
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.review-select .review-trigger:hover {
  border-color: #d0d5dd;
  background-color: #e8ebf0; /* Slightly darker on hover */
}

.review-select.disabled .review-trigger {
  background: #f3f4f7;
  color: #8a8f9c;
  border-color: #e2e4ea;
  cursor: not-allowed;
}

.review-trigger-label {
  font-size: 0.78rem;
  color: #666; /* Darker gray for better contrast */
  font-weight: 500;
  letter-spacing: 0.02em;
}

.review-select.disabled .review-trigger-label {
  color: #9aa1ae;
}

.review-trigger-value {
  font-size: 1rem;
  font-weight: 700;
  color: inherit;
  min-width: 28px;
  text-align: center;
}

.review-select.disabled .review-trigger-value {
  color: #8a8f9c;
}

.chevron {
  color: #5a6b8a;
  transition: transform 0.2s ease;
}

.chevron.rotated {
  transform: rotate(180deg);
}

.review-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  min-width: 140px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 91, 255, 0.18);
  border: 1px solid #eef0f6;
  list-style: none;
  margin: 0;
  padding: 6px;
  z-index: 20;
}

.review-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  font-weight: 600;
  color: #1a1a1a;
  cursor: pointer;
  transition: background 0.15s ease;
  font-size: 0.95rem;
}

.review-option:hover {
  background: #f0f6ff;
  color: #005bff;
}

.review-option.active {
  background: linear-gradient(135deg, #ecf2ff, #dde7ff);
  color: #005bff;
}

.review-check {
  color: #005bff;
  font-weight: 700;
}

.review-tooltip {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  white-space: nowrap;
  padding: 8px 12px;
  background: #1a1a1a;
  color: #fff;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
  z-index: 20;
}

.review-menu-enter-active,
.review-menu-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.review-menu-enter-from,
.review-menu-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Адаптивность для search-box */
@media (max-width: 580px) {
  .search-box {
    flex-direction: column;
  }
  
  .search-box button {
    width: 100%;
    padding: 12px;
  }

  .review-select {
    width: 100%;
  }

  .review-trigger {
    width: 100%;
    justify-content: space-between;
    padding: 12px 14px;
  }
}

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
  grid-template-columns: 1fr;
  gap: 16px;
}

@media (min-width: 481px) {
  .versions-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
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
  gap: 4px;
}

.date { font-weight: 700; color: #1a1a1a; }
.time { font-size: 0.9rem; color: #888; }
.version-meta {
  font-size: 0.85rem;
  color: #5a6b8a;
}

.open-btn {
  padding: 10px;
  font-size: 0.9rem;
  background: #f0f6ff;
  color: #005bff;
  border: none;
  outline: none;
  border-radius: 10px;
}

.open-btn:focus {
  outline: none;
  box-shadow: none;
}

.open-btn:focus-visible {
  outline: 2px solid #005bff;
  outline-offset: 2px;
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
.bg-btn {
  margin-top: 12px;
  background: #f0f2f5;
  color: #333;
  border: 1px solid #e0e0e0;
  padding: 8px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}
.bg-btn:hover {
  background: #e4e6e9;
}

.background-hint {
  margin: 16px 0;
  padding: 12px 16px;
  background: #f0f6ff;
  border: 1px solid #d6e7ff;
  color: #1a3d8f;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
}
.background-hint .link-btn {
  background: #005bff;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}
.background-hint .link-btn:hover {
  background: #0046d5;
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

/* Auth Prompt Modal */
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
  max-width: 450px;
  padding: 30px;
  position: relative;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  text-align: center;
}

.modal-header {
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.3rem;
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

.prompt-icon {
  font-size: 3rem;
  margin-bottom: 15px;
}

.modal-body p {
  line-height: 1.6;
  color: #555;
  margin-bottom: 15px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 25px;
}

.modal-actions button {
  flex: 1;
  padding: 12px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-secondary {
  background: #f0f2f5;
  color: #333;
}

.btn-secondary:hover {
  background: #e4e6e9;
}

.btn-primary {
  background: #005bff;
  color: white;
}

.btn-primary:hover {
  background: #0046d5;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}


.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(6px);
}

.modal-content {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 460px;
  padding: 28px;
  position: relative;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.error-modal .modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
}

.error-modal .modal-body p {
  margin: 12px 0 0 0;
  color: #444;
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-primary {
  background: #005bff;
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:hover {
  background: #0046d5;
}

.modal-header {
  border-bottom: 1px solid #eee;
  padding-bottom: 12px;
}

.modal-body {
  padding-top: 6px;
}

.modal-close-big {
  position: absolute;
  top: 12px;
  right: 16px;
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #888;
}
</style>




