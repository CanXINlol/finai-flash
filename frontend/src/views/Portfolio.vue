<template>
  <div class="portfolio-view">
    <div class="toolbar">
      <h2>Positions</h2>
      <button class="btn-add" @click="showForm = !showForm">+ Add</button>
    </div>

    <form v-if="showForm" @submit.prevent="addPosition" class="add-form">
      <input v-model="form.ticker" placeholder="Ticker (e.g. NVDA)" required />
      <input v-model="form.name" placeholder="Name" required />
      <input v-model.number="form.quantity" type="number" placeholder="Quantity" step="any" required />
      <input v-model="form.market" placeholder="Market (US / HK / A-share)" />
      <button type="submit">Save</button>
    </form>

    <table v-if="store.positions.length">
      <thead>
        <tr>
          <th>Ticker</th><th>Name</th><th>Qty</th><th>Market</th><th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in store.positions" :key="p.id">
          <td class="ticker">{{ p.ticker }}</td>
          <td>{{ p.name }}</td>
          <td>{{ p.quantity }}</td>
          <td>{{ p.market || '—' }}</td>
          <td><button class="btn-del" @click="store.removePosition(p.id)">✕</button></td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">No positions yet. Add one to get personalized AI analysis.</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

const store = usePortfolioStore()
const showForm = ref(false)
const form = reactive({ ticker: '', name: '', quantity: 0, market: '' })

onMounted(() => store.fetchPositions())

async function addPosition() {
  await store.addPosition({ ...form, cost_basis: null })
  Object.assign(form, { ticker: '', name: '', quantity: 0, market: '' })
  showForm.value = false
}
</script>

<style scoped>
.portfolio-view { padding: 20px; max-width: 800px; }
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
h2 { color: #f0c060; font-size: 14px; text-transform: uppercase; letter-spacing: .08em; }
.btn-add { background: #1a7f37; color: #fff; border: none; padding: 4px 14px; border-radius: 4px; cursor: pointer; font-size: 12px; }
.add-form { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; padding: 12px; background: #161b22; border-radius: 6px; border: 1px solid #30363d; }
.add-form input { background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.add-form button { background: #238636; color: #fff; border: none; padding: 4px 14px; border-radius: 4px; cursor: pointer; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: .05em; padding: 6px 8px; border-bottom: 1px solid #30363d; }
td { padding: 8px; border-bottom: 1px solid #21262d; font-size: 12px; }
.ticker { color: #58a6ff; font-weight: 700; }
.btn-del { background: none; border: none; color: #6e7681; cursor: pointer; font-size: 12px; }
.btn-del:hover { color: #ef4444; }
.empty { color: #6e7681; font-size: 12px; margin-top: 24px; }
</style>
