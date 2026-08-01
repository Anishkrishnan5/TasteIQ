import { useState } from 'react'
import { getRecommendations } from './services/api'
import './App.css'

const suggestions = ['high-protein chicken', 'light lunch', 'spicy dinner', 'vegetarian bowl']

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function search(event, suggestedQuery) {
    event?.preventDefault()
    const nextQuery = suggestedQuery || query
    if (!nextQuery.trim()) return
    setQuery(nextQuery)
    setLoading(true)
    setError('')
    try {
      const data = await getRecommendations(nextQuery)
      setResults(data.results)
      setMessage(data.message)
    } catch {
      setError('TasteIQ could not reach the API. Make sure the backend is running on port 8000.')
    } finally {
      setLoading(false)
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
          <input aria-label="Describe your meal" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Try “high-protein chicken under 600 calories”" />
          <button disabled={loading}>{loading ? 'Searching…' : 'Find my meal →'}</button>
        </form>
        <div className="suggestions">
          <span>Try</span>{suggestions.map((item) => <button key={item} onClick={(e) => search(e, item)}>{item}</button>)}
        </div>
      </section>

      {error && <p className="error" role="alert">{error}</p>}
      {message && <section className="results" aria-live="polite">
        <div className="results-heading"><div><p className="eyebrow">TasteIQ picks</p><h2>Matches for you</h2></div><p>{message}</p></div>
        <div className="grid">{results.map((item, index) => (
          <article key={item.id || `${item.name}-${index}`}>
            <div className="number">{String(index + 1).padStart(2, '0')}</div>
            <h3>{item.name}</h3>
            <p>{item.restaurant || 'Menu item'}</p>
            <div className="facts">
              {item.calories != null && <span>{Math.round(item.calories)} cal</span>}
              {item.protein_g != null && <span>{Math.round(item.protein_g)}g protein</span>}
              {(item.derived_tags || []).slice(0, 2).map((tag) => <span key={tag}>{tag.replaceAll('_', ' ')}</span>)}
            </div>
          </article>
        ))}</div>
      </section>}
      <footer>Built around your taste. Grounded in menu data.</footer>
    </main>
  )
}

export default App
