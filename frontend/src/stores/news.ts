import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface NewsItem {
  id: number
  title: string
  source: string
  pub_time: string
  is_analyzed: boolean
}

export interface Analysis {
  news_id: number
  score: number
  sentiment: 'bullish' | 'bearish' | 'neutral'
  summary: string
  reasoning: string
  suggestion: string
  portfolio_note: string | null
}

export const useNewsStore = defineStore('news', () => {
  const items = ref<NewsItem[]>([])
  const analyses = ref<Record<number, Analysis>>({})
  const connected = ref(false)
  let ws: WebSocket | null = null

  async function fetchRecent() {
    const { data } = await axios.get('/api/v1/news?limit=100')
    items.value = data.items
  }

  function connectWS() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${proto}://${location.host}/ws`)

    ws.onopen = () => { connected.value = true }
    ws.onclose = () => {
      connected.value = false
      setTimeout(connectWS, 3000) // auto-reconnect
    }
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      if (msg.type === 'news_item') {
        items.value.unshift(msg.data)
        if (items.value.length > 200) items.value.pop()
      } else if (msg.type === 'analysis_done') {
        analyses.value[msg.data.news_id] = msg.data
      }
    }
  }

  async function triggerAnalysis(newsId: number) {
    const { data } = await axios.post(`/api/v1/analysis/${newsId}/trigger`)
    analyses.value[newsId] = data
    return data
  }

  return { items, analyses, connected, fetchRecent, connectWS, triggerAnalysis }
})
