import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'

import App from './App.vue'
import HomeView from './views/HomeView.vue'
import PickupView from './views/PickupView.vue'
import 'element-plus/dist/index.css'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: PickupView },
    { path: '/pickup/:code?', component: HomeView },
    { path: '/share/:code?', component: HomeView }
  ]
})

createApp(App).use(router).use(ElementPlus).mount('#app')
