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
      router.push(`/product/${props.id}`);
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
  <div class="loading-screen">
    <div class="spinner"></div>
    <p>ИИ анализирует отзывы и характеристики товара {{ id }}...</p>
    <p>Это может занять до 1 минуты.</p>
  </div>
</template>