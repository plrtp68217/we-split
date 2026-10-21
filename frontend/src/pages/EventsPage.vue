<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '../api.js'

const router = useRouter()

const events = ref([])
const users = ref([])
const loaded = ref(false)
const error = ref('')

const name = ref('')
const selectedIds = ref([])

async function load() {
  try {
    events.value = await api.get('/events/')
    users.value = await api.get('/users/')
  } catch (e) {
    error.value = e.message
  }
  loaded.value = true
}

function toggleUser(id) {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter((selectedId) => selectedId !== id)
  } else {
    selectedIds.value.push(id)
  }
}

async function createEvent() {
  error.value = ''
  try {
    const event = await api.post('/events/', { name: name.value.trim(), user_ids: selectedIds.value })
    router.push(`/events/${event.id}`)
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <div class="page-head">
      <h1>События</h1>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <section class="section">
      <h2>Новое событие</h2>

      <p v-if="loaded && users.length === 0" class="empty">
        Сначала <RouterLink to="/users">добавьте людей</RouterLink>, которые будут делить расходы.
      </p>

      <form v-else class="create" @submit.prevent="createEvent">
        <label class="field">
          Название
          <input v-model="name" placeholder="Например, выходные на даче" maxlength="50" required />
        </label>

        <div class="field">
          Кто участвует
          <div class="chips">
            <button
              v-for="user in users"
              :key="user.id"
              type="button"
              class="chip"
              :class="{ 'chip-selected': selectedIds.includes(user.id) }"
              :aria-pressed="selectedIds.includes(user.id)"
              @click="toggleUser(user.id)"
            >
              {{ user.name }}
            </button>
          </div>
        </div>

        <div>
          <button class="button" :disabled="!name.trim() || selectedIds.length === 0">
            Создать событие
          </button>
        </div>
      </form>
    </section>

    <section class="section">
      <h2>Все события</h2>

      <p v-if="loaded && events.length === 0" class="empty">
        Событий пока нет. Создайте первое, чтобы начать записывать траты.
      </p>

      <ul v-else class="list">
        <li v-for="event in events" :key="event.id">
          <RouterLink :to="`/events/${event.id}`" class="list-row event-link">
            <span class="event-name">{{ event.name }}</span>
            <span class="muted small">Открыть</span>
          </RouterLink>
        </li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
.create {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 640px;
}

/* в колонке .field не должен растягиваться по высоте */
.create .field {
  flex: none;
}

.event-link {
  text-decoration: none;
}

.event-link:hover {
  background: var(--bg);
}

li + li .event-link {
  border-top: 1px solid var(--line);
}

li:first-child .event-link {
  border-radius: var(--radius) var(--radius) 0 0;
}

li:last-child .event-link {
  border-radius: 0 0 var(--radius) var(--radius);
}

.event-name {
  font-size: 18px;
  font-weight: 500;
}
</style>
