import axios from 'axios'

const client = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' })

export async function getRecommendations(query, filters = {}) {
  const response = await client.post('/api/recommendations', { query, ...filters })
  return response.data
}
