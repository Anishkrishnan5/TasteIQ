export default function ResultCard({ item, index, saved, canSave, onToggleSaved }) {
  const reasons = item.personalization?.reasons || []
  return (
    <article>
      <div className="card-topline">
        <div className="number">{String(index + 1).padStart(2, '0')}</div>
        {canSave && (
          <button className="save-item" onClick={() => onToggleSaved(item)}>
            {saved ? 'Saved' : 'Save'}
          </button>
        )}
      </div>
      <h3>{item.name}</h3>
      <p>{item.restaurant || 'Menu item'}</p>
      {reasons.length > 0 && <p className="match-reason">Matched: {reasons.join(' · ')}</p>}
      <div className="macros">
        <div><strong>{item.calories != null ? Math.round(item.calories) : '—'}</strong><span>Calories</span></div>
        <div><strong>{item.protein_g != null ? `${Math.round(item.protein_g)}g` : '—'}</strong><span>Protein</span></div>
        <div><strong>{item.carbs_g != null ? `${Math.round(item.carbs_g)}g` : '—'}</strong><span>Carbs</span></div>
        <div><strong>{item.fat_g != null ? `${Math.round(item.fat_g)}g` : '—'}</strong><span>Fat</span></div>
      </div>
      <div className="ingredients"><strong>Ingredients</strong><p>{item.ingredients?.length ? item.ingredients.join(', ') : 'Not provided by the menu source.'}</p></div>
    </article>
  )
}
