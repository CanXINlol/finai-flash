<template>
  <div class="analysis-card" v-if="analysis">
    <div class="card-header">
      <ScoreGauge :score="analysis.score" />
      <ImpactBadge :sentiment="analysis.sentiment" />
      <span class="model">{{ analysis.model_used }}</span>
    </div>

    <div class="section">
      <div class="label">Summary</div>
      <div class="value">{{ analysis.summary }}</div>
    </div>

    <div class="section">
      <div class="label">Reasoning</div>
      <div class="value muted">{{ analysis.reasoning }}</div>
    </div>

    <div class="section highlight">
      <div class="label">Trade Suggestion</div>
      <div class="value">{{ analysis.suggestion }}</div>
    </div>

    <div class="section" v-if="analysis.portfolio_note">
      <div class="label">Your Portfolio</div>
      <div class="value accent">{{ analysis.portfolio_note }}</div>
    </div>

    <div class="latency">{{ analysis.latency_ms }}ms</div>
  </div>
  <div v-else class="empty-card">Select a news item and click AI to analyze</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNewsStore } from '../stores/news'
import ImpactBadge from './ImpactBadge.vue'
import ScoreGauge from './ScoreGauge.vue'

const props = defineProps<{ newsId: number }>()
const store = useNewsStore()
const analysis = computed(() => store.analyses[props.newsId] ?? null)
</script>

<style scoped>
.analysis-card { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.card-header { display: flex; align-items: center; gap: 8px; }
.model { margin-left: auto; font-size: 10px; color: #6e7681; }
.section { display: flex; flex-direction: column; gap: 4px; }
.label { font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: #6e7681; }
.value { font-size: 12px; color: #c9d1d9; line-height: 1.5; }
.value.muted { color: #8b949e; }
.value.accent { color: #58a6ff; }
.section.highlight { background: #161b22; border-radius: 6px; padding: 10px; border: 1px solid #30363d; }
.latency { font-size: 10px; color: #6e7681; text-align: right; }
.empty-card { padding: 48px 16px; color: #6e7681; font-size: 12px; text-align: center; }
</style>
