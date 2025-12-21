<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';

const router = useRouter();
const urlOrId = ref('');
const loading = ref(false);

// Состояние для модалки/диалога, если товар найден
const existingTask = ref(null); 

// Простая функция извлечения ID (цифры из ссылки или просто ввод)
const extractOzonId = (input) => {
  const match = input.match(/(\d{8,12})/);
  return match ? match[0] : input;
};

const startCheck = async () => {
  const ozonId = extractOzonId(urlOrId.value);
  if (!ozonId) return alert('Введите корректную ссылку или ID');

  loading.value = true;
  try {
    const res = await api.get(`/products/check/${ozonId}`);
    
    if (res.data.exists) {
      // Товар уже есть в БД
      existingTask.value = res.data;
    } else {
      // Товара нет, сразу запускаем анализ
      await requestAnalysis(ozonId);
    }
  } catch (e) {
    alert('Ошибка при проверке товара');
  } finally {
    loading.value = false;
  }
};

const requestAnalysis = async (id) => {
  try {
    await api.post('/products/analyze', { url_or_id: id });
    router.push(`/loading/${id}`);
  } catch (e) {
    alert('Не удалось запустить анализ');
  }
};
</script>

<template>
  <div class="home">
    <h1>Анализ товаров Ozon</h1>
    <div class="search-box">
      <input v-model="urlOrId" placeholder="Ссылка на товар или артикул" />
      <button @click="startCheck" :disabled="loading">Анализировать</button>
    </div>

    <div v-if="existingTask" class="modal">
      <p>Этот товар уже анализировался {{ existingTask.date_added }}</p>
      <button @click="router.push(`/product/${existingTask.ozon_id}`)">Посмотреть старый отчет</button>
      <button @click="requestAnalysis(existingTask.ozon_id)">Обновить данные (новый анализ)</button>
    </div>
  </div>
</template>