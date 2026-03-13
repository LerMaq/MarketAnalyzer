import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ProductReportView from '../views/ProductReportView.vue'
import ProfileView from '../views/ProfileView.vue'
import TariffsView from '../views/TariffsView.vue'
import RegisterView from '../views/RegisterView.vue'

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
    path: '/register',
    name: 'register',
    component: RegisterView
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView
  },
  {
    path: '/tariffs',
    name: 'tariffs',
    component: TariffsView
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