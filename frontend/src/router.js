import { createRouter, createWebHistory } from 'vue-router'
import EventsPage from './pages/EventsPage.vue'
import EventPage from './pages/EventPage.vue'
import UsersPage from './pages/UsersPage.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: EventsPage },
    { path: '/events/:id', component: EventPage },
    { path: '/users', component: UsersPage },
  ],
})
