<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';

const props = defineProps(['id']);
const router = useRouter();
let timer = null;

const checkStatus = async () => {
  try {
    const res = await api.get(`/products/check/${props.id}`);
    if (res.data.exists) {
      clearInterval(timer);
      router.push(`/product/unknown/${props.id}`);
    }
  } catch (e) {
    console.error("Ошибка опроса статуса");
  }
};

onMounted(() => {
  // Опрашиваем бэкенд каждые 3 секунды
  timer = setInterval(checkStatus, 3000);
});

onUnmounted(() => clearInterval(timer));
</script>

<template>
  <div class="loading-screen fade-in">
    <div class="spinner"></div>
    <p>ИИ анализирует отзывы и характеристики товара {{ id }}...</p>
    <p>Это может занять до 1 минуты.</p>
  </div>
</template>

<style scoped>
.loading-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 20px;
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #005bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.loading-screen p {
  color: #666;
  font-size: 1rem;
  margin: 8px 0;
  max-width: 400px;
  line-height: 1.5;
}

/* Адаптивность для мобильных */
@media (max-width: 480px) {
  .loading-screen {
    min-height: 50vh;
    padding: 15px;
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    margin-bottom: 15px;
  }
  
  .loading-screen p {
    font-size: 0.95rem;
    padding: 0 10px;
  }
}
</style>
