<script setup>
import { ref, computed } from 'vue'
import { api } from '../api.js'
import { formatMoney } from '../format.js'

const props = defineProps({
  eventId: { type: [String, Number], required: true },
  members: { type: Array, required: true },
})

const emit = defineEmits(['created'])

const name = ref('')
const amount = ref('')
const payerId = ref('')
const splitType = ref('equal')
// доли при делении вручную: { id пользователя: сумма }
const shares = ref({})
const error = ref('')

// считаем в копейках, чтобы не ловить ошибки округления дробных чисел
function toCents(value) {
  return Math.round(Number(value || 0) * 100)
}

const remainingCents = computed(() => {
  let sharesCents = 0
  for (const member of props.members) {
    sharesCents += toCents(shares.value[member.id])
  }
  return toCents(amount.value) - sharesCents
})

const canSubmit = computed(() => {
  if (!name.value.trim() || toCents(amount.value) <= 0 || !payerId.value) {
    return false
  }
  return splitType.value === 'equal' || remainingCents.value === 0
})

function reset() {
  name.value = ''
  amount.value = ''
  payerId.value = ''
  splitType.value = 'equal'
  shares.value = {}
}

async function submit() {
  error.value = ''

  const body = {
    name: name.value.trim(),
    amount: String(amount.value),
    payer_id: Number(payerId.value),
    split_type: splitType.value,
  }

  if (splitType.value === 'custom') {
    body.shares = []
    for (const member of props.members) {
      if (toCents(shares.value[member.id]) > 0) {
        body.shares.push({ user_id: member.id, amount: String(shares.value[member.id]) })
      }
    }
  }

  try {
    await api.post(`/events/${props.eventId}/expenses`, body)
    reset()
    emit('created')
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <form class="expense-form" @submit.prevent="submit">
    <div class="form">
      <label class="field field-wide">
        За что
        <input v-model="name" placeholder="Продукты, такси, аренда…" maxlength="50" required />
      </label>
      <label class="field">
        Сумма, ₽
        <input v-model="amount" type="number" min="0.01" step="0.01" inputmode="decimal" placeholder="0" required />
      </label>
      <label class="field">
        Кто платил
        <select v-model="payerId" required>
          <option value="" disabled>Выберите</option>
          <option v-for="member in members" :key="member.id" :value="member.id">{{ member.name }}</option>
        </select>
      </label>
    </div>

    <div class="split">
      <span class="split-label">Как делить</span>
      <div class="segmented" role="group">
        <button
          type="button"
          :class="{ active: splitType === 'equal' }"
          :aria-pressed="splitType === 'equal'"
          @click="splitType = 'equal'"
        >
          Поровну
        </button>
        <button
          type="button"
          :class="{ active: splitType === 'custom' }"
          :aria-pressed="splitType === 'custom'"
          @click="splitType = 'custom'"
        >
          Вручную
        </button>
      </div>
    </div>

    <div v-if="splitType === 'custom'" class="shares">
      <label v-for="member in members" :key="member.id" class="share-row">
        <span>{{ member.name }}</span>
        <input v-model="shares[member.id]" type="number" min="0" step="0.01" inputmode="decimal" placeholder="0" />
      </label>
      <p class="small" :class="remainingCents === 0 ? 'muted' : 'remaining'">
        <template v-if="remainingCents === 0">Вся сумма распределена</template>
        <template v-else-if="remainingCents > 0">Осталось распределить {{ formatMoney(remainingCents / 100) }}</template>
        <template v-else>Доли больше суммы на {{ formatMoney(-remainingCents / 100) }}</template>
      </p>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <button class="button" :disabled="!canSubmit">Добавить трату</button>
  </form>
</template>

<style scoped>
.expense-form {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 18px;
  padding: 20px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}

.form {
  width: 100%;
}

.field-wide {
  flex-basis: 100%;
}

.split {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.split-label {
  font-size: 14px;
  color: var(--muted);
}

.segmented {
  display: inline-flex;
  padding: 3px;
  background: var(--bg);
  border-radius: var(--radius);
}

.segmented button {
  padding: 6px 14px;
  font: inherit;
  font-size: 15px;
  color: var(--muted);
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.segmented button.active {
  color: var(--ink);
  background: var(--surface);
  box-shadow: 0 1px 2px rgba(24, 33, 29, 0.12);
}

.shares {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 360px;
}

.share-row {
  display: grid;
  grid-template-columns: 1fr 140px;
  align-items: center;
  gap: 12px;
}

.shares p {
  margin: 4px 0 0;
}

.remaining {
  color: var(--red);
}

.error {
  margin: 0;
  width: 100%;
}
</style>
