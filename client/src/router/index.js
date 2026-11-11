import { createRouter, createWebHistory } from 'vue-router'
import Live from '../views/Live.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'live', component: Live },
  ],
})