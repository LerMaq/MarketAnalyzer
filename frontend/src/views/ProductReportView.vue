<template>
  <div class="report-page">
    <div v-if="isLoading" class="report-loading-overlay">
      <div class="spinner"></div>
      <p>Загрузка отчета...</p>
    </div>

    <div v-if="product" class="report-container fade-in">
      <header class="report-header">
        <div class="header-row buttons-row">
          <button @click="goBack" class="back-btn">← Назад</button>
          <button 
            v-if="isAdmin" 
            @click="confirmDeleteReport" 
            class="delete-report-btn"
            title="Удалить отчет"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 512 512">
              <g>
                <path d="M 123.20 510.55 C105.11,506.17 91.63,490.76 89.07,471.50 C88.48,467.10 86.43,444.15 84.50,420.50 C76.32,319.81 61.96,147.64 61.74,147.53 C61.61,147.47 59.04,146.31 56.04,144.96 C39.80,137.65 29.07,117.65 31.67,99.58 C34.54,79.64 49.40,64.12 68.61,60.98 C71.85,60.45 91.71,60.01 112.75,60.01 L 151.00 60.00 L 151.00 51.14 C151.00,46.26 151.46,39.85 152.02,36.89 C155.43,18.93 169.93,4.43 187.89,1.02 C195.14,-0.35 316.86,-0.35 324.11,1.02 C342.07,4.43 356.57,18.93 359.98,36.89 C360.54,39.85 361.00,46.26 361.00,51.14 L 361.00 60.00 L 399.25 60.01 C420.29,60.01 440.15,60.45 443.39,60.98 C462.60,64.12 477.46,79.64 480.33,99.58 C482.93,117.65 472.94,136.45 456.26,144.87 L 450.21,147.93 L 449.58,153.71 C448.99,159.14 435.26,325.00 427.50,420.50 C425.57,444.15 423.52,467.10 422.93,471.50 C420.29,491.29 406.05,507.00 387.20,510.90 C379.00,512.60 130.29,512.26 123.20,510.55 ZM 386.68 479.40 C393.41,474.38 391.93,488.58 414.47,212.50 C416.94,182.25 419.15,155.81 419.39,153.75 L 419.81 150.00 L 256.00 150.00 L 92.19 150.00 L 92.61 153.75 C92.85,155.81 95.06,182.25 97.53,212.50 C113.77,411.39 118.98,471.06 120.35,473.72 C122.11,477.12 124.73,479.57 128.02,480.89 C129.63,481.54 175.00,481.82 257.18,481.69 L 383.85 481.50 L 386.68 479.40 ZM 443.40 117.73 C453.45,111.97 453.23,97.87 443.00,92.12 L 439.23 90.00 L 256.00 90.00 L 72.77 90.00 L 69.00 92.12 C58.77,97.87 58.55,111.97 68.60,117.73 L 72.50 119.97 L 256.00 119.97 L 439.50 119.97 L 443.40 117.73 ZM 331.00 51.52 C331.00,40.41 329.19,35.78 323.54,32.47 L 319.32 30.00 L 256.00 30.00 L 192.68 30.00 L 188.46 32.47 C182.81,35.78 181.00,40.41 181.00,51.52 L 181.00 60.00 L 256.00 60.00 L 331.00 60.00 L 331.00 51.52 ZM 173.42 449.54 C170.83,447.98 168.74,445.71 167.69,443.30 C166.35,440.21 164.63,416.57 158.46,316.54 C151.24,199.35 150.96,193.39 152.52,189.31 C155.64,181.13 164.79,177.81 172.85,181.93 C181.07,186.12 180.07,177.57 188.58,315.67 L 196.17 438.83 L 194.17 443.35 C190.58,451.46 181.26,454.23 173.42,449.54 ZM 248.86 449.84 C246.86,448.68 244.27,446.04 243.11,443.98 L 241.00 440.23 L 241.00 316.00 L 241.00 191.77 L 243.12 188.00 C245.59,183.61 251.40,180.00 256.00,180.00 C260.60,180.00 266.41,183.61 268.88,188.00 L 271.00 191.77 L 271.00 316.00 L 271.00 440.23 L 268.88,444.00 C266.38,448.45 260.57,452.01 255.86,451.98 C254.01,451.96 250.86,451.00 248.86,449.84 ZM 323.66 449.89 C320.93,448.45 319.25,446.56 317.83,443.35 L 315.83 438.83 L 323.42 315.67 C332.00,176.43 330.88,185.71 339.67,181.82 C348.11,178.09 356.39,181.22 359.48,189.31 C361.04,193.39 360.76,199.36 353.55,316.54 C345.10,454.02 346.04,445.90 338.07,449.96 C333.07,452.51 328.60,452.49 323.66,449.89 Z" fill="rgba(0,0,0,1)"/>
              </g>
            </svg>
            Удалить отчет
          </button>
        </div>
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
              <div v-if="product.summary?.text"
                   v-html="md.render(product.summary.text)"
                   class="markdown-body">
              </div>
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
          <div class="chat-container" :class="{ 'is-blurred': !isAuthenticated }">
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

            <div v-if="chatError" class="chat-error-banner">
              {{ chatError }}
            </div>

            <div class="chat-messages" ref="chatBox" @scroll="handleScroll">
              <div v-if="messages.length === 0" class="empty-chat">
                Спросите что-нибудь о товаре, например: <br/>
                <em>"{{ randomPlaceholder }}"</em>
              </div>
              <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
                <div class="bubble-wrapper">
                  <div class="bubble markdown-body" v-html="md.render(msg.content)"></div>
                  <span v-if="msg.time" class="msg-time">{{ msg.time }}</span>
                </div>
              </div>

              <div v-if="streamingText" class="message assistant">
                <div class="bubble streaming markdown-body" v-html="md.render(streamingText)"></div>
              </div>
            </div>

            <div class="chat-input-area">
              <input
                v-model="userInput"
                @keyup.enter="sendMessage"
                placeholder="Введите вопрос..."
                :disabled="isStreaming || !!chatError"
              />

              <button v-if="isStreaming" @click="stopGeneration" class="stop-btn" title="Остановить">
                <span class="stop-icon">■</span>
              </button>

              <button v-else @click="sendMessage" :disabled="!userInput || !!chatError">
                <span>➤</span>
              </button>
            </div>

            <div class="model-select-area">
              <select v-model="selectedKeyId" @change="onModelSelect" class="model-select">
                <option :value="null">По умолчанию</option>
                <option v-for="k in userKeys" :key="k.id" :value="k.id">
                  {{ k.model_name }}
                </option>
              </select>
              <button v-if="selectedKeyId !== null" @click="confirmDeleteKey" class="delete-btn" title="Удалить модель">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 512 512">
                  <g>
                    <path d="M 123.20 510.55 C105.11,506.17 91.63,490.76 89.07,471.50 C88.48,467.10 86.43,444.15 84.50,420.50 C76.32,319.81 61.96,147.64 61.74,147.53 C61.61,147.47 59.04,146.31 56.04,144.96 C39.80,137.65 29.07,117.65 31.67,99.58 C34.54,79.64 49.40,64.12 68.61,60.98 C71.85,60.45 91.71,60.01 112.75,60.01 L 151.00 60.00 L 151.00 51.14 C151.00,46.26 151.46,39.85 152.02,36.89 C155.43,18.93 169.93,4.43 187.89,1.02 C195.14,-0.35 316.86,-0.35 324.11,1.02 C342.07,4.43 356.57,18.93 359.98,36.89 C360.54,39.85 361.00,46.26 361.00,51.14 L 361.00 60.00 L 399.25 60.01 C420.29,60.01 440.15,60.45 443.39,60.98 C462.60,64.12 477.46,79.64 480.33,99.58 C482.93,117.65 472.94,136.45 456.26,144.87 L 450.21 147.93 L 449.58 153.71 C448.99,159.14 435.26,325.00 427.50,420.50 C425.57,444.15 423.52,467.10 422.93,471.50 C420.29,491.29 406.05,507.00 387.20,510.90 C379.00,512.60 130.29,512.26 123.20,510.55 ZM 386.68 479.40 C393.41,474.38 391.93,488.58 414.47,212.50 C416.94,182.25 419.15,155.81 419.39,153.75 L 419.81 150.00 L 256.00 150.00 L 92.19 150.00 L 92.61 153.75 C92.85,155.81 95.06,182.25 97.53,212.50 C113.77,411.39 118.98,471.06 120.35,473.72 C122.11,477.12 124.73,479.57 128.02,480.89 C129.63,481.54 175.00,481.82 257.18,481.69 L 383.85 481.50 L 386.68 479.40 ZM 443.40 117.73 C453.45,111.97 453.23,97.87 443.00,92.12 L 439.23 90.00 L 256.00 90.00 L 72.77 90.00 L 69.00 92.12 C58.77,97.87 58.55,111.97 68.60,117.73 L 72.50 119.97 L 256.00 119.97 L 439.50 119.97 L 443.40 117.73 ZM 331.00 51.52 C331.00,40.41 329.19,35.78 323.54,32.47 L 319.32 30.00 L 256.00 30.00 L 192.68 30.00 L 188.46 32.47 C182.81,35.78 181.00,40.41 181.00,51.52 L 181.00 60.00 L 256.00 60.00 L 331.00 60.00 L 331.00 51.52 ZM 173.42 449.54 C170.83,447.98 168.74,445.71 167.69,443.30 C166.35,440.21 164.63,416.57 158.46,316.54 C151.24,199.35 150.96,193.39 152.52,189.31 C155.64,181.13 164.79,177.81 172.85,181.93 C181.07,186.12 180.07,177.57 188.58,315.67 L 196.17 438.83 L 194.17 443.35 C190.58,451.46 181.26,454.23 173.42,449.54 ZM 248.86 449.84 C246.86,448.68 244.27,446.04 243.11,443.98 L 241.00 440.23 L 241.00 316.00 L 241.00 191.77 L 243.12 188.00 C245.59,183.61 251.40,180.00 256.00,180.00 C260.60,180.00 266.41,183.61 268.88,188.00 L 271.00 191.77 L 271.00 316.00 L 271.00 440.23 L 268.88,444.00 C266.38,448.45 260.57,452.01 255.86,451.98 C254.01,451.96 250.86,451.00 248.86,449.84 ZM 323.66 449.89 C320.93,448.45 319.25,446.56 317.83,443.35 L 315.83 438.83 L 323.42 315.67 C332.00,176.43 330.88,185.71 339.67,181.82 C348.11,178.09 356.39,181.22 359.48,189.31 C361.04,193.39 360.76,199.36 353.55,316.54 C345.10,454.02 346.04,445.90 338.07,449.96 C333.07,452.51 328.60,452.49 323.66,449.89 Z" fill="rgba(0,0,0,1)"/>
                  </g>
                </svg>
              </button>
              <button @click="addUserKey">Добавить модель</button>
            </div>

            <!-- Overlay for unauthenticated users -->
            <div v-if="!isAuthenticated" class="chat-overlay">
              <div class="overlay-content">
                <span class="lock-icon">🔒</span>
                <h3>Чат доступен после входа</h3>
                <p>Авторизуйтесь, чтобы задавать вопросы ИИ о товаре</p>
                <button @click="$router.push('/login')" class="login-btn">Войти в аккаунт</button>
              </div>
            </div>
          </div>
        </aside>
      </main>
    </div>

    <!-- Модальные окна -->
    <Transition name="fade">
      <div v-if="selectedMetric" class="modal-overlay" @click.self="closeMetricDetails">
        <div class="modal-content">
          <button @click="closeMetricDetails" class="close-modal modal-close-big">&times;</button>
          <header class="modal-header">
            <h3>{{ selectedMetric.metric.name }}</h3>
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

    <Transition name="fade">
      <div v-if="showDeleteReportConfirm" class="modal-overlay">
        <div class="modal-content delete-confirm-modal">
          <button @click="cancelDeleteReport" class="close-modal modal-close-big">&times;</button>
          <header class="modal-header">
            <h3>Подтверждение удаления</h3>
          </header>

          <div class="modal-body">
            <p>Вы уверены, что хотите удалить этот отчет? Это действие нельзя отменить.</p>

            <div class="modal-actions">
              <button type="button" @click="cancelDeleteReport">Отмена</button>
              <button type="button" @click="submitDeleteReport" class="delete-confirm-btn">Удалить</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showDeleteConfirm" class="modal-overlay">
        <div class="modal-content delete-confirm-modal">
          <button @click="cancelDeleteKey" class="close-modal modal-close-big">&times;</button>
          <header class="modal-header">
            <h3>Подтверждение удаления</h3>
          </header>

          <div class="modal-body">
            <p>Вы уверены, что хотите удалить выбранную модель ИИ? Это действие нельзя отменить.</p>

            <div class="modal-actions">
              <button type="button" @click="cancelDeleteKey">Отмена</button>
              <button type="button" @click="submitDeleteKey" class="delete-confirm-btn">Удалить</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showAddKeyModal" class="modal-overlay">
        <div class="modal-content">
          <button @click="closeAddKeyModal" class="close-modal modal-close-big">&times;</button>
          <header class="modal-header">
            <h3>Добавить пользовательскую модель ИИ</h3>
          </header>

          <div class="modal-body">
            <form @submit.prevent="submitAddKey">
              <div class="form-group">
                <label for="provider_url">URL провайдера:</label>
                <input id="provider_url" v-model="newKeyData.provider_url" type="url" autocomplete="off" required />
              </div>

              <div class="form-group">
                <label for="key">API ключ:</label>
                <input id="key" v-model="newKeyData.key" autocomplete="off" required />
              </div>

              <div class="form-group">
                <label for="model_name">Название модели:</label>
                <input id="model_name" v-model="newKeyData.model_name" autocomplete="off" required />
              </div>

              <div class="modal-actions">
                <button type="button" @click="closeAddKeyModal">Отмена</button>
                <button type="submit">Добавить</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import auth from '../auth'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ breaks: true, linkify: true })
const router = useRouter()
const props = defineProps(['article', 'id'])
const product = ref(null)
const isLoading = ref(true)
const messages = ref([])
const userInput = ref('')
const streamingText = ref('')
const isStreaming = ref(false)
const chatBox = ref(null)
const chatId = ref(null)
const myChats = ref([])
const isChatsMenuOpen = ref(false)
const selectedMetric = ref(null)
const isSummaryExpanded = ref(false)
const abortController = ref(null)
const chatError = ref('')

const userKeys = ref([])
const selectedKeyId = ref(null)

const showAddKeyModal = ref(false)
const newKeyData = ref({
  provider_url: '',
  key: '',
  model_name: ''
})

const showDeleteConfirm = ref(false)
const deleteKeyId = ref(null)

// Delete report
const showDeleteReportConfirm = ref(false)
const deleteReportId = ref(null)

const isAuthenticated = computed(() => !!auth.user.value)
const isAdmin = computed(() => {
  if (!auth.user.value) return false
  return auth.user.value.permissions?.includes('admin.panel') || false
})

const confirmDeleteReport = () => {
  deleteReportId.value = props.id
  showDeleteReportConfirm.value = true
}

const cancelDeleteReport = () => {
  showDeleteReportConfirm.value = false
  deleteReportId.value = null
}

const submitDeleteReport = async () => {
  try {
    await api.delete(`/products/${deleteReportId.value}`)
    alert('Отчет успешно удален')
    // Redirect to home page after successful deletion
    window.location.href = '/'
  } catch (e) {
    console.error('Ошибка удаления отчета:', e)
    alert('Не удалось удалить отчет: ' + (e.response?.data?.detail || 'Ошибка'))
  } finally {
    showDeleteReportConfirm.value = false
    deleteReportId.value = null
  }
}

const syncMessagesWithRetry = async (maxAttempts = 3, delay = 500) => {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      if (!chatId.value) break
      const res = await api.get(`/chat/${chatId.value}/messages`)
      if (res.data && res.data.length > 0) {
        const lastMsg = res.data[res.data.length - 1]
        if (lastMsg.role === 'assistant') {
          messages.value = formatMessages(res.data)
          streamingText.value = ''
          return true
        }
      }
    } catch (e) {
      console.error('Попытка синхронизации не удалась:', e)
    }
    await new Promise(resolve => setTimeout(resolve, delay))
  }
  streamingText.value = ''
  return false
}

const placeholders = [
  "Какие главные недостатки выделяют покупатели?",
  "Стоит ли этот товар своих денег?",
  "Есть ли смысл переплачивать за этот бренд?",
  "Что чаще всего ломается у этого товара?"
]

const randomPlaceholder = ref(placeholders[Math.floor(Math.random() * placeholders.length)])

const formatMessages = (data) => {
  return data.map(m => ({
    role: m.role,
    content: m.message_text,
    time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }))
}

const toggleSummary = () => {
  isSummaryExpanded.value = !isSummaryExpanded.value
}

const openMetricDetails = (pm) => {
  selectedMetric.value = pm
}

const closeMetricDetails = () => {
  selectedMetric.value = null
}

const loadChatMessages = async (id) => {
  try {
    const res = await api.get(`/chat/${id}/messages`)
    chatId.value = id
    messages.value = formatMessages(res.data)
    isChatsMenuOpen.value = false
    scrollToBottom()
  } catch (e) {
    console.error("Ошибка загрузки сообщений:", e)
    const status = e.response?.status
    const detail = e.response?.data?.detail
    if (status === 429) {
      chatError.value = detail || 'Дневной лимит сообщений в чате исчерпан. Попробуйте завтра или обновите тариф в профиле.'
    }
  }
}

const startNewChat = () => {
  chatId.value = null
  messages.value = []
  isChatsMenuOpen.value = false
  chatError.value = ''
}

const goBack = () => {
  // Проверяем, есть ли история навигации
  if (window.history.length > 1) {
    router.back()
  } else {
    // Если истории нет, переходим на главную
    router.push('/')
  }
}

onMounted(async () => {
  try {
    const res = await api.get(`/products/report/${props.id}`)
    product.value = res.data

    const chatListRes = await api.get(`/chat/my-chats/${props.id}`)
    myChats.value = chatListRes.data

    if (myChats.value.length > 0) {
      await loadChatMessages(myChats.value[0].id)
    }

    await loadUserKeys()
  } catch (e) {
    console.error("Ошибка загрузки отчета:", e)
  } finally {
    isLoading.value = false
  }
})

watch(selectedKeyId, (newVal, oldVal) => {
  console.log('selectedKeyId changed from', oldVal, 'to', newVal)
})

const stopGeneration = async () => {
  if (abortController.value) {
    abortController.value.abort()
    isStreaming.value = false
    await syncMessagesWithRetry(3, 500)
  }
}

const loadUserKeys = async () => {
  try {
    const res = await api.get('/chat/keys')
    userKeys.value = res.data
    const active = userKeys.value.find(k => k.is_active)
    selectedKeyId.value = active ? active.id : null
  } catch (e) {
    console.error('Не удалось получить ключи ИИ пользователя:', e)
    const status = e.response?.status
    const detail = e.response?.data?.detail
    if (status === 429) {
      chatError.value = detail || 'Дневной лимит запросов к ИИ исчерпан. Попробуйте завтра или измените тариф.'
    }
  }
}

const onModelSelect = async () => {
  await nextTick()
  const keyId = selectedKeyId.value
  console.log('onModelSelect called, selectedKeyId:', keyId)
  try {
    await api.post('/chat/keys/activate', { key_id: keyId })
    console.log('Request sent successfully with key_id:', keyId)
    userKeys.value.forEach(k => {
      k.is_active = (k.id === keyId)
    })
  } catch (e) {
    console.error('Ошибка при переключении модели:', e)
    const status = e.response?.status
    const detail = e.response?.data?.detail
    if (status === 429) {
      chatError.value = detail || 'Дневной лимит запросов к ИИ исчерпан. Попробуйте завтра или измените тариф.'
    }
  }
}

const addUserKey = async () => {
  openAddKeyModal()
}

const openAddKeyModal = () => {
  showAddKeyModal.value = true
}

const closeAddKeyModal = () => {
  showAddKeyModal.value = false
  newKeyData.value = { provider_url: '', key: '', model_name: '' }
}

const submitAddKey = async () => {
  try {
    await api.post('/chat/keys', newKeyData.value)
    await loadUserKeys()
    closeAddKeyModal()
  } catch (e) {
    console.error('Не удалось добавить ключ ИИ:', e)
    const status = e.response?.status
    const detail = e.response?.data?.detail
    chatError.value = detail || 'Не удалось добавить модель ИИ. Попробуйте ещё раз позже.'
  }
}

const confirmDeleteKey = () => {
  if (selectedKeyId.value === null) return
  deleteKeyId.value = selectedKeyId.value
  showDeleteConfirm.value = true
}

const submitDeleteKey = async () => {
  try {
    await api.delete(`/chat/keys/${deleteKeyId.value}`)
    await loadUserKeys()
    selectedKeyId.value = null
    showDeleteConfirm.value = false
    deleteKeyId.value = null
  } catch (e) {
    console.error('Не удалось удалить ключ ИИ:', e)
    const status = e.response?.status
    const detail = e.response?.data?.detail
    chatError.value = detail || 'Не удалось удалить модель ИИ. Попробуйте ещё раз позже.'
  }
}

const cancelDeleteKey = () => {
  showDeleteConfirm.value = false
  deleteKeyId.value = null
}

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

const userIsScrolling = ref(false)

const handleScroll = () => {
  if (!chatBox.value) return
  const { scrollTop, scrollHeight, clientHeight } = chatBox.value
  userIsScrolling.value = scrollHeight - scrollTop - clientHeight > 100
}

const sendMessage = async () => {
  if (!userInput.value || isStreaming.value) return

  abortController.value = new AbortController()
  chatError.value = ''
  let streamHadError = false

  const text = userInput.value
  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  isStreaming.value = true
  streamingText.value = ''

  await nextTick()
  scrollToBottom()

  try {
    if (!chatId.value) {
      const createRes = await api.post('/chat/create', {
        product_id: Number(props.id),
        title: text.substring(0, 30) + "..."
      })
      chatId.value = createRes.data.id
      myChats.value.unshift(createRes.data)
    }

    const baseURL = import.meta.env.VITE_API_URL || window.location.origin || 'http://localhost:8000'
    const response = await fetch(`${baseURL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      signal: abortController.value.signal,
      body: JSON.stringify({
        chat_id: Number(chatId.value),
        message_text: text
      })
    })

    if (!response.ok || !response.body) {
      if (response.status === 401) {
        chatError.value = 'Для использования чата нужно войти в аккаунт.'
      } else if (response.status === 429) {
        chatError.value = 'Дневной лимит сообщений в чате исчерпан. Попробуйте завтра или обновите тариф.'
      } else {
        chatError.value = 'Не удалось начать ответ ИИ. Попробуйте ещё раз.'
      }
      throw new Error(`Stream request failed with status ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let leftover = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      const chunk = leftover + decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')
      leftover = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) continue

        if (trimmed.includes('[DONE]')) break

        let content = trimmed.startsWith('data: ') ? trimmed.replace('data: ', '') : trimmed
        if (content.startsWith('Error:')) {
          chatError.value = content.replace('Error:', '').trim() || 'Произошла ошибка при получении ответа ИИ. Попробуйте ещё раз.'
          streamHadError = true
          break
        }
        streamingText.value += content

        if (!userIsScrolling.value) {
          await nextTick()
          scrollToBottom()
        }
      }

      if (streamHadError || chunk.includes('[DONE]')) break
    }

    if (streamHadError) {
      streamingText.value = ''
      return
    }

    const finalData = await api.get(`/chat/${chatId.value}/messages`)
    if (finalData.data) {
      messages.value = formatMessages(finalData.data)
    }
    streamingText.value = ''
  } catch (e) {
    console.error("Ошибка стрима:", e)
    if (!chatError.value) {
      chatError.value = 'Произошла ошибка при получении ответа ИИ. Попробуйте ещё раз.'
    }
  } finally {
    isStreaming.value = false
    if (!abortController.value?.signal.aborted) {
       await syncMessagesWithRetry(2, 300)
    }
    await nextTick()
    if (!userIsScrolling.value) scrollToBottom()
  }
}
</script>

<style scoped>
.report-page {
  position: relative;
}

.report-loading-overlay {
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

.report-loading-overlay .spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #005bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

.report-container {
  max-width: 1300px;
  margin: 0 auto;
  padding: 20px;
}

.report-header {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
}

.header-row.buttons-row {
  display: flex;
}

.back-btn {
  background: #eee;
  color: #333;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
}

.title-section h1 {
  font-size: 1.4rem;
  margin: 0;
  color: #1a1a1a;
  line-height: 1.2;
}

.sku {
  color: #888;
  font-size: 0.9rem;
}

.delete-report-btn {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  background: #ff5252;
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.2s;
}

.delete-report-btn:hover {
  background: #ff1744;
}

.report-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 30px;
}

@media (min-width: 1024px) {
  .report-grid {
    grid-template-columns: 1fr 380px;
  }
}

.card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  border: 1px solid #eee;
}

.score-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #005bff;
  color: white;
}

.score-circle {
  text-align: right;
}

.score-circle .number {
  font-size: 3.5rem;
  font-weight: 800;
}

.score-circle .total {
  font-size: 1.2rem;
  opacity: 0.7;
}

.summary-card {
  border-left: 5px solid #005bff;
  background: #f0f6ff;
}

.summary-card h3 {
  margin-top: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #005bff;
}

.summary-card p {
  line-height: 1.6;
  color: #333;
  white-space: pre-line;
  margin: 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

@media (min-width: 768px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.metric-item {
  background: white;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
}

.metric-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.m-name {
  font-weight: 700;
  line-height: 1.2;
  font-size: 0.95rem;
  color: #1a1a1a;
  flex: 0 1 auto;
}

.m-score.high { color: #00c853; }
.m-score.med { color: #ff9100; }
.m-score.low { color: #ff5252; }

.m-score {
  font-weight: 700;
  white-space: nowrap;
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

.m-explanation {
  font-size: 0.85rem;
  color: #666;
  line-height: 1.5;
}

.chat-container {
  background: white;
  border-radius: 16px;
  border: 1px solid #eee;
  height: 500px;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 20px;
  overflow: hidden;
}

@media (max-width: 1023px) {
  .chat-container {
    position: relative;
    top: 0;
    height: 450px;
  }
}

.chat-container.is-blurred > *:not(.chat-overlay) {
  filter: blur(5px);
  pointer-events: none;
  user-select: none;
}

.chat-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 20px;
  text-align: center;
}

.overlay-content {
  background: white;
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 91, 255, 0.15);
  max-width: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.lock-icon {
  font-size: 2.5rem;
  margin-bottom: 5px;
}

.overlay-content h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #1a1a1a;
}

.overlay-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

.login-btn {
  margin-top: 10px;
  background: #005bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s;
}

.login-btn:hover {
  background: #0046d5;
}

.chat-header {
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #00c853;
  border-radius: 50%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.message .bubble {
  padding: 12px 16px;
  border-radius: 14px;
  max-width: 90%;
  line-height: 1.4;
  font-size: 0.95rem;
}

.message.user {
  align-self: flex-end;
}

.message.user .bubble {
  background: #005bff;
  color: white;
  border-bottom-right-radius: 2px;
}

.message.assistant {
  align-self: flex-start;
}

.message.assistant .bubble {
  background: #f0f2f5;
  color: #1a1a1a;
  border-bottom-left-radius: 2px;
}

.streaming {
  border-right: 2px solid #005bff;
  animation: blink 1s infinite;
}

.chat-input-area {
  padding: 15px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 10px;
}

.chat-input-area input {
  flex: 1;
  border: 1px solid #eee;
  padding: 12px;
  border-radius: 10px;
  outline: none;
}

.chat-input-area button {
  background: #005bff;
  color: white;
  border: none;
  width: 45px;
  border-radius: 10px;
  cursor: pointer;
}

.model-select-area {
  padding: 10px 15px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-select-area select,
.model-select {
  flex: 1;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  max-width: 220px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.model-select-area button {
  background: #005bff;
  color: white;
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.delete-btn {
  width: 32px;
  height: 32px;
  display: contents;
  align-items: center;
  font-size: 1.2rem;
}

.modal-close-big {
  position: absolute;
  top: 10px;
  right: 20px;
  font-size: 28px;
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  z-index: 1010;
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
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-modal {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.modal-actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.modal-actions button[type="button"] {
  background: #f0f0f0;
  color: #333;
}

.modal-actions button[type="submit"] {
  background: #005bff;
  color: white;
}

.delete-confirm-btn {
  background: #ff5252 !important;
  color: white;
}

.delete-confirm-btn:hover {
  background: #ff1744 !important;
}

@keyframes blink {
  50% { border-color: transparent; }
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1000px) {
  .report-grid {
    grid-template-columns: 1fr;
  }
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}

.chat-header {
  justify-content: space-between;
  position: relative;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.icon-btn {
  background: #f0f2f5;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: 0.2s;
  font-size: 1.1rem;
}

.icon-btn:hover {
  background: #e4e6e9;
}

.icon-btn.active {
  background: #005bff;
  color: white;
}

.dropdown-wrapper {
  position: relative;
}

.chats-dropdown {
  position: absolute;
  top: 40px;
  right: 0;
  width: 260px;
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  z-index: 100;
  max-height: 400px;
  overflow-y: auto;
}

.dropdown-header {
  padding: 12px;
  font-weight: 700;
  border-bottom: 1px solid #f0f0f0;
  font-size: 0.9rem;
}

.chat-item {
  padding: 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border-bottom: 1px solid #f9f9f9;
  transition: 0.2s;
}

.chat-item:hover {
  background: #f0f6ff;
}

.chat-item.selected {
  border-left: 3px solid #005bff;
  background: #f0f6ff;
}

.chat-title {
  font-size: 0.85rem;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-date {
  font-size: 0.75rem;
  color: #888;
}

.empty-list {
  padding: 20px;
  text-align: center;
  color: #888;
  font-size: 0.9rem;
}

.info-btn {
  margin-left: auto;
  margin-top: 1px;
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

.m-title-block {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
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
  max-height: 100px;
  overflow: hidden;
  transition: max-height 0.5s cubic-bezier(0, 1, 0, 1);
  position: relative;
}

.summary-content.expanded {
  max-height: 2000px;
  transition: max-height 0.5s ease-in-out;
}

.summary-content:not(.expanded)::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 40px;
  background: linear-gradient(transparent, #f0f6ff);
  pointer-events: none;
}

:deep(.markdown-body) {
  font-size: 0.95rem;
  line-height: 1.5;
}

:deep(.markdown-body p) {
  margin-bottom: 8px;
}

:deep(.markdown-body p:last-child) {
  margin-bottom: 0;
}

:deep(.markdown-body ul),
:deep(.markdown-body ol) {
  padding-left: 20px;
  margin: 8px 0;
}

:deep(.markdown-body li) {
  margin-bottom: 4px;
}

:deep(.markdown-body strong) {
  font-weight: 700;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 3px;
}

.message .bubble :deep(p:first-child) {
  margin-top: 0 !important;
}

.message .bubble :deep(p:last-child) {
  margin-bottom: 0 !important;
}

.message .bubble :deep(h1:first-child),
.message .bubble :deep(h2:first-child),
.message .bubble :deep(h3:first-child) {
  margin-top: 0 !important;
}

.message .bubble :deep(p) {
  margin-top: 8px;
  margin-bottom: 8px;
}

.stop-btn {
  background: #ff5252 !important;
  color: white;
}

.stop-icon {
  font-size: 1.2rem;
}

.stop-btn:hover {
  background: #ff1744 !important;
}

.bubble-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 90%;
}

.message.user .bubble-wrapper {
  align-items: flex-end;
}

.message.assistant .bubble-wrapper {
  align-items: flex-start;
}

.msg-time {
  font-size: 0.7rem;
  color: #aaa;
  margin-top: 4px;
  padding: 0 4px;
}
</style>
