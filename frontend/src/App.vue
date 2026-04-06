<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">⚡ finai-flash</div>
      <div class="status">
        <span :class="['dot', store.connected ? 'live' : 'dead']"></span>
        {{ store.connected ? 'LIVE' : 'RECONNECTING' }}
        <span class="count">{{ store.items.length }} items</span>
      </div>
      <nav>
        <button :class="{ active: tab === 'feed' }" @click="tab = 'feed'">Feed</button>
        <button :class="{ active: tab === 'portfolio' }" @click="tab = 'portfolio'">Portfolio</button>
      </nav>
    </header>

    <main>
      <Dashboard v-if="tab === 'feed'" />
      <Portfolio v-else />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Dashboard from './views/Dashboard.vue'
import Portfolio from './views/Portfolio.vue'
import { useNewsStore } from './stores/news'

const store = useNewsStore()
const tab = ref<'feed' | 'portfolio'>('feed')

onMounted(async () => {
  await store.fetchRecent()
  store.connectWS()
})
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0d1117; color: #c9d1d9; font-family: 'Courier New', monospace; font-size: 13px; }

.app-shell { display: flex; flex-direction: column; height: 100vh; }

.topbar {
  display: flex; align-items: center; gap: 16px;
  padding: 0 16px; height: 44px;
  background: #161b22; border-bottom: 1px solid #30363d;
  flex-shrink: 0;
}
.brand { font-weight: 700; font-size: 15px; color: #f0c060; letter-spacing: .05em; }
.status { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #8b949e; margin-right: auto; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #ef4444; }
.dot.live { background: #22c55e; box-shadow: 0 0 6px #22c55e88; }
.count { margin-left: 8px; color: #58a6ff; }

nav button {
  background: none; border: none; color: #8b949e; cursor: pointer;
  padding: 4px 12px; border-radius: 4px; font-size: 12px;
  transition: all .15s;
}
nav button:hover { color: #c9d1d9; background: #21262d; }
nav button.active { color: #f0c060; background: #21262d; }

main { flex: 1; overflow: hidden; }
</style>
