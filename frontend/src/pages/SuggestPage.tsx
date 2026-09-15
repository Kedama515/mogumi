import { useEffect, useState } from 'react'
import { api } from '../api'
import { ConsumePanel } from '../components/ConsumePanel'
import { TagInput } from '../components/TagInput'
import type { Meal, MealStatus, SuggestionRequest, SuggestionResponse, UserSettings } from '../types'

const MEAL_TYPES = ['朝食', '昼食', '夕食']
const CUISINE_OPTIONS = ['おまかせ', '和食', '洋食', '中華']

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

function mealToResponse(meal: Meal): SuggestionResponse {
  return {
    meal_id: meal.id,
    dishes: meal.menu.map((d) => ({ name: d.name, role: d.role ?? '', ingredients: d.ingredients })),
    timeline: meal.timeline,
    nutrition_per_serving: meal.nutrition_per_serving,
    estimated_cost_yen_per_serving: meal.cost_yen_per_serving,
    tags: meal.tags,
    reasoning: meal.memo,
    api_usage: { input_tokens: 0, output_tokens: 0, cost_usd: null },
  }
}

export function SuggestPage() {
  const [form, setForm] = useState<SuggestionRequest>({
    meal_type: '夕食',
    servings: 2,
    user_request: '',
    target_date: today(),
    cuisine_preference: null,
    desired_dishes: [],
    desired_ingredients: [],
  })
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [status, setStatus] = useState<MealStatus | null>(null)
  const [overrideOpen, setOverrideOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SuggestionResponse | null>(null)
  const [revealTimeline, setRevealTimeline] = useState(true)
  const [refinementText, setRefinementText] = useState('')
  const [refining, setRefining] = useState(false)
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [batchCooked, setBatchCooked] = useState<Record<number, boolean>>({})
  const [favoritedDishIds, setFavoritedDishIds] = useState<Record<number, boolean>>({})

  async function handleFavorite(mealDishId: number) {
    await api.favoriteDish(mealDishId)
    setFavoritedDishIds((prev) => ({ ...prev, [mealDishId]: true }))
  }

  useEffect(() => {
    api.getSettings().then((s) => {
      setSettings(s)
      setForm((f) => ({ ...f, servings: s.default_servings }))
    })
  }, [])

  async function reloadStatus() {
    const s = await api.getMealStatus(form.target_date, form.meal_type)
    setStatus(s)
    if (s.draft_for_slot) {
      setResult(mealToResponse(s.draft_for_slot))
      setRevealTimeline(true)
    } else if (!s.stale_draft) {
      setResult(null)
    }
  }

  useEffect(() => {
    reloadStatus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.target_date, form.meal_type])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSaveState('idle')
    setBatchCooked({})
    setRefinementText('')
    try {
      const suggestion = await api.suggest(form)
      setResult(suggestion)
      setRevealTimeline(settings?.suggestion_mode !== 'confirm_menu')
      await reloadStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleRefine() {
    if (!result) return
    setRefining(true)
    setError(null)
    try {
      const suggestion = await api.suggest({
        ...form,
        current_menu: result.dishes,
        refinement_request: refinementText,
      })
      setResult(suggestion)
      setRefinementText('')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setRefining(false)
    }
  }

  async function handleSave() {
    if (!result) return
    setSaveState('saving')
    try {
      const batchCookedNames = result.dishes
        .filter((_, i) => batchCooked[i])
        .map((d) => d.name)
      await api.confirmMeal(result.meal_id, batchCookedNames)
      setSaveState('saved')
      await reloadStatus()
    } catch {
      setSaveState('error')
    }
  }

  async function handleDiscardStaleDraft() {
    if (!status?.stale_draft) return
    await api.deleteMeal(status.stale_draft.id)
    await reloadStatus()
  }

  async function handleConfirmStaleDraft() {
    if (!status?.stale_draft) return
    await api.confirmMeal(status.stale_draft.id)
    await reloadStatus()
  }

  if (status?.stale_draft) {
    const d = status.stale_draft
    return (
      <div className="page">
        <div className="card">
          <h2>作成途中の献立があります</h2>
          <p>
            {d.date} {d.meal_type} の献立が下書きのまま残っています。先にこちらを片付けてください。
          </p>
          <ul className="dish-list">
            {d.menu.map((dish, i) => (
              <li key={i}>
                {dish.role && <span className="dish-role">{dish.role}</span>} {dish.name}
              </li>
            ))}
          </ul>
          <div className="field-row">
            <button onClick={handleConfirmStaleDraft}>この内容で登録する</button>
            <button className="ghost" onClick={handleDiscardStaleDraft}>
              削除する
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      {status?.confirmed_meal && (
        <div className="card">
          <p className="muted">
            {form.target_date} の{form.meal_type}はすでに記録されています({status.confirmed_meal.menu
              .map((d) => d.name)
              .join('、')}
            )。新しく考え直す場合はそのまま提案してください。
          </p>
        </div>
      )}

      <form className="card suggest-form" onSubmit={handleSubmit}>
        <div className="field-row">
          <label>
            日付
            <input
              type="date"
              value={form.target_date}
              onChange={(e) => setForm({ ...form, target_date: e.target.value })}
            />
          </label>
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
            和洋中
            <select
              value={form.cuisine_preference ?? 'おまかせ'}
              onChange={(e) =>
                setForm({
                  ...form,
                  cuisine_preference: e.target.value === 'おまかせ' ? null : e.target.value,
                })
              }
            >
              {CUISINE_OPTIONS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
        </div>

        <button
          type="button"
          className="fridge-group-title"
          onClick={() => setOverrideOpen((v) => !v)}
        >
          <span className="fridge-group-arrow">{overrideOpen ? '▼' : '▶'}</span>
          今回だけ人数を変更(普段は個人設定を使用)
        </button>
        {overrideOpen && (
          <div className="field-row">
            <label>
              人数
              <input
                type="number"
                min={1}
                value={form.servings}
                onChange={(e) => setForm({ ...form, servings: Number(e.target.value) })}
              />
            </label>
          </div>
        )}
        <label>
          食べたいメニュー(任意、スペースで区切って追加)
          <TagInput
            value={form.desired_dishes}
            onChange={(tags) => setForm({ ...form, desired_dishes: tags })}
            placeholder="例: カレー"
          />
        </label>
        <label>
          使いたい食材(任意、スペースで区切って追加)
          <TagInput
            value={form.desired_ingredients}
            onChange={(tags) => setForm({ ...form, desired_ingredients: tags })}
            placeholder="例: にんじん"
          />
        </label>
        <label>
          その他の希望(任意)
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
          <div className="dish-tiles">
            {result.dishes.map((d, i) => (
              <div key={i} className="dish-tile">
                <div className="dish-tile-section">
                  <span className="dish-tile-label">メニュー</span>
                  {d.role && <span className="dish-role">{d.role}</span>}
                  <strong>{d.name}</strong>
                </div>
                <div className="dish-tile-section">
                  <span className="dish-tile-label">食材</span>
                  <div className="muted">{d.ingredients.join('、') || '(未記録)'}</div>
                </div>
                <div className="dish-tile-section">
                  <span className="dish-tile-label">備考</span>
                  <label className="muted">
                    <input
                      type="checkbox"
                      checked={Boolean(batchCooked[i])}
                      onChange={(e) =>
                        setBatchCooked((prev) => ({ ...prev, [i]: e.target.checked }))
                      }
                    />
                    作り置き(冷蔵庫に追加)
                  </label>
                </div>
              </div>
            ))}
          </div>

          <div className="inline-form">
            <input
              placeholder="微調整リクエスト(例: もう少し野菜多めで)"
              value={refinementText}
              onChange={(e) => setRefinementText(e.target.value)}
            />
            <button type="button" onClick={handleRefine} disabled={refining}>
              {refining ? '調整中…' : 'この内容で微調整'}
            </button>
          </div>

          {!revealTimeline ? (
            <button type="button" onClick={() => setRevealTimeline(true)}>
              この内容でタイムラインを見る
            </button>
          ) : (
            <>
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

              <button
                onClick={handleSave}
                disabled={saveState === 'saving' || saveState === 'saved'}
              >
                {saveState === 'saved'
                  ? '記録しました'
                  : saveState === 'saving'
                    ? '記録中…'
                    : 'この献立を記録する'}
              </button>
              {saveState === 'error' && <p className="error">記録に失敗しました</p>}
              {saveState === 'saved' && status?.confirmed_meal && (
                <div className="dish-tiles">
                  {status.confirmed_meal.menu.map((dish) => (
                    <div key={dish.id} className="dish-tile">
                      <strong>{dish.name}</strong>
                      {dish.recipe_id || favoritedDishIds[dish.id] ? (
                        <span className="muted">レシピ登録済み</span>
                      ) : (
                        <button type="button" className="ghost" onClick={() => handleFavorite(dish.id)}>
                          お気に入り登録
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {saveState === 'saved' && <ConsumePanel mealId={result.meal_id} />}
            </>
          )}
        </div>
      )}
    </div>
  )
}
