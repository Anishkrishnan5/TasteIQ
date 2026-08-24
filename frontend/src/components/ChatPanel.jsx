import { useState } from 'react'
import { chat } from '../services/api'

export default function ChatPanel({ profileId, filters }) {
  const [input, setInput] = useState('')
  const [turns, setTurns] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function sendMessage(event) {
    event.preventDefault()
    const message = input.trim()
    if (!message || busy) return
    const userTurn = { role: 'user', content: message }
    setTurns([...turns, userTurn])
    setInput('')
    setBusy(true)
    setError('')
    try {
      const numericFilters = Object.fromEntries(
        Object.entries(filters)
          .filter(([, value]) => value !== '')
          .map(([key, value]) => [key, Number(value)]),
      )
      const response = await chat(message, turns.slice(-10), {
        ...numericFilters,
        ...(profileId ? { profile_id: profileId } : {}),
      })
      setTurns((current) => [
        ...current,
        {
          role: 'assistant',
          content: response.answer,
          citations: response.citations,
          provider: response.meta.provider,
        },
      ])
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'The grounded assistant is unavailable.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="chat-panel" aria-labelledby="chat-heading">
      <div className="chat-intro">
        <p className="eyebrow">Grounded assistant</p>
        <h2 id="chat-heading">Ask TasteIQ</h2>
        <p>Answers use retrieved menu records only. Every recommendation links back to its source card.</p>
      </div>
      <div className="chat-window">
        <div className="chat-turns" aria-live="polite">
          {turns.length === 0 && <p className="chat-placeholder">Try “What’s a high-protein chicken option?”</p>}
          {turns.map((turn, index) => (
            <div className={`chat-turn ${turn.role}`} key={`${turn.role}-${index}`}>
              <strong>{turn.role === 'user' ? 'You' : 'TasteIQ'}</strong>
              <p>{turn.content}</p>
              {turn.citations?.length > 0 && (
                <ul aria-label="Menu citations">
                  {turn.citations.map((item) => (
                    <li key={item.spoonacular_id}>[{item.spoonacular_id}] {item.name}</li>
                  ))}
                </ul>
              )}
              {turn.provider === 'deterministic' && <small>Local grounded fallback</small>}
            </div>
          ))}
        </div>
        {error && <p className="chat-error" role="alert">{error}</p>}
        <form onSubmit={sendMessage}>
          <input
            aria-label="Ask TasteIQ"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about a meal…"
            maxLength={1000}
          />
          <button disabled={busy}>{busy ? 'Thinking…' : 'Send'}</button>
        </form>
      </div>
    </section>
  )
}
