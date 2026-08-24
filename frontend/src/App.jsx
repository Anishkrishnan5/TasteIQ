import { useEffect, useState } from 'react'
import ChatPanel from './components/ChatPanel'
import ProfilePanel from './components/ProfilePanel'
import ResultCard from './components/ResultCard'
import {
  createProfile,
  getProfile,
  getRecommendations,
  getSavedMenuItems,
  removeSavedMenuItem,
  saveMenuItem,
  updateProfile,
} from './services/api'
import './App.css'

const suggestions = ['high-protein chicken', 'light lunch', 'spicy dinner', 'vegetarian bowl']
const emptyFilters = { max_calories: '', min_protein: '' }
const emptyProfile = {
  display_name: '',
  dietary_preferences: '',
  disliked_ingredients: '',
  favorite_cuisines: '',
}

function profilePayload(profile) {
  return Object.fromEntries(
    Object.entries(profile).map(([key, value]) => [
      key,
      key === 'display_name'
        ? value
        : value.split(',').map((item) => item.trim()).filter(Boolean),
    ]),
  )
}

function profileForm(profile) {
  return {
    display_name: profile.display_name,
    dietary_preferences: profile.dietary_preferences.join(', '),
    disliked_ingredients: profile.disliked_ingredients.join(', '),
    favorite_cuisines: profile.favorite_cuisines.join(', '),
  }
}

function App() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState(emptyFilters)
  const [results, setResults] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [profile, setProfile] = useState(emptyProfile)
  const [profileId, setProfileId] = useState(() => localStorage.getItem('tasteiq-profile-id'))
  const [profileBusy, setProfileBusy] = useState(false)
  const [savedIds, setSavedIds] = useState(new Set())

  useEffect(() => {
    if (!profileId) return
    Promise.all([getProfile(profileId), getSavedMenuItems(profileId)])
      .then(([storedProfile, savedItems]) => {
        setProfile(profileForm(storedProfile))
        setSavedIds(new Set(savedItems.map((item) => item.spoonacular_id)))
      })
      .catch((requestError) => {
        if (requestError.response?.status === 404) {
          localStorage.removeItem('tasteiq-profile-id')
          setProfileId(null)
          setProfile(emptyProfile)
          setSavedIds(new Set())
        }
      })
  }, [profileId])

  async function search(event, suggestedQuery) {
    event?.preventDefault()
    const nextQuery = suggestedQuery || query
    if (!nextQuery.trim()) return
    setQuery(nextQuery)
    setLoading(true)
    setError('')
    try {
      const appliedFilters = Object.fromEntries(
        Object.entries(filters)
          .filter(([, value]) => value !== '')
          .map(([key, value]) => [key, Number(value)]),
      )
      if (profileId) appliedFilters.profile_id = profileId
      const data = await getRecommendations(nextQuery, appliedFilters)
      setResults(data.results)
      setMessage(data.message)
    } catch (requestError) {
      setError(
        requestError.response?.data?.error?.message ||
          'TasteIQ could not reach the API. Make sure the backend is running on port 8000.',
      )
    } finally {
      setLoading(false)
    }
  }

  async function saveProfile(event) {
    event.preventDefault()
    setProfileBusy(true)
    setError('')
    try {
      const payload = profilePayload(profile)
      const saved = profileId
        ? await updateProfile(profileId, payload)
        : await createProfile(payload)
      setProfileId(saved.id)
      localStorage.setItem('tasteiq-profile-id', saved.id)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'TasteIQ could not save your profile.')
    } finally {
      setProfileBusy(false)
    }
  }

  async function toggleSaved(item) {
    if (!profileId) return
    const nextSaved = new Set(savedIds)
    try {
      if (nextSaved.has(item.spoonacular_id)) {
        await removeSavedMenuItem(profileId, item.spoonacular_id)
        nextSaved.delete(item.spoonacular_id)
      } else {
        await saveMenuItem(profileId, item)
        nextSaved.add(item.spoonacular_id)
      }
      setSavedIds(nextSaved)
    } catch {
      setError('TasteIQ could not update your saved meals.')
    }
  }

  return (
    <main>
      <nav><span className="brand">Taste<span>IQ</span></span><span className="status">Grounded menu discovery</span></nav>
      <section className="hero">
        <p className="eyebrow">Eat smarter, not harder</p>
        <h1>Your next favorite meal,<br /><em>matched to you.</em></h1>
        <p className="intro">Describe what you’re craving. TasteIQ searches real menu data and returns focused recommendations in seconds.</p>
        <form onSubmit={search}>
          <div className="query-row">
            <input aria-label="Describe your meal" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Try “spicy chicken”" />
            <button disabled={loading}>{loading ? 'Searching…' : 'Find my meal →'}</button>
          </div>
          <div className="filters" aria-label="Nutrition filters">
            <label>Maximum calories<input type="number" min="1" max="5000" value={filters.max_calories} onChange={(event) => setFilters({ ...filters, max_calories: event.target.value })} placeholder="Any" /></label>
            <label>Minimum protein<input type="number" min="0" max="500" value={filters.min_protein} onChange={(event) => setFilters({ ...filters, min_protein: event.target.value })} placeholder="Any" /><span>grams</span></label>
            {(filters.max_calories || filters.min_protein) && <button type="button" className="clear-filters" onClick={() => setFilters(emptyFilters)}>Clear filters</button>}
            <p>Filtered results include only items with known nutrition data.</p>
          </div>
        </form>
        <div className="suggestions">
          <span>Try</span>{suggestions.map((item) => <button key={item} onClick={(e) => search(e, item)}>{item}</button>)}
        </div>
      </section>

      <ProfilePanel
        profile={profile}
        active={Boolean(profileId)}
        busy={profileBusy}
        onChange={(field, value) => setProfile({ ...profile, [field]: value })}
        onSave={saveProfile}
      />

      <ChatPanel profileId={profileId} filters={filters} />

      {error && <p className="error" role="alert">{error}</p>}
      {message && <section className="results" aria-live="polite">
        <div className="results-heading"><div><p className="eyebrow">TasteIQ picks</p><h2>Matches for you</h2></div><p>{message}</p></div>
        <div className="grid">{results.map((item, index) => (
          <ResultCard
            key={item.id || `${item.name}-${index}`}
            item={item}
            index={index}
            saved={savedIds.has(item.spoonacular_id)}
            canSave={Boolean(profileId)}
            onToggleSaved={toggleSaved}
          />
        ))}</div>
      </section>}
      <footer>Built around your taste. Grounded in menu data.</footer>
    </main>
  )
}

export default App
