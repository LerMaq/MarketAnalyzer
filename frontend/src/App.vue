<template>
  <div class="app-wrapper">
    <header class="header">
      <router-link to="/" class="logo" @click="handleLogoClick">
        <div class="logo-image">
          <img src="\logo market_analyzer.png" alt="Ozon AI Logo">
        </div>
        Ozon<span>AI</span>
      </router-link>

      <!-- Десктопная навигация -->
      <nav class="nav">
        <template v-if="isAuthenticated">
          <button class="link-btn" @click="$router.push('/tariffs')">Тарифы</button>
          <button class="link-btn" @click="$router.push('/history')">История</button>
          <button class="link-btn" @click="$router.push('/profile')">Профиль</button>
          <button class="link-btn" @click="logout">Выйти</button>
        </template>
        <template v-else>
          <button class="link-btn" @click="$router.push('/login')">Вход</button>
          <button class="link-btn" @click="$router.push('/register')">Регистрация</button>
        </template>
      </nav>

      <!-- Бургер-меню для мобильных -->
      <button
        class="burger-menu"
        :class="{ active: isMobileMenuOpen }"
        @click="toggleMobileMenu"
        aria-label="Меню"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>
    </header>

    <!-- Мобильная навигация -->
    <nav class="mobile-nav" :class="{ active: isMobileMenuOpen }">
      <template v-if="isAuthenticated">
        <button class="link-btn" @click="navigateTo('/tariffs'); toggleMobileMenu()">Тарифы</button>
        <button class="link-btn" @click="navigateTo('/history'); toggleMobileMenu()">История</button>
        <button class="link-btn" @click="navigateTo('/profile'); toggleMobileMenu()">Профиль</button>
        <button class="link-btn" @click="logoutAndCloseMenu">Выйти</button>
      </template>
      <template v-else>
        <button class="link-btn" @click="navigateTo('/login'); toggleMobileMenu()">Вход</button>
        <button class="link-btn" @click="navigateTo('/register'); toggleMobileMenu()">Регистрация</button>
      </template>
    </nav>

    <!-- Overlay для закрытия меню -->
    <div class="overlay" :class="{ active: isMobileMenuOpen }" @click="toggleMobileMenu"></div>

    <Transition name="slide-down">
      <div v-if="activeNotification" class="notify-bar" :class="activeNotification.type">
        <div class="notify-text">
          <strong>{{ activeNotification.title }}</strong>
          <span>{{ activeNotification.message }}</span>
        </div>
        <div class="notify-actions">
          <button
            v-if="activeNotification.actionPath"
            class="notify-btn"
            @click="handleNotificationAction(activeNotification)"
          >
            {{ activeNotification.actionLabel || 'Открыть' }}
          </button>
          <button class="notify-close" @click="dismissNotification(activeNotification.id)">Скрыть</button>
        </div>
      </div>
    </Transition>

    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, computed, ref, watch } from 'vue'
import auth from './auth'
import { useRouter, useRoute } from 'vue-router'
import {
  initTracker,
  notifications,
  navigationRequests,
  dismissNotification,
  consumeNavigationRequest
} from './analysisTracker'

const router = useRouter()
const route = useRoute()
const isMobileMenuOpen = ref(false)

onMounted(() => {
  auth.loadUser()
  initTracker()
})

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const navigateTo = (path) => {
  router.push(path)
}

const handleLogoClick = (event) => {
  if (route.path === '/') {
    event.preventDefault()
    window.location.reload()
  }
}

const logout = async () => {
  await auth.logout()
  window.location.href = '/'
}

const logoutAndCloseMenu = async () => {
  await logout()
  isMobileMenuOpen.value = false
}

const isAuthenticated = computed(() => !!auth.user.value)
const activeNotification = computed(() => notifications.value[0] || null)
const pendingNavigation = computed(() => navigationRequests.value[0] || null)

const handleNotificationAction = (notification) => {
  if (notification?.actionPath) {
    router.push(notification.actionPath)
    dismissNotification(notification.id)
  }
}

watch(pendingNavigation, async (request) => {
  if (!request?.path) return

  try {
    await router.push(request.path)
  } finally {
    consumeNavigationRequest(request.id)
  }
})
</script>

<style>
/* CSS-переменные для адаптивности */
:root {
  --container-padding: 5%;
  --container-max-width: 1200px;
  --header-padding: 1rem;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --border-radius: 8px;
  --transition: all 0.2s ease;
}

/* Глобальные стили, которые нужны везде */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  max-width: 100%;
  overflow-x: hidden;
}

.app-wrapper {
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: #2c3e50;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.header {
  background: white;
  padding: var(--header-padding) var(--container-padding);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.logo {
  display: flex;
  font-size: 2rem;
  font-weight: 800;
  color: #005bff;
  cursor: pointer;
  align-items: center;
  text-decoration: none;
}

.logo img {
  width: 50px;
  height: 50px;
  margin-right: 10px;
}

.logo span {
  color: #f91155;
}

.container {
  padding: var(--spacing-lg) var(--container-padding);
  max-width: var(--container-max-width);
  margin: 0 auto;
}

/* Адаптивная навигация */
.nav {
  display: flex;
  gap: var(--spacing-sm);
}

/* Бургер-меню для мобильных */
.burger-menu {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  z-index: 1001;
}

.burger-menu span {
  display: block;
  width: 24px;
  height: 3px;
  background: #333;
  border-radius: 2px;
  transition: var(--transition);
}

.burger-menu.active span:nth-child(1) {
  transform: rotate(45deg) translate(5px, 5px);
}

.burger-menu.active span:nth-child(2) {
  opacity: 0;
}

.burger-menu.active span:nth-child(3) {
  transform: rotate(-45deg) translate(7px, -6px);
}

/* Мобильная навигация */
.mobile-nav {
  position: fixed;
  top: 0;
  right: -100%;
  width: 70%;
  max-width: 300px;
  height: 100vh;
  background: white;
  box-shadow: -2px 0 10px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  padding: 80px var(--spacing-md) var(--spacing-md);
  gap: var(--spacing-sm);
  transition: right 0.3s ease;
  z-index: 999;
}

.mobile-nav.active {
  right: 0;
}

.mobile-nav .link-btn {
  width: 100%;
  text-align: left;
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  z-index: 998;
  opacity: 0;
  visibility: hidden;
  transition: var(--transition);
}

.overlay.active {
  opacity: 1;
  visibility: visible;
}

.link-btn {
  background: #005bff;
  border: none;
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.75rem 1.25rem;
  border-radius: var(--border-radius);
  box-shadow: 0 2px 4px rgba(0, 91, 255, 0.2);
  transition: var(--transition);
  white-space: nowrap;
}

.link-btn:hover {
  background: #0047cc;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 91, 255, 0.3);
}

/* Адаптивные медиа-запросы */
@media (max-width: 768px) {
  :root {
    --header-padding: 0.75rem;
    --container-padding: 4%;
  }

  .header {
    padding: var(--header-padding) var(--container-padding);
  }

  .logo {
    font-size: 1.5rem;
  }

  .logo img {
    width: 40px;
    height: 40px;
    margin-right: 8px;
  }

  .nav {
    display: none;
  }

  .burger-menu {
    display: flex;
  }

  .container {
    padding: var(--spacing-md) var(--container-padding);
  }

  .link-btn {
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
  }
}

@media (max-width: 360px) {
  :root {
    --container-padding: 3%;
  }

  .logo {
    font-size: 1.3rem;
  }

  .logo img {
    width: 36px;
    height: 36px;
    margin-right: 6px;
  }
}

/* Глобальная анимация fade-in для всех страниц */
.fade-in {
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.35s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}

.notify-bar {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  width: min(720px, calc(100% - 32px));
  background: white;
  border: 1px solid #e6e6e6;
  border-radius: 14px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.12);
  z-index: 1200;
}

.notify-bar.success {
  border-color: #b7e4c7;
  background: #f0fff4;
}

.notify-bar.error {
  border-color: #f5c2c7;
  background: #fff5f5;
}

.notify-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: #222;
}

.notify-text strong {
  font-size: 0.95rem;
}

.notify-text span {
  font-size: 0.9rem;
  color: #555;
}

.notify-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.notify-btn {
  background: #005bff;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.notify-btn:hover {
  background: #0046d5;
}

.notify-close {
  background: #f0f2f5;
  color: #333;
  border: none;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}

.notify-close:hover {
  background: #e4e6e9;
}
</style>


