<template>
  <div v-if="product" class="report-container fade-in">
    <header class="report-header">
      <button @click="$router.push('/')" class="back-btn">← К поиску</button>
      <div class="title-section">
        <h1>{{ product.name }}</h1>
        <span class="sku">Артикул: {{ article }}</span>
      </div>
    </header>

    <main class="report-grid">
      <div class="analytics-panel">

        <div class="card score-card">
          <div class="score-info">
            <h3>Общий рейтинг товара</h3>
            <p>На основе анализа отзывов и 10 ключевых метрик</p>
          </div>
          <div class="score-circle">
            <span class="number">{{ Math.round(product.score) }}</span>
            <span class="total">/100</span>
          </div>
        </div>



        <div class="card summary-card">
          <div class="summary-header" @click="toggleSummary">
            <h3><span class="icon">✨</span> Резюме нейросети</h3>
            <button class="expand-btn">
              {{ isSummaryExpanded ? 'Свернуть ▲' : 'Развернуть ▼' }}
            </button>
          </div>

          <div :class="['summary-content', { expanded: isSummaryExpanded }]">
            <p>{{ product.summary?.text }}</p>
          </div>
        </div>
        <div class="metrics-grid">
          <div v-for="pm in product.product_metrics" :key="pm.id" class="metric-item">
            <div class="metric-head">
              <span class="m-name">{{ pm.metric.name }}</span>

              <button @click="openMetricDetails(pm)" class="info-btn">
                <i>i</i>
              </button>

              <span class="m-score" :class="getScoreClass(pm.score)">{{ pm.score }}/100</span>
            </div>

            <div class="m-bar">
              <div
                class="m-fill"
                :style="{ width: pm.score + '%', backgroundColor: getScoreColor(pm.score) }"
              ></div>
            </div>

            <p class="m-explanation">{{ pm.explanation }}</p>
          </div>
        </div>
      </div>

      <aside class="chat-panel">
        <div class="chat-container">
          <div class="chat-header">
            <div class="header-info">
              <span class="status-dot"></span>
              <h3>AI Консультант</h3>
            </div>

            <div class="header-actions">
              <button @click="startNewChat" class="icon-btn" title="Новый чат">
                <span>+</span>
              </button>

              <div class="dropdown-wrapper">
                <button @click="isChatsMenuOpen = !isChatsMenuOpen" class="icon-btn" :class="{active: isChatsMenuOpen}">
                  <span class="icon">📜</span>
                </button>

                <div v-if="isChatsMenuOpen" class="chats-dropdown">
                  <div class="dropdown-header">Ваши чаты</div>
                  <div v-if="myChats.length === 0" class="empty-list">Чатов пока нет</div>
                  <div
                    v-for="c in myChats"
                    :key="c.id"
                    @click="loadChatMessages(c.id)"
                    class="chat-item"
                    :class="{selected: c.id === chatId}"
                  >
                    <span class="chat-title">{{ c.title || 'Чат без названия' }}</span>
                    <span class="chat-date">{{ new Date(c.created_at).toLocaleDateString() }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="chat-messages" ref="chatBox">
            <div v-if="messages.length === 0" class="empty-chat">
              Спросите что-нибудь о товаре, например: <br/>
              <em>"Есть ли проблемы с активацией в моем регионе?"</em>
            </div>
            <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
              <div class="bubble">{{ msg.content }}</div>
            </div>
            <div v-if="streamingText" class="message assistant">
              <div class="bubble streaming">{{ streamingText }}</div>
            </div>
          </div>

          <div class="chat-input-area">
            <input
              v-model="userInput"
              @keyup.enter="sendMessage"
              placeholder="Введите вопрос..."
              :disabled="isStreaming"
            />
            <button @click="sendMessage" :disabled="isStreaming || !userInput">
              <span v-if="!isStreaming">➤</span>
              <span v-else class="loader"></span>
            </button>
          </div>
        </div>
      </aside>
    </main>
  </div>
  <div v-else class="loading-full">
    <div class="spinner"></div>
    <p>Загрузка отчета...</p>
  </div>

  <Transition name="fade">
  <div v-if="selectedMetric" class="modal-overlay" @click.self="closeMetricDetails">
    <div class="modal-content">
      <header class="modal-header">
        <h3>{{ selectedMetric.metric.name }}</h3>
        <button @click="closeMetricDetails" class="close-modal">&times;</button>
      </header>

      <div class="modal-body">
        <section class="info-section">
          <h4>Что это значит?</h4>
          <p>{{ selectedMetric.metric.description }}</p>
        </section>

        <section class="info-section">
          <h4>Почему такая оценка?</h4>
          <p>{{ selectedMetric.explanation }}</p>
        </section>

        <div class="modal-score-bar">
          <span>Оценка: {{ selectedMetric.score }}/100</span>
          <div class="m-bar">
            <div class="m-fill" :style="{ width: selectedMetric.score + '%', backgroundColor: getScoreColor(selectedMetric.score) }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</Transition>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import api from '../api/client'

const props = defineProps(['article', 'id'])
const product = ref(null)
const messages = ref([])
const userInput = ref('')
const streamingText = ref('')
const isStreaming = ref(false)
const chatBox = ref(null)
const chatId = ref(null)
const myChats = ref([]) // Список всех чатов по этому товару
const isChatsMenuOpen = ref(false) // Состояние выпадающего списка
const selectedMetric = ref(null); // Метрика для модального окна
const isSummaryExpanded = ref(false);

const toggleSummary = () => {
  isSummaryExpanded.value = !isSummaryExpanded.value;
};


const openMetricDetails = (pm) => {
  selectedMetric.value = pm;
};

const closeMetricDetails = () => {
  selectedMetric.value = null;
};

// Функция загрузки сообщений конкретного чата
const loadChatMessages = async (id) => {
  try {
    const res = await api.get(`/chat/${id}/messages`)
    chatId.value = id
    messages.value = res.data.map(m => ({
      role: m.role,
      content: m.message_text
    }))
    isChatsMenuOpen.value = false
    scrollToBottom()
  } catch (e) {
    console.error("Ошибка загрузки сообщений:", e)
  }
}

// Функция инициализации нового чата (очистка экрана)
const startNewChat = () => {
  chatId.value = null
  messages.value = []
  isChatsMenuOpen.value = false
}

onMounted(async () => {
  try {
    const res = await api.get(`/products/report/${props.id}`)
    product.value = res.data

    // Загружаем список чатов
    const chatListRes = await api.get(`/chat/my-chats/${props.id}`)
    myChats.value = chatListRes.data

    // Если чаты есть, загружаем сообщения самого последнего (первого в списке)
    if (myChats.value.length > 0) {
      await loadChatMessages(myChats.value[0].id)
    }
  } catch (e) {
    console.error("Ошибка загрузки отчета:", e)
  }
})

const getScoreColor = (s) => {
  if (s > 75) return '#00c853'
  if (s > 50) return '#ff9100'
  return '#ff5252'
}

const getScoreClass = (s) => {
  if (s > 75) return 'high'
  if (s > 50) return 'med'
  return 'low'
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatBox.value) {
    chatBox.value.scrollTop = chatBox.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!userInput.value || isStreaming.value) return

  const text = userInput.value
  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  isStreaming.value = true
  scrollToBottom()

  try {
    // 1. Создание чата, если его нет
    if (!chatId.value) {
      const createRes = await api.post('/chat/create', {
        product_id: Number(props.id),
        title: text.substring(0, 30) + "..."
      });
      chatId.value = createRes.data.id;
      myChats.value.unshift(createRes.data);
    }

    // 2. Запрос к стриму
    const response = await fetch(`${import.meta.env.VITE_API_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        chat_id: Number(chatId.value),
        message_text: text
      })
    })

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Ошибка стрима:", errorData);
      isStreaming.value = false;
      return;
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let leftover = ''; // ОБЯЗАТЕЛЬНО ОБЪЯВЛЯЕМ ЗДЕСЬ

    while (true) {
      const { value, done } = await reader.read()

      // Если поток завершен, обрабатываем последний кусок и выходим
      if (done) {
        if (streamingText.value) {
          messages.value.push({ role: 'assistant', content: streamingText.value });
          streamingText.value = '';
        }
        isStreaming.value = false;
        scrollToBottom();
        break;
      }

      // Декодируем и склеиваем с остатком
      const chunk = leftover + decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      // Сохраняем последний (возможно неполный) кусок строки
      leftover = lines.pop() || '';

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue;

        // Обработка маркера завершения
        if (trimmedLine.includes('[DONE]')) {
          // Если в строке с [DONE] был полезный текст, забираем его
          let finalPart = trimmedLine.replace('data: ', '').replace('[DONE]', '').trim();
          if (finalPart) streamingText.value += finalPart;

          messages.value.push({ role: 'assistant', content: streamingText.value });
          streamingText.value = '';
          isStreaming.value = false;
          scrollToBottom();
          return; // Важно: полностью выходим из функции
        }

        // Извлекаем данные
        let content = '';
        if (trimmedLine.startsWith('data: ')) {
          content = trimmedLine.replace('data: ', '');
        } else {
          // Если бэк прислал строку без префикса (как мы видели в Swagger)
          content = trimmedLine;
        }

        // Добавляем контент к результату
        streamingText.value += content;

        await nextTick();
        scrollToBottom();
      }
    }
  } catch (e) {
    console.error("Ошибка при отправке:", e);
    isStreaming.value = false;
  }
}
</script>

<style scoped>
.report-container { max-width: 1300px; margin: 0 auto; padding: 20px; }

.report-header { display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }
.back-btn { background: #eee; color: #333; padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; }
.title-section h1 { font-size: 1.4rem; margin: 0; color: #1a1a1a; line-height: 1.2; }
.sku { color: #888; font-size: 0.9rem; }

.report-grid { display: grid; grid-template-columns: 1fr 380px; gap: 30px; }

.card { background: white; border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid #eee; }

/* Score Card */
.score-card { display: flex; justify-content: space-between; align-items: center; background: #005bff; color: white; }
.score-circle { text-align: right; }
.score-circle .number { font-size: 3.5rem; font-weight: 800; }
.score-circle .total { font-size: 1.2rem; opacity: 0.7; }

/* Summary */
.summary-card { border-left: 5px solid #005bff; background: #f0f6ff; }
.summary-card h3 { margin-top: 0; display: flex; align-items: center; gap: 8px; color: #005bff; }
.summary-card p {
  line-height: 1.6;
  color: #333;
  white-space: pre-line;
  margin: 0;
}

/* Metrics */
.metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.metric-item { background: white; padding: 20px; border-radius: 12px; border: 1px solid #f0f0f0; }
.metric-head {
  display: flex;
  align-items: flex-start; /* Выравнивание всех элементов по верхней линии */
  gap: 12px;
  margin-bottom: 12px;
}
.m-name {
  font-weight: 700;
  line-height: 1.2;
  font-size: 0.95rem;
  color: #1a1a1a;
  flex: 0 1 auto; /* Название занимает только нужное место, но может сжиматься */
}
.m-score.high { color: #00c853; }
.m-score.med { color: #ff9100; }
.m-score.low { color: #ff5252; }
.m-score {
  font-weight: 700;
  white-space: nowrap; /* Чтобы оценка не переносилась */
  font-size: 0.95rem;
  line-height: 1.2;
}
.m-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  margin-bottom: 12px;
  overflow: hidden;
}
.m-fill {
  height: 100%;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}
.m-explanation { font-size: 0.85rem; color: #666; line-height: 1.5; }

/* Chat */
.chat-container {
  background: white;
  border-radius: 16px;
  border: 1px solid #eee;
  /* Уменьшаем высоту здесь */
  height: 500px;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 20px;
}
.chat-header { padding: 15px 20px; border-bottom: 1px solid #f0f0f0; display: flex; align-items: center; gap: 10px; }
.status-dot { width: 8px; height: 8px; background: #00c853; border-radius: 50%; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
.message .bubble { padding: 12px 16px; border-radius: 14px; max-width: 90%; line-height: 1.4; font-size: 0.95rem; }
.message.user { align-self: flex-end; }
.message.user .bubble { background: #005bff; color: white; border-bottom-right-radius: 2px; }
.message.assistant { align-self: flex-start; }
.message.assistant .bubble { background: #f0f2f5; color: #1a1a1a; border-bottom-left-radius: 2px; }
.streaming { border-right: 2px solid #005bff; animation: blink 1s infinite; }

.chat-input-area { padding: 15px; border-top: 1px solid #f0f0f0; display: flex; gap: 10px; }
.chat-input-area input { flex: 1; border: 1px solid #eee; padding: 12px; border-radius: 10px; outline: none; }
.chat-input-area button { background: #005bff; color: white; border: none; width: 45px; border-radius: 10px; cursor: pointer; }

@keyframes blink { 50% { border-color: transparent; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.fade-in { animation: fadeIn 0.5s ease-out; }

@media (max-width: 1000px) {
  .report-grid { grid-template-columns: 1fr; }
  .metrics-grid { grid-template-columns: 1fr; }
}
.chat-header { justify-content: space-between; position: relative; }
.header-info { display: flex; align-items: center; gap: 10px; }
.header-actions { display: flex; gap: 8px; align-items: center; }

.icon-btn {
  background: #f0f2f5; border: none; width: 32px; height: 32px;
  border-radius: 8px; cursor: pointer; display: flex; align-items: center;
  justify-content: center; transition: 0.2s; font-size: 1.1rem;
}
.icon-btn:hover { background: #e4e6e9; }
.icon-btn.active { background: #005bff; color: white; }

.dropdown-wrapper { position: relative; }
.chats-dropdown {
  position: absolute; top: 40px; right: 0; width: 260px;
  background: white; border: 1px solid #eee; border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1); z-index: 100;
  max-height: 400px; overflow-y: auto;
}

.dropdown-header { padding: 12px; font-weight: 700; border-bottom: 1px solid #f0f0f0; font-size: 0.9rem; }
.chat-item {
  padding: 12px; cursor: pointer; display: flex; flex-direction: column;
  gap: 4px; border-bottom: 1px solid #f9f9f9; transition: 0.2s;
}
.chat-item:hover { background: #f0f6ff; }
.chat-item.selected { border-left: 3px solid #005bff; background: #f0f6ff; }
.chat-title { font-size: 0.85rem; color: #1a1a1a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chat-date { font-size: 0.75rem; color: #888; }
.empty-list { padding: 20px; text-align: center; color: #888; font-size: 0.9rem; }

/* Иконка информации */
.m-name-wrapper { display: flex; align-items: center; gap: 8px; }
.info-btn {
  /* margin-left: auto толкает иконку максимально вправо к оценке */
  margin-left: auto;
  margin-top: 1px; /* Тонкая настройка, чтобы i была идеально вровень с текстом */

  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border: none;
  width: 18px;
  height: 18px;
  min-width: 18px;
  border-radius: 50%;
  font-size: 11px;
  font-style: normal;
  color: #888;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.info-btn:hover {
  background: #005bff;
  color: white;
}

/* Модальное окно */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.5); display: flex; align-items: center;
  justify-content: center; z-index: 1000; backdrop-filter: blur(4px);
}
.modal-content {
  background: white; border-radius: 20px; width: 90%; max-width: 500px;
  padding: 30px; position: relative; box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px;
}
.close-modal {
  background: none; border: none; font-size: 28px; cursor: pointer; color: #888;
}
.info-section { margin-bottom: 20px; }
.info-section h4 { margin-bottom: 8px; color: #005bff; font-size: 1rem; }
.info-section p { line-height: 1.6; color: #444; }

.modal-score-bar { margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee; }
.modal-score-bar span { font-weight: bold; display: block; margin-bottom: 8px; }

/* Анимация появления */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.m-title-block {
  display: flex;
  flex-wrap: wrap; /* Если название очень длинное, иконка перенесется вместе с текстом */
  align-items: center;
  gap: 6px;
  flex: 1; /* Позволяет названию занимать всё свободное место до баллов */
}
.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer; /* Делаем весь заголовок кликабельным */
  margin-bottom: 10px;
}
.expand-btn {
  background: none;
  border: none;
  color: #005bff;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 6px;
  transition: background 0.2s;
}
.expand-btn:hover {
  background: rgba(0, 91, 255, 0.1);
}
.summary-content {
  max-height: 100px; /* Высота в свернутом состоянии */
  overflow: hidden;
  transition: max-height 0.5s cubic-bezier(0, 1, 0, 1); /* Плавный переход */
  position: relative;
}
.summary-content.expanded {
  max-height: 2000px; /* Достаточно большое число для полного раскрытия */
  transition: max-height 0.5s ease-in-out;
}
.summary-content:not(.expanded)::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 40px;
  background: linear-gradient(transparent, #f0f6ff); /* Цвет должен совпадать с фоном карточки */
  pointer-events: none;
}
</style>