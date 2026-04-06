import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface Position {
  id: number
  ticker: string
  name: string
  quantity: number
  cost_basis: number | null
  market: string | null
}

export const usePortfolioStore = defineStore('portfolio', () => {
  const positions = ref<Position[]>([])

  async function fetchPositions() {
    const { data } = await axios.get('/api/v1/portfolio')
    positions.value = data
  }

  async function addPosition(p: Omit<Position, 'id'>) {
    const { data } = await axios.post('/api/v1/portfolio', p)
    positions.value.push(data)
    return data
  }

  async function removePosition(id: number) {
    await axios.delete(`/api/v1/portfolio/${id}`)
    positions.value = positions.value.filter(p => p.id !== id)
  }

  return { positions, fetchPositions, addPosition, removePosition }
})
