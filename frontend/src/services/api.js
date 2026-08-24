import axios from 'axios'

const client = axios.create({ baseURL: import.meta.env.VITE_API_URL || window.location.origin })

export async function getRecommendations(query, filters = {}) {
  const response = await client.post('/api/recommendations', { query, ...filters })
  return response.data
}

export async function createProfile(profile) {
  const response = await client.post('/api/profiles', profile)
  return response.data
}

export async function getProfile(profileId) {
  const response = await client.get(`/api/profiles/${profileId}`)
  return response.data
}

export async function getSavedMenuItems(profileId) {
  const response = await client.get(`/api/profiles/${profileId}/saved`)
  return response.data
}

export async function updateProfile(profileId, profile) {
  const response = await client.put(`/api/profiles/${profileId}`, profile)
  return response.data
}

export async function saveMenuItem(profileId, item) {
  const response = await client.post(`/api/profiles/${profileId}/saved`, {
    spoonacular_id: item.spoonacular_id,
    item_name: item.name,
  })
  return response.data
}

export async function removeSavedMenuItem(profileId, sourceId) {
  await client.delete(`/api/profiles/${profileId}/saved/${sourceId}`)
}

export async function chat(message, history, options = {}) {
  const response = await client.post('/api/chat', { message, history, ...options })
  return response.data
}
