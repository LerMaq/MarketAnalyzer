<template>
  <div class="app-wrapper">
    <header class="header">
      <div class="logo" @click="$router.push('/')">Ozon<span>AI</span></div>
      <nav class="nav">
        <template v-if="isAuthenticated">
          <button class="link-btn" @click="$router.push('/profile')">Профиль</button>
          <button class="link-btn" @click="logout">Выйти</button>
        </template>
        <template v-else>
          <button class="link-btn" @click="$router.push('/login')">Вход</button>
          <button class="link-btn" @click="$router.push('/register')">Регистрация</button>
        </template>
      </nav>
    </header>

    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import auth from './auth'

onMounted(() => {
  auth.loadUser()
})

const logout = async () => {
  await auth.logout()
  // after logout, send user to home or login
  window.location.href = '/'
}

const isAuthenticated = computed(() => !!auth.user.value)
</script>

<style>
/* Глобальные стили, которые нужны везде */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

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
  position: sticky;
  top: 0;
  z-index: 1000;
}
.logo {
  font-size: 1.5rem;
  font-weight: 800;
  color: #005bff;
  cursor: pointer;
}
.logo span { color: #f91155; }
.container { padding: 2rem 5%; max-width: 1200px; margin: 0 auto; }

.nav { display: flex; gap: 10px; }
.link-btn { background: transparent; border: none; color: #005bff; font-size: 1rem; cursor: pointer; padding: 0.25rem 0.5rem; }
.link-btn:hover { text-decoration: underline; }</style>