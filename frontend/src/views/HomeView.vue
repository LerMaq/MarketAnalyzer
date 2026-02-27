<template>
  <div class="home-wrapper fade-in">
    <div class="hero">
      <h1>Глубокий анализ товаров</h1>
      <p>Узнайте, что на самом деле думают покупатели, с помощью ИИ.</p>
    </div>

    <div class="search-box">
      <input
        v-model="urlOrId"
        placeholder="Вставьте ссылку на Ozon или артикул"
        @keyup.enter="handleSearch"
        :disabled="isLoading"
      />
      <button @click="handleSearch" :disabled="isLoading">
        <span v-if="!isLoading">Анализировать</span>
        <span v-else class="mini-spinner"></span>
      </button>
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
          <button @click="$router.push(`/product/${urlOrId}/${v.id}`)" class="open-btn">
            Открыть отчет
          </button>
        </div>

        <div class="version-card update-card" @click="startNewTask">
          <div class="plus-icon">+</div>
          <span>Обновить анализ</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api/client'
import { useRouter } from 'vue-router'

const router = useRouter() // 2. Инициализируем объект router

const urlOrId = ref('')
const versions = ref([])
const isLoading = ref(false)
const taskStatus = ref(null)

const handleSearch = async () => {
  // 1. Проверяем именно urlOrId (как в твоем оригинале)
  if (!urlOrId.value) return

  isLoading.value = true
  // Сбрасываем старые состояния
  versions.value = []

  try {
    // 2. Убедись, что тут urlOrId.value, а не ozonId
    const res = await api.get(`/products/check/${urlOrId.value}`)

    // В новом бэкенде данные приходят в объекте { ozon_id: ..., versions: [] }
    const foundVersions = res.data.versions || []

    if (foundVersions.length > 0) {
      // ТОВАР НАЙДЕН
      versions.value = foundVersions
      isLoading.value = false

      // Если хочешь сразу перекидывать на последний отчет:
      // const latestId = foundVersions[0].id
      // router.push(`/report/${latestId}`)

    } else {
      // ТОВАР НОВЫЙ (бэкенд вернул 200 и пустой массив)
      console.log("Товар новый, запускаем анализ...")
      await startNewTask() // Вызываем твою функцию запуска задачи
    }
  } catch (e) {
    // Если мы здесь, значит либо переменная не определена, либо сеть упала
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

    // ВАЖНО: Проверьте имя поля.
    // Если бэк присылает { task_id: ... }, то пишем res.data.task_id
    const newTaskId = res.data.task_id;

    if (newTaskId) {
      // Запускаем опрос, передавая полученный ID
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

        // Перенаправляем на страницу товара по вашему формату:
        // /product/ОЗОН_ИД/АЙДИ_ПРОДУКТА
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
      // Если это не системная ошибка роутера, а ошибка сети — лучше не сбрасывать интервал сразу
      // clearInterval(interval);
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

/* Поиск */
.search-box {
  display: flex;
  gap: 12px;
  background: white;
  padding: 12px;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 91, 255, 0.1);
  margin-bottom: 3rem;
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

/* Версии */
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
  width: 40px; height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #005bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin { 100% { transform: rotate(360deg); } }
.fade-in { animation: fadeIn 0.6s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>