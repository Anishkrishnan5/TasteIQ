import { useState } from 'react'
import { getRecommendations } from './services/api'
import './App.css'

const suggestions = ['high-protein chicken', 'light lunch', 'spicy dinner', 'vegetarian bowl']
const emptyFilters = { max_calories: '', min_protein: '' }

function App() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState(emptyFilters)
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
      const appliedFilters = Object.fromEntries(
        Object.entries(filters)
          .filter(([, value]) => value !== '')
          .map(([key, value]) => [key, Number(value)]),
      )
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

      {error && <p className="error" role="alert">{error}</p>}
      {message && <section className="results" aria-live="polite">
        <div className="results-heading"><div><p className="eyebrow">TasteIQ picks</p><h2>Matches for you</h2></div><p>{message}</p></div>
        <div className="grid">{results.map((item, index) => (
          <article key={item.id || `${item.name}-${index}`}>
            <div className="number">{String(index + 1).padStart(2, '0')}</div>
            <h3>{item.name}</h3>
            <p>{item.restaurant || 'Menu item'}</p>
            <div className="macros">
              <div><strong>{item.calories != null ? Math.round(item.calories) : '—'}</strong><span>Calories</span></div>
              <div><strong>{item.protein_g != null ? `${Math.round(item.protein_g)}g` : '—'}</strong><span>Protein</span></div>
              <div><strong>{item.carbs_g != null ? `${Math.round(item.carbs_g)}g` : '—'}</strong><span>Carbs</span></div>
              <div><strong>{item.fat_g != null ? `${Math.round(item.fat_g)}g` : '—'}</strong><span>Fat</span></div>
            </div>
            <div className="ingredients"><strong>Ingredients</strong><p>{item.ingredients?.length ? item.ingredients.join(', ') : 'Not provided by the menu source.'}</p></div>
          </article>
        ))}</div>
      </section>}
      <footer>Built around your taste. Grounded in menu data.</footer>
    </main>
  )
}

export default App
