<template>
  <div class="tariffs-page fade-in">
    <h2 class="page-title">Тарифы</h2>
    <p class="page-desc">Выберите подходящий план для работы с OzonAI</p>

    <div class="tariffs-grid">
      <!-- Бесплатно -->
      <div class="tariff-card tariff-free">
        <h3 class="card-title">Бесплатно</h3>
        <dl class="params">
          <div class="param-row">
            <dt>Количество анализов товаров</dt>
            <dd>5 / день</dd>
          </div>
          <div class="param-row">
            <dt>Количество сообщений ИИ ассистенту</dt>
            <dd>15 / день</dd>
          </div>
          <div class="param-row">
            <dt>Возможность выбирать ИИ модели</dt>
            <dd>нет</dd>
          </div>
          <div class="param-row">
            <dt>Приоритет на анализ товара</dt>
            <dd>Общая очередь</dd>
          </div>
          <div class="param-row">
            <dt>Глубина анализа отзывов</dt>
            <dd>50 отзывов</dd>
          </div>
        </dl>
        <div class="price">0 рублей / месяц</div>
      </div>

      <!-- Премиум -->
      <div class="tariff-card tariff-premium">
        <span class="badge">{{ isPremium ? 'Ваш план' : 'Рекомендуем' }}</span>
        <h3 class="card-title accent">Премиум</h3>
        <dl class="params">
          <div class="param-row">
            <dt>Количество анализов товаров</dt>
            <dd>10 / день</dd>
          </div>
          <div class="param-row">
            <dt>Количество сообщений ИИ ассистенту</dt>
            <dd>100 / день</dd>
          </div>
          <div class="param-row">
            <dt>Возможность выбирать ИИ модели</dt>
            <dd>да</dd>
          </div>
          <div class="param-row">
            <dt>Приоритет на анализ товара</dt>
            <dd>Без очереди</dd>
          </div>
          <div class="param-row">
            <dt>Глубина анализа отзывов</dt>
            <dd>200 отзывов</dd>
          </div>
        </dl>
        <div class="price accent">300 рублей / месяц</div>
        <button
          v-if="!isPremium"
          class="btn-subscribe"
          @click="openModal"
        >
          Оформить подписку
        </button>
      </div>
    </div>

    <!-- Модальное окно оплаты -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h3>Оформление подписки Премиум</h3>
        <p class="modal-summary">Сумма к оплате: 300 ₽</p>
        <div class="modal-field">
          <label>Способ оплаты</label>
          <select v-model="paymentMethod">
            <option value="card">Карты РФ</option>
            <option value="sbp">СБП</option>
          </select>
        </div>
        <div class="modal-field">
          <label>Сумма для пополнения (₽)</label>
          <input v-model.number="amount" type="number" min="300" placeholder="300" />
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeModal">Отмена</button>
          <button class="btn-pay" @click="submitPayment" :disabled="!amount || amount < 300">
            Пополнить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/client'
import auth from '../auth'

const showModal = ref(false)
const paymentMethod = ref('card')
const amount = ref(300)

const profile = ref(null)

const isFree = computed(() => !profile.value?.tariff || profile.value.tariff === 'free')
const isPremium = computed(() => profile.value?.tariff === 'premium')

const loadProfile = async () => {
  try {
    const res = await api.get('/user/me')
    profile.value = res.data
  } catch (e) {
    profile.value = null
  }
}

const openModal = () => {
  amount.value = 300
  paymentMethod.value = 'card'
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const submitPayment = async () => {
  if (!amount.value || amount.value < 300) return
  try {
    await api.post('/user/subscribe', { amount: amount.value })
    await auth.loadUser()
    await loadProfile()
    closeModal()
    alert('Подписка оформлена! Лимиты обновлены.')
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка при оплате')
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.tariffs-page {
  max-width: 900px;
  margin: 40px auto;
  padding: 0 20px;
}

.page-title {
  text-align: center;
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 8px;
}

.page-desc {
  text-align: center;
  color: #666;
  margin-bottom: 40px;
}

.tariffs-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  justify-content: center;
  align-items: start;
}

@media (max-width: 720px) {
  .tariffs-grid {
    grid-template-columns: 1fr;
  }
}

.tariff-card {
  background: white;
  border-radius: 12px;
  padding: 28px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 2px solid #e0e0e0;
  position: relative;
}

.tariff-premium {
  border-color: #005bff;
  background: linear-gradient(to bottom, rgba(0, 91, 255, 0.03) 0%, white 100%);
}

.badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: #005bff;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.card-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 20px 0;
}

.card-title.accent {
  color: #005bff;
}

.params {
  margin: 0 0 24px 0;
  padding: 0;
}

.param-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
  font-size: 0.95rem;
}

.param-row:last-child {
  border-bottom: none;
}

.param-row dt {
  margin: 0;
  color: #333;
  flex-shrink: 0;
}

.param-row dd {
  margin: 0;
  color: #555;
  font-weight: normal;
  text-align: right;
  flex-shrink: 0;
}

/* Адаптивность для очень узких экранов */
@media (max-width: 480px) {
  .tariffs-page {
    padding: 0 4%;
    margin: 20px auto;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .page-desc {
    font-size: 0.95rem;
    margin-bottom: 30px;
  }
  
  .tariff-card {
    padding: 20px 16px;
  }
  
  .card-title {
    font-size: 1.2rem;
  }
  
  .param-row {
    flex-direction: column;
    gap: 4px;
    align-items: flex-start;
  }
  
  .param-row dd {
    text-align: left;
  }
  
  .modal {
    padding: 20px;
    width: 95%;
  }
  
  .modal-actions {
    flex-direction: column;
  }
  
  .btn-cancel, .btn-pay {
    width: 100%;
  }
}

.price {
  font-size: 1.1rem;
  font-weight: 500;
  color: #333;
  margin: 0 0 16px 0;
}

.tariff-premium .price {
  margin-bottom: 20px;
}

.price.accent {
  color: #005bff;
}

.btn-subscribe {
  width: 100%;
  padding: 14px 24px;
  border-radius: 8px;
  border: none;
  background: #005bff;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-subscribe:hover {
  background: #0047cc;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 28px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.modal-summary {
  color: #666;
  margin-bottom: 20px;
}

.modal-field {
  margin-bottom: 16px;
}

.modal-field label {
  display: block;
  font-weight: 500;
  color: #555;
  margin-bottom: 6px;
}

.modal-field select,
.modal-field input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 8px;
  cursor: pointer;
}

.btn-pay {
  flex: 1;
  padding: 10px;
  border: none;
  background: #005bff;
  color: white;
  border-radius: 8px;
  cursor: pointer;
}

.btn-pay:hover:not(:disabled) {
  background: #0047cc;
}

.btn-pay:disabled {
  background: #aaa;
  cursor: not-allowed;
}
</style>
