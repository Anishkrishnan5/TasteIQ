import axios from 'axios'

const localApiUrl = `${window.location.protocol}//${window.location.hostname}:8000`
const client = axios.create({ baseURL: import.meta.env.VITE_API_URL || localApiUrl })

export async function getRecommendations(query, filters = {}) {
  const response = await client.post('/api/recommendations', { query, ...filters })
  return response.data
}
