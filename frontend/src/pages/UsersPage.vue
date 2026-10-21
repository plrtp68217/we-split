<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api.js'

const users = ref([])
const loaded = ref(false)
const error = ref('')

const name = ref('')
const email = ref('')

// id человека, у которого нажали «Удалить» и ждём подтверждения
const confirmingId = ref(null)

async function load() {
  try {
    users.value = await api.get('/users/')
  } catch (e) {
    error.value = e.message
  }
  loaded.value = true
}

async function addUser() {
  error.value = ''
  try {
    await api.post('/users/', { name: name.value.trim(), email: email.value.trim() })
    name.value = ''
    email.value = ''
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function deleteUser(id) {
  error.value = ''
  try {
    await api.delete(`/users/${id}`)
    confirmingId.value = null
    await load()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-head">
      <h1>Люди</h1>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <section class="section">
      <h2>Добавить человека</h2>
      <form class="form" @submit.prevent="addUser">
        <label class="field">
          Имя
          <input v-model="name" placeholder="Петя" maxlength="50" required />
        </label>
        <label class="field">
          Почта
          <input v-model="email" type="email" placeholder="petya@example.com" required />
        </label>
        <button class="button">Добавить</button>
      </form>
    </section>

    <section class="section">
      <h2>Все люди</h2>

      <p v-if="loaded && users.length === 0" class="empty">
        Здесь пока никого нет. Добавьте себя и друзей, с которыми делите расходы.
      </p>

      <ul v-else class="list">
        <li v-for="user in users" :key="user.id" class="list-row">
          <div>
            <div class="user-name">{{ user.name }}</div>
            <div class="muted small">{{ user.email }}</div>
          </div>

          <div v-if="confirmingId === user.id" class="confirm">
            <span class="small muted">Траты и долги тоже удалятся</span>
            <button class="button button-red button-small" @click="deleteUser(user.id)">Удалить</button>
            <button class="button button-quiet button-small" @click="confirmingId = null">Отмена</button>
          </div>
          <button v-else class="button button-danger button-small" @click="confirmingId = user.id">
            Удалить
          </button>
        </li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
.user-name {
  font-weight: 500;
}

.confirm {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}
</style>
