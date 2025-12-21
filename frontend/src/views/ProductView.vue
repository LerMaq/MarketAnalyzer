<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api';

const props = defineProps(['id']);
const report = ref(null);
const question = ref('');
const chatHistory = ref([]);
const isSending = ref(false);

onMounted(async () => {
  try {
    const res = await api.get(`/products/report/${props.id}`);
    report.value = res.data;
  } catch (e) {
    alert("Ошибка загрузки отчета");
  }
});

const askAI = async () => {
  if (!question.value) return;
  isSending.value = true;
  
  // Добавляем вопрос пользователя в локальный чат
  chatHistory.value.push({ role: 'user', text: question.value });
  
  try {
    const res = await api.post('/chat/ask', {
      ozon_id: parseInt(props.id),
      question: question.value
    });
    chatHistory.value.push({ role: 'ai', text: res.data.answer });
    question.value = '';
  } catch (e) {
    chatHistory.value.push({ role: 'error', text: 'Ошибка связи с ИИ' });
  } finally {
    isSending.value = false;
  }
};
</script>

<template>
  <div v-if="report" class="product-page">
    <header>
      <h1>{{ report.name }}</h1>
      <p>ID: {{ id }}</p>
    </header>

    <main class="content">
      <div class="report-section">
        <div class="summary">
          <h3>Резюме ИИ</h3>
          <p>{{ report.ai_summary }}</p>
        </div>

        <div class="metrics">
          <div v-for="m in report.metrics" :key="m.metric_name" class="metric-card">
            <div class="label">{{ m.metric_name }}: {{ m.score }}/100</div>
            <div class="bar"><div :style="{ width: m.score + '%' }"></div></div>
          </div>
        </div>
      </div>

      <aside class="chat-section">
        <h3>Задать вопрос по товару</h3>
        <div class="chat-window">
          <div v-for="(msg, i) in chatHistory" :key="i" :class="['msg', msg.role]">
            {{ msg.text }}
          </div>
        </div>
        <div class="chat-input">
          <input v-model="question" @keyup.enter="askAI" placeholder="Напр.: Стоит ли его покупать?" />
          <button @click="askAI" :disabled="isSending">Отправить</button>
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.product-page { display: grid; padding: 20px; }
.content { display: grid; grid-template-columns: 1fr 350px; gap: 30px; }
.chat-window { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; }
.msg.user { text-align: right; color: blue; margin-bottom: 10px; }
.msg.ai { text-align: left; color: green; margin-bottom: 10px; }
.bar { background: #eee; height: 10px; border-radius: 5px; }
.bar div { background: #42b883; height: 100%; border-radius: 5px; }
</style>