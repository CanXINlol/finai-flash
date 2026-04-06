<template>
  <div class="news-feed">
    <div
      v-for="item in store.items"
      :key="item.id"
      class="news-row"
      :class="{ analyzed: !!store.analyses[item.id] }"
      @click="selectNews(item.id)"
    >
      <span class="time">{{ fmtTime(item.pub_time) }}</span>
      <span class="source-badge" :class="item.source">{{ item.source }}</span>

      <span class="title">{{ item.title }}</span>

      <template v-if="store.analyses[item.id]">
        <ImpactBadge :sentiment="store.analyses[item.id].sentiment" />
        <ScoreGauge :score="store.analyses[item.id].score" />
      </template>
      <button
        v-else
        class="btn-analyze"
        @click.stop="analyze(item.id)"
        :disabled="analyzing === item.id"
      >
        {{ analyzing === item.id ? '...' : 'AI' }}
      </button>
    </div>
    <p v-if="!store.items.length" class="empty">Waiting for news...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, inject } from 'vue'
import { useNewsStore } from '../stores/news'
import ImpactBadge from './ImpactBadge.vue'
import ScoreGauge from './ScoreGauge.vue'

const store = useNewsStore()
const selectNews = inject<(id: number) => void>('selectNews', () => {})
const analyzing = ref<number | null>(null)

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function analyze(id: number) {
  analyzing.value = id
  try { await store.triggerAnalysis(id) } finally { analyzing.value = null }
}
</script>

<style scoped>
.news-feed { padding: 4px 0; }
.news-row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; border-bottom: 1px solid #21262d;
  cursor: pointer; transition: background .1s;
}
.news-row:hover { background: #161b22; }
.news-row.analyzed { border-left: 2px solid #238636; }
.time { flex-shrink: 0; color: #6e7681; font-size: 11px; width: 44px; }
.source-badge {
  flex-shrink: 0; font-size: 10px; padding: 1px 5px; border-radius: 3px;
  background: #21262d; color: #8b949e; text-transform: uppercase;
}
.source-badge.jin10  { background: #1a3a5c; color: #58a6ff; }
.source-badge.cls    { background: #1a3a2a; color: #3fb950; }
.source-badge.reuters{ background: #3a1a1a; color: #f85149; }
.title { flex: 1; color: #c9d1d9; font-size: 12px; line-height: 1.4; }
.btn-analyze {
  flex-shrink: 0; background: #21262d; border: 1px solid #30363d;
  color: #8b949e; padding: 2px 8px; border-radius: 3px; font-size: 11px; cursor: pointer;
}
.btn-analyze:hover { color: #f0c060; border-color: #f0c060; }
.btn-analyze:disabled { opacity: .5; cursor: not-allowed; }
.empty { color: #6e7681; text-align: center; padding: 48px; font-size: 12px; }
</style>
