<script setup>
import { formatMoney } from '../format.js'

defineProps({
  balances: { type: Array, required: true },
  hasExpenses: { type: Boolean, required: true },
})

const emit = defineEmits(['settle'])
</script>

<template>
  <aside class="panel">
    <h2 class="panel-title">Кто кому должен</h2>

    <p v-if="!hasExpenses" class="panel-empty">
      Добавьте первую трату, и здесь появится, кто кому сколько переводит.
    </p>

    <p v-else-if="balances.length === 0" class="panel-empty">
      Все в расчёте. Никто никому не должен.
    </p>

    <ul v-else class="transfers">
      <li v-for="balance in balances" :key="`${balance.from_user.id}-${balance.to_user.id}`" class="transfer">
        <div class="names">
          {{ balance.from_user.name }}
          <span class="arrow" aria-label="переводит">→</span>
          {{ balance.to_user.name }}
        </div>
        <div class="transfer-bottom">
          <span class="amount money">{{ formatMoney(balance.amount) }}</span>
          <button class="settle" @click="emit('settle', balance)">Оплачено</button>
        </div>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.panel {
  padding: 28px;
  color: #fff;
  background: var(--green);
  border-radius: 18px;
}

.panel-title {
  margin-bottom: 20px;
  color: #bfe0d2;
  font-size: 16px;
  font-weight: 500;
}

.panel-empty {
  margin: 0;
  font-size: 20px;
  line-height: 1.35;
}

.transfers {
  margin: 0;
  padding: 0;
  list-style: none;
}

.transfer {
  padding: 16px 0;
}

.transfer:first-child {
  padding-top: 0;
}

.transfer + .transfer {
  border-top: 1px solid rgba(255, 255, 255, 0.18);
}

.names {
  font-size: 17px;
}

.arrow {
  margin: 0 4px;
  color: #bfe0d2;
}

.transfer-bottom {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 4px;
}

.amount {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.settle {
  padding: 6px 14px;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: var(--radius);
  cursor: pointer;
}

.settle:hover {
  color: var(--green-dark);
  background: #fff;
}

.settle:focus-visible {
  outline-color: #fff;
}
</style>
