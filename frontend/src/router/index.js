import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '@Homeview.vue';
import LoadingView from '@/views/LoadingView.vue';
import ProductView from '@/views/ProductView.vue';

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/loading/:id', name: 'loading', component: LoadingView, props: true },
  { path: '/product/:id', name: 'product', component: ProductView, props: true },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;