import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ProductReportView from '../views/ProductReportView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue') // Ленивая загрузка
  },
  {
    // :article — артикул Ozon, :id — ID записи в БД
    path: '/product/:article/:id',
    name: 'product-report',
    component: ProductReportView,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router