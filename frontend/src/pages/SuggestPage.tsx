import { useState } from 'react'
import { api } from '../api'
import type { Meal, SuggestionRequest, SuggestionResponse } from '../types'

const MEAL_TYPES = ['朝食', '昼食', '夕食']

export function SuggestPage() {
  const [form, setForm] = useState<SuggestionRequest>({
    meal_type: '夕食',
    servings: 2,
    user_request: '',
    lookback_days: 3,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SuggestionResponse | null>(null)
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    setSaveState('idle')
    try {
      const suggestion = await api.suggest(form)
      setResult(suggestion)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    if (!result) return
    setSaveState('saving')
    try {
      const meal: Omit<Meal, 'id'> = {
        date: new Date().toISOString().slice(0, 10),
        meal_type: form.meal_type,
        servings: form.servings,
        estimated: true,
        memo: result.reasoning,
        menu: result.dishes.map((d) => ({ name: d.name, role: d.role, recipe_id: null })),
        nutrition_per_serving: result.nutrition_per_serving,
        cost_yen_per_serving: result.estimated_cost_yen_per_serving,
        tags: result.tags,
      }
      await api.createMeal(meal)
      setSaveState('saved')
    } catch {
      setSaveState('error')
    }
  }

  return (
    <div className="page">
      <form className="card suggest-form" onSubmit={handleSubmit}>
        <div className="field-row">
          <label>
            食事
            <select
              value={form.meal_type}
              onChange={(e) => setForm({ ...form, meal_type: e.target.value })}
            >
              {MEAL_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label>
            人数
            <input
              type="number"
              min={1}
              value={form.servings}
              onChange={(e) => setForm({ ...form, servings: Number(e.target.value) })}
            />
          </label>
          <label>
            直近何日を見る
            <input
              type="number"
              min={0}
              value={form.lookback_days}
              onChange={(e) => setForm({ ...form, lookback_days: Number(e.target.value) })}
            />
          </label>
        </div>
        <label>
          食べたいもの・希望(任意)
          <textarea
            placeholder="例: さっぱりしたものが食べたい"
            value={form.user_request}
            onChange={(e) => setForm({ ...form, user_request: e.target.value })}
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? '提案を考え中…' : '献立を提案してもらう'}
        </button>
      </form>

      {error && <p className="error">エラー: {error}</p>}

      {result && (
        <div className="card suggestion-result">
          <h2>提案された献立</h2>
          <ul className="dish-list">
            {result.dishes.map((d, i) => (
              <li key={i}>
                <span className="dish-role">{d.role}</span> {d.name}
              </li>
            ))}
          </ul>

          <h3>調理タイムライン</h3>
          <ol className="timeline">
            {result.timeline.map((step, i) => (
              <li key={i}>
                <strong>{step.dish}</strong>: {step.description}
              </li>
            ))}
          </ol>

          <div className="nutrition-row">
            <span>カロリー: {result.nutrition_per_serving.calories_kcal ?? '-'} kcal</span>
            <span>たんぱく質: {result.nutrition_per_serving.protein_g ?? '-'} g</span>
            <span>脂質: {result.nutrition_per_serving.fat_g ?? '-'} g</span>
            <span>炭水化物: {result.nutrition_per_serving.carb_g ?? '-'} g</span>
            <span>材料費目安: {result.estimated_cost_yen_per_serving ?? '-'} 円/人前</span>
          </div>

          <p className="reasoning">{result.reasoning}</p>

          <button onClick={handleSave} disabled={saveState === 'saving' || saveState === 'saved'}>
            {saveState === 'saved' ? '記録しました' : saveState === 'saving' ? '記録中…' : 'この献立を記録する'}
          </button>
          {saveState === 'error' && <p className="error">記録に失敗しました</p>}
        </div>
      )}
    </div>
  )
}
