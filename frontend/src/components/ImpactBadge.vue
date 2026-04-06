<template>
  <span class="badge" :class="sentiment">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ sentiment: 'bullish' | 'bearish' | 'neutral' }>()

const label = computed(() => ({
  bullish: '🟢 Bullish',
  bearish: '🔴 Bearish',
  neutral: '⚪ Neutral',
}[props.sentiment]))
</script>

<style scoped>
.badge { flex-shrink: 0; font-size: 10px; padding: 1px 6px; border-radius: 3px; }
.bullish { background: #0d2a1a; color: #3fb950; border: 1px solid #1a4a2a; }
.bearish { background: #2a0d0d; color: #f85149; border: 1px solid #4a1a1a; }
.neutral { background: #21262d; color: #8b949e; border: 1px solid #30363d; }
</style>
