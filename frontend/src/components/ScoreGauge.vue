<template>
  <span class="gauge" :style="{ color: color }">{{ score }}/10</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ score: number }>()

const color = computed(() => {
  if (props.score >= 8) return '#f85149'
  if (props.score >= 6) return '#f0c060'
  return '#3fb950'
})
</script>

<style scoped>
.gauge { flex-shrink: 0; font-size: 11px; font-weight: 700; width: 32px; text-align: right; }
</style>
