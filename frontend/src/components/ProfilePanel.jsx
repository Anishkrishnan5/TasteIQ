const fields = [
  ['favorite_cuisines', 'Favorite cuisines', 'mexican, italian'],
  ['dietary_preferences', 'Diet preferences', 'vegetarian, high_protein'],
  ['disliked_ingredients', 'Disliked ingredients', 'mushroom, olives'],
]

export default function ProfilePanel({ profile, active, busy, onChange, onSave }) {
  return (
    <section className="profile-panel" aria-labelledby="profile-heading">
      <div>
        <p className="eyebrow">Personalization</p>
        <h2 id="profile-heading">Teach TasteIQ what you like</h2>
        <p>
          Preferences rerank grounded results. Disliked ingredients are removed when ingredient data
          is available.
        </p>
      </div>
      <form onSubmit={onSave}>
        <label>
          Profile name
          <input
            value={profile.display_name}
            onChange={(event) => onChange('display_name', event.target.value)}
            placeholder="Your name"
            required
          />
        </label>
        {fields.map(([name, label, placeholder]) => (
          <label key={name}>
            {label}
            <input
              value={profile[name]}
              onChange={(event) => onChange(name, event.target.value)}
              placeholder={placeholder}
            />
          </label>
        ))}
        <button disabled={busy}>{busy ? 'Saving…' : active ? 'Update profile' : 'Create profile'}</button>
        {active && <span className="profile-active">Personalization active</span>}
      </form>
    </section>
  )
}
