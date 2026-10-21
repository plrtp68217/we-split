<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import { formatMoney } from '../format.js'
import ExpenseForm from '../components/ExpenseForm.vue'
import BalancePanel from '../components/BalancePanel.vue'

const route = useRoute()
const router = useRouter()
const eventId = route.params.id

const event = ref(null)
const members = ref([])
const expenses = ref([])
const balances = ref([])
const allUsers = ref([])
const error = ref('')

const newMemberId = ref('')
const confirmingDelete = ref(false)

// люди, которых ещё нет в событии
const usersToAdd = computed(() => {
  return allUsers.value.filter((user) => !members.value.some((member) => member.id === user.id))
})

// новые траты сверху
const sortedExpenses = computed(() => {
  return [...expenses.value].sort((a, b) => b.id - a.id)
})

const total = computed(() => {
  let sum = 0
  for (const expense of expenses.value) {
    sum += Number(expense.amount)
  }
  return sum
})

async function load() {
  try {
    event.value = await api.get(`/events/${eventId}`)
    members.value = await api.get(`/events/${eventId}/users`)
    expenses.value = await api.get(`/events/${eventId}/expenses`)
    balances.value = await api.get(`/events/${eventId}/balances`)
    allUsers.value = await api.get('/users/')
  } catch (e) {
    error.value = e.message
  }
}

// выполняет действие, показывает ошибку, если она есть, и обновляет данные
async function run(action) {
  error.value = ''
  try {
    await action()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

function addMember() {
  run(async () => {
    await api.post(`/events/${eventId}/users`, { user_id: Number(newMemberId.value) })
    newMemberId.value = ''
  })
}

function removeMember(userId) {
  run(() => api.delete(`/events/${eventId}/users/${userId}`))
}

function deleteExpense(expenseId) {
  run(() => api.delete(`/expenses/${expenseId}`))
}

function settle(balance) {
  run(() => api.post(`/events/${eventId}/settlements`, {
    from_user_id: balance.from_user.id,
    to_user_id: balance.to_user.id,
  }))
}

async function deleteEvent() {
  try {
    await api.delete(`/events/${eventId}`)
    router.push('/')
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <RouterLink to="/" class="back small">Все события</RouterLink>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="event">
      <div class="page-head">
        <div>
          <h1>{{ event.name }}</h1>
          <p v-if="expenses.length" class="muted total">
            Потрачено всего <span class="money">{{ formatMoney(total) }}</span>
          </p>
        </div>
      </div>

      <section class="section">
        <h2>Участники</h2>
        <div class="members">
          <div class="chips">
            <span v-for="member in members" :key="member.id" class="chip">
              {{ member.name }}
              <button class="chip-remove" :aria-label="`Убрать из события: ${member.name}`" @click="removeMember(member.id)">
                ×
              </button>
            </span>
          </div>

          <form v-if="usersToAdd.length" class="add-member" @submit.prevent="addMember">
            <select v-model="newMemberId" required aria-label="Кого добавить">
              <option value="" disabled>Добавить участника</option>
              <option v-for="user in usersToAdd" :key="user.id" :value="user.id">{{ user.name }}</option>
            </select>
            <button class="button button-quiet" :disabled="!newMemberId">Добавить</button>
          </form>
        </div>
      </section>

      <div class="layout">
        <div>
          <section class="section">
            <h2>Новая трата</h2>
            <ExpenseForm :event-id="eventId" :members="members" @created="load" />
          </section>

          <section class="section">
            <h2>Траты</h2>

            <p v-if="expenses.length === 0" class="empty">Трат пока нет.</p>

            <ul v-else class="list">
              <li v-for="expense in sortedExpenses" :key="expense.id" class="list-row expense">
                <div class="expense-main">
                  <div class="expense-name">{{ expense.name }}</div>
                  <div class="muted small">Плательщик: {{ expense.payer.name }}</div>
                  <div v-if="expense.debts.length" class="small debts">
                    Должны:
                    <span
                      v-for="debt in expense.debts"
                      :key="debt.id"
                      class="debt"
                      :class="{ settled: debt.is_settled }"
                      :title="debt.is_settled ? 'Оплачено' : ''"
                    >
                      {{ debt.debtor.name }} <span class="money">{{ formatMoney(debt.amount) }}</span>
                    </span>
                  </div>
                </div>

                <div class="expense-side">
                  <span class="expense-amount money">{{ formatMoney(expense.amount) }}</span>
                  <button class="button button-danger button-small" @click="deleteExpense(expense.id)">Удалить</button>
                </div>
              </li>
            </ul>
          </section>
        </div>

        <BalancePanel
          class="balance"
          :balances="balances"
          :has-expenses="expenses.length > 0"
          @settle="settle"
        />
      </div>

      <section class="danger-zone">
        <div v-if="confirmingDelete" class="confirm">
          <span>Удалить событие вместе со всеми тратами?</span>
          <button class="button button-red button-small" @click="deleteEvent">Удалить</button>
          <button class="button button-quiet button-small" @click="confirmingDelete = false">Отмена</button>
        </div>
        <button v-else class="button button-danger button-small" @click="confirmingDelete = true">
          Удалить событие
        </button>
      </section>
    </template>
  </main>
</template>

<style scoped>
.back {
  display: inline-block;
  margin-bottom: 20px;
  color: var(--muted);
  text-decoration: none;
}

.back:hover {
  color: var(--ink);
}

.total {
  margin: 10px 0 0;
  font-size: 18px;
}

.members {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 24px;
}

.chip {
  cursor: default;
}

.add-member {
  display: flex;
  gap: 8px;
}

.add-member select {
  width: auto;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: 40px;
  align-items: start;
}

.balance {
  position: sticky;
  top: 24px;
  margin-top: 39px;
}

.expense {
  align-items: flex-start;
}

.expense-name {
  font-size: 17px;
  font-weight: 500;
}

.debts {
  display: flex;
  flex-wrap: wrap;
  gap: 2px 12px;
  margin-top: 4px;
}

.settled {
  color: var(--muted);
  text-decoration: line-through;
}

.expense-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.expense-amount {
  font-size: 18px;
  font-weight: 700;
}

.danger-zone {
  padding-top: 24px;
  border-top: 1px solid var(--line);
}

.confirm {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

@media (max-width: 860px) {
  .layout {
    grid-template-columns: 1fr;
    gap: 0;
  }

  /* на телефоне итог важнее всего, поэтому показываем его первым */
  .balance {
    position: static;
    order: -1;
    margin: 0 0 40px;
  }
}
</style>
