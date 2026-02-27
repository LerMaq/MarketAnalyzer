<template>
  <div class="app-wrapper">
    <header class="header">
      <div class="logo" @click="$router.push('/')">Ozon<span>AI</span></div>
    </header>

    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<style>
/* Глобальные стили, которые нужны везде */
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
  cursor: pointer;
}
.logo {
  font-size: 1.5rem;
  font-weight: 800;
  color: #005bff;
}
.logo span { color: #f91155; }
.container { padding: 2rem 5%; max-width: 1200px; margin: 0 auto; }
</style>