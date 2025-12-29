<script setup>
import { ref, onUnmounted } from 'vue';
import axios from 'axios';

/**
 * НАСТРОЙКА API
 * Замените URL, если ваш бэкенд запущен на другом порту
 */
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// --- СОСТОЯНИЯ (STATE) ---
const view = ref('home'); // Возможные значения: 'home', 'loading', 'report'
const urlOrId = ref('');
const ozonId = ref(null);
const loading = ref(false);
const error = ref(null);

// Данные отчета и проверки
const report = ref(null);
const checkInfo = ref(null); // Хранит { exists, date_added, ozon_id }

// Модальное окно для метрик
const isMetricModalVisible = ref(false);
const selectedMetric = ref(null);

// Чат-бот
const question = ref('');
const chatHistory = ref([]);
const isSendingChat = ref(false);

// Таймер для опроса бэкенда (Polling)
let pollInterval = null;

// --- ЛОГИКА ---

// Извлечение ID из ссылки или строки
const getOzonId = (input) => {
  const match = input.match(/(\d{8,12})/);
  return match ? match[0] : input.trim();
};

// ШАГ 1: Проверка наличия товара в БД
const handleCheck = async () => {
  const id = getOzonId(urlOrId.value);
  if (!id) return alert('Введите корректный ID или ссылку');
  
  ozonId.value = id;
  loading.value = true;
  error.value = null;

  try {
    const res = await api.get(`/products/check/${id}`);
    checkInfo.value = res.data;
    
    if (!res.data.exists) {
      // Если товара нет, сразу запускаем анализ
      await startAnalysis();
    }
    // Если товар есть, UI предложит выбор (см. template)
  } catch (err) {
    error.value = "Ошибка при связи с сервером. Убедитесь, что FastAPI запущен.";
    console.error(err);
  } finally {
    loading.value = false;
  }
};

// ШАГ 2: Запуск процесса анализа (POST)
const startAnalysis = async () => {
  try {
    loading.value = true;
    checkInfo.value = null; // Закрываем окно выбора
    await api.post('/products/analyze', { url_or_id: ozonId.value });
    
    // Переходим в режим ожидания
    view.value = 'loading';
    startPolling();
  } catch (err) {
    error.value = "Не удалось поставить товар в очередь на анализ.";
  } finally {
    loading.value = false;
  }
};

// ШАГ 3: Опрос бэкенда (Polling)
const startPolling = () => {
  pollInterval = setInterval(async () => {
    try {
      const res = await api.get(`/products/check/${ozonId.value}`);
      if (res.data.exists) {
        stopPolling();
        await fetchFullReport();
      }
    } catch (e) {
      console.warn("Ожидание готовности анализа...");
    }
  }, 3000); // Проверка каждые 3 секунды
};

const stopPolling = () => {
  if (pollInterval) clearInterval(pollInterval);
};

// ШАГ 4: Получение полных данных
const fetchFullReport = async () => {
  try {
    const res = await api.get(`/products/report/${ozonId.value}`);
    report.value = res.data;
    view.value = 'report';
  } catch (err) {
    error.value = "Ошибка при загрузке данных отчета.";
  }
};

// Логика модального окна метрик
const openMetricModal = (metric) => {
  selectedMetric.value = metric;
  isMetricModalVisible.value = true;
};

const closeMetricModal = () => {
  isMetricModalVisible.value = false;
  selectedMetric.value = null;
};

// ЧАТ-БОТ
const askAI = async () => {
  if (!question.value || isSendingChat.value) return;
  
  const userText = question.value;
  chatHistory.value.push({ role: 'user', text: userText });
  question.value = '';
  isSendingChat.value = true;

  try {
    const res = await api.post('/chat/ask', {
      ozon_id: parseInt(ozonId.value),
      question: userText
    });
    chatHistory.value.push({ role: 'ai', text: res.data.answer });
  } catch (e) {
    chatHistory.value.push({ role: 'error', text: 'Ошибка нейросети. Попробуйте позже.' });
  } finally {
    isSendingChat.value = false;
  }
};

// Сброс всего и возврат на главную
const reset = () => {
  stopPolling();
  view.value = 'home';
  report.value = null;
  checkInfo.value = null;
  chatHistory.value = [];
  urlOrId.value = '';
  closeMetricModal();
};

onUnmounted(stopPolling);
</script>

<template>
  <div class="app-wrapper">
    <header class="header">
      <div class="logo" @click="reset">Ozon<span>AI</span></div>
      <div v-if="ozonId && view !== 'home'" class="current-id">Товар: {{ ozonId }}</div>
    </header>

    <main class="container">
      
      <!-- HOME VIEW -->
      <section v-if="view === 'home'" class="fade-in">
        <div class="hero">
          <h1>Глубокий анализ товаров</h1>
          <p>Узнайте, что на самом деле думают покупатели, с помощью ИИ.</p>
        </div>

        <div class="search-box">
          <input 
            v-model="urlOrId" 
            placeholder="Вставьте ссылку на Ozon или артикул" 
            @keyup.enter="handleCheck"
          />
          <button @click="handleCheck" :disabled="loading">
            {{ loading ? 'Проверка...' : 'Анализировать' }}
          </button>
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>

        <div v-if="checkInfo?.exists" class="modal">
          <div class="modal-content">
            <h3>Товар уже анализировался</h3>
            <p>Последнее обновление: <strong>{{ new Date(checkInfo.date_added).toLocaleString() }}</strong></p>
            <div class="modal-actions">
              <button @click="fetchFullReport">Посмотреть готовый</button>
              <button @click="startAnalysis">Обновить анализ</button>
            </div>
          </div>
        </div>
      </section>

      <!-- LOADING VIEW -->
      <section v-if="view === 'loading'" class="loading-state fade-in">
        <div class="spinner"></div>
        <h2>ИИ читает отзывы...</h2>
        <p>Это может занять от 20 до 60 секунд. Мы сообщим, как только отчет будет готов.</p>
      </section>

      <!-- REPORT VIEW -->
      <section v-if="view === 'report' && report" class="report-view fade-in">
        <div class="report-layout">
          
          <div class="analytics-col">
            <button class="back-link" @click="reset">← На главную</button>
            <h2>{{ report.name }}</h2>

            <div class="card ai-summary">
              <h3><span class="icon">✨</span> Резюме нейросети</h3>
              <p>{{ report.summary.text }}</p>
            </div>

            <div class="card overall-score-card">
              <h3><span class="icon">🏆</span> Общая оценка товара</h3>
              <div class="score-display">
                <span class="score-value">{{ report.score }}</span>
                <span class="score-max">/ 100</span>
              </div>
              <p class="score-description">
                Итоговый балл, основанный на анализе всех метрик и их весов.
              </p>
            </div>

            <div class="metrics-grid">
              <div v-for="pm in report.product_metrics" :key="pm.metric.name" class="metric-card">
                <div class="metric-head">
                  <span class="m-name">{{ pm.metric.name }}</span>
                  <span class="info-icon" @click="openMetricModal(pm.metric)">i</span>
                  <span class="m-score">{{ pm.score }}/100</span>
                </div>
                <div class="progress-bar">
                  <div class="fill" :style="{ width: pm.score + '%' }"></div>
                </div>
                <p class="m-explain">{{ pm.explanation }}</p>
              </div>
            </div>
          </div>

          <aside class="chat-col">
            <div class="chat-container">
              <h3>Вопросы о товаре</h3>
              <div class="chat-messages">
                <div v-if="chatHistory.length === 0" class="empty-chat">
                  Спросите ИИ о чем угодно, например: "Какие главные недостатки у этого товара?"
                </div>
                <div v-for="(msg, i) in chatHistory" :key="i" :class="['message', msg.role]">
                  {{ msg.text }}
                </div>
                <div v-if="isSendingChat" class="message ai typing">ИИ думает...</div>
              </div>
              <div class="chat-input">
                <input v-model="question" @keyup.enter="askAI" placeholder="Ваш вопрос..." />
                <button @click="askAI" :disabled="isSendingChat">➤</button>
              </div>
            </div>
          </aside>

        </div>
      </section>

      <!-- METRIC DETAIL MODAL -->
      <div v-if="isMetricModalVisible && selectedMetric" class="modal" @click.self="closeMetricModal">
        <div class="modal-content metric-modal-content">
          <button class="close-btn" @click="closeMetricModal">×</button>
          <h3>{{ selectedMetric.name }}</h3>
          <div class="metric-details">
            <p><strong>Описание:</strong> {{ selectedMetric.description }}</p>
            <p><strong>Влияние метрики:</strong> {{ selectedMetric.weight }}</p>
            <p><strong>Метрика подтверждена модераторами:</strong> {{ selectedMetric.is_custom ? 'Нет' : 'Да' }}</p>
          </div>
        </div>
      </div>

    </main>
  </div>
</template>

<style scoped>
.app-wrapper {
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: #2c3e50;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.header {
  background: white;
  padding: 1rem 5%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.logo {
  font-size: 1.5rem;
  font-weight: 800;
  color: #005bff;
  cursor: pointer;
}

.logo span { color: #f91155; }

.container { padding: 2rem 5%; max-width: 1200px; margin: 0 auto; }

/* Поиск */
.hero { text-align: center; margin-bottom: 3rem; margin-top: 5rem; }
.search-box {
  display: flex;
  gap: 10px;
  max-width: 700px;
  margin: 0 auto;
  background: white;
  padding: 10px;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.05);
}

input {
  flex: 1;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
}

button {
  padding: 0 25px;
  background: #005bff;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

button:disabled { background: #a0c4ff; }

/* Модалка */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  max-width: 450px;
  width: 90%;
  text-align: center;
  position: relative;
}
.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  justify-content: center;
}
.modal-actions button {
  flex: 1;
}

/* Metric Modal Specifics */
.metric-modal-content {
  text-align: left;
}
.metric-details p {
  margin: 10px 0;
  line-height: 1.6;
}
.metric-details strong {
  color: #005bff;
}
.close-btn {
  position: absolute;
  top: 10px;
  right: 15px;
  background: none;
  border: none;
  font-size: 1.8rem;
  color: #888;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}


/* Лоадер */
.loading-state { text-align: center; margin-top: 10rem; }
.spinner {
  width: 50px; height: 50px; border: 5px solid #f3f3f3; border-top: 5px solid #005bff;
  border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px;
}

/* Отчет */
.report-layout { display: grid; grid-template-columns: 1fr 350px; gap: 30px; }
.card { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
.ai-summary { background: #eef5ff; border-left: 5px solid #005bff; }

/* Overall Score Card */
.overall-score-card {
  text-align: center;
  padding: 25px;
}
.score-display {
  display: flex;
  justify-content: center;
  align-items: baseline;
  margin: 10px 0;
}
.score-value {
  font-size: 4rem;
  font-weight: 800;
  color: #005bff;
}
.score-max {
  font-size: 1.5rem;
  font-weight: 600;
  color: #a0c4ff;
  margin-left: 5px;
}
.score-description {
  font-size: 0.9rem;
  color: #888;
  margin: 0;
}

/* Метрики */
.metric-card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #eee; }
.metric-head {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}
.m-name {
  font-weight: 600;
  color: #333;
  flex-grow: 1;
}
.info-icon {
  font-size: 0.9rem;
  font-weight: bold;
  font-style: italic;
  color: #888;
  cursor: pointer;
  margin-left: 8px;
  border: 1px solid #ccc;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  transition: background-color 0.2s;
}
.info-icon:hover {
  background-color: #eee;
}
.m-score {
  font-weight: bold;
  font-size: 1.1rem;
  color: #005bff;
  margin-left: 15px;
}
.progress-bar { background: #eee; height: 8px; border-radius: 4px; margin: 10px 0; overflow: hidden; }
.fill { background: #00c853; height: 100%; border-radius: 4px; }

/* Чат */
.chat-container {
  background: white; border-radius: 12px; height: 600px; display: flex; flex-direction: column;
  position: sticky; top: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);
}
.chat-messages { flex: 1; overflow-y: auto; padding: 15px; }
.message { margin-bottom: 10px; padding: 10px; border-radius: 8px; max-width: 85%; }
.message.user { background: #005bff; color: white; align-self: flex-end; margin-left: auto; }
.message.ai { background: #f0f2f5; align-self: flex-start; }
.chat-input { padding: 15px; border-top: 1px solid #eee; display: flex; gap: 5px; }

/* Анимации */
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.fade-in { animation: fadeIn 0.5s ease-in; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 900px) {
  .report-layout { grid-template-columns: 1fr; }
  .chat-container { height: 400px; position: static; }
}
</style>
