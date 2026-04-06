<template>
  <div class="dashboard">
    <div class="feed">
      <NewsFeed />
    </div>
    <div class="panel" v-if="selectedId">
      <AnalysisCard :news-id="selectedId" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, provide } from 'vue'
import NewsFeed from '../components/NewsFeed.vue'
import AnalysisCard from '../components/AnalysisCard.vue'

const selectedId = ref<number | null>(null)
provide('selectNews', (id: number) => { selectedId.value = id })
</script>

<style scoped>
.dashboard { display: flex; height: 100%; overflow: hidden; }
.feed { flex: 1; overflow-y: auto; border-right: 1px solid #30363d; }
.panel { width: 400px; overflow-y: auto; }
</style>
