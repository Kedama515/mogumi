import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Recipe } from '../types'

function splitLines(text: string): string[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
}

function splitCsv(text: string): string[] {
  return text
    .split(',')
    .map((v) => v.trim())
    .filter(Boolean)
}

const EMPTY_FORM = {
  dish_name: '',
  source_url: '',
  ingredients: '',
  steps: '',
  memo: '',
  protein: '',
  cuisine: '',
  cooking_method: '',
  style: '',
}

export function RecipePage() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [openId, setOpenId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)

  async function reload() {
    setRecipes(await api.listRecipes())
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [])

  function startEdit(r: Recipe) {
    setEditingId(r.id)
    setForm({
      dish_name: r.dish_name,
      source_url: r.source_url,
      ingredients: r.ingredients.join('\n'),
      steps: r.steps.join('\n'),
      memo: r.memo,
      protein: r.tags.protein.join(', '),
      cuisine: r.tags.cuisine.join(', '),
      cooking_method: r.tags.cooking_method.join(', '),
      style: r.tags.style.join(', '),
    })
    setShowForm(true)
  }

  function closeForm() {
    setForm(EMPTY_FORM)
    setEditingId(null)
    setShowForm(false)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.dish_name.trim()) return
    const payload = {
      dish_name: form.dish_name.trim(),
      source_url: form.source_url.trim(),
      ingredients: splitLines(form.ingredients),
      steps: splitLines(form.steps),
      memo: form.memo.trim(),
      tags: {
        protein: splitCsv(form.protein),
        cuisine: splitCsv(form.cuisine),
        cooking_method: splitCsv(form.cooking_method),
        style: splitCsv(form.style),
      },
    }
    if (editingId != null) {
      await api.updateRecipe(editingId, payload)
    } else {
      await api.createRecipe(payload)
    }
    closeForm()
    await reload()
  }

  async function handleDelete(id: number) {
    await api.deleteRecipe(id)
    await reload()
  }

  const allTags = (r: Recipe) =>
    [...r.tags.protein, ...r.tags.cuisine, ...r.tags.cooking_method, ...r.tags.style]

  return (
    <div className="page">
      <button
        className="ghost"
        onClick={() => (showForm ? closeForm() : setShowForm(true))}
      >
        {showForm ? '閉じる' : '＋ レシピを追加'}
      </button>

      {showForm && (
        <form className="card recipe-form" onSubmit={handleSubmit}>
          <label>
            料理名
            <input
              value={form.dish_name}
              onChange={(e) => setForm({ ...form, dish_name: e.target.value })}
            />
          </label>
          <label>
            出典URL(任意)
            <input
              value={form.source_url}
              onChange={(e) => setForm({ ...form, source_url: e.target.value })}
            />
          </label>
          <label>
            材料(1行に1つ)
            <textarea
              value={form.ingredients}
              onChange={(e) => setForm({ ...form, ingredients: e.target.value })}
            />
          </label>
          <label>
            手順(1行に1つ)
            <textarea
              value={form.steps}
              onChange={(e) => setForm({ ...form, steps: e.target.value })}
            />
          </label>
          <label>
            メモ(任意)
            <textarea value={form.memo} onChange={(e) => setForm({ ...form, memo: e.target.value })} />
          </label>
          <div className="field-row">
            <label>
              たんぱく源(カンマ区切り)
              <input
                value={form.protein}
                onChange={(e) => setForm({ ...form, protein: e.target.value })}
              />
            </label>
            <label>
              ジャンル
              <input
                value={form.cuisine}
                onChange={(e) => setForm({ ...form, cuisine: e.target.value })}
              />
            </label>
          </div>
          <div className="field-row">
            <label>
              調理法
              <input
                value={form.cooking_method}
                onChange={(e) => setForm({ ...form, cooking_method: e.target.value })}
              />
            </label>
            <label>
              スタイル
              <input value={form.style} onChange={(e) => setForm({ ...form, style: e.target.value })} />
            </label>
          </div>
          <button type="submit">{editingId != null ? '更新' : '追加'}</button>
        </form>
      )}

      {loading ? (
        <p>読み込み中…</p>
      ) : recipes.length === 0 ? (
        <p>レシピが登録されていません。</p>
      ) : (
        <ul className="item-list">
          {recipes.map((r) => (
            <li key={r.id} className="card recipe-card">
              <div className="recipe-summary" onClick={() => setOpenId(openId === r.id ? null : r.id)}>
                <div>
                  <strong>{r.dish_name}</strong>
                  <div className="tag-row">
                    {allTags(r).map((t) => (
                      <span key={t} className="dish-role">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  className="ghost"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(r.id)
                  }}
                >
                  削除
                </button>
              </div>

              {openId === r.id && (
                <div className="recipe-detail">
                  {r.source_url && (
                    <p>
                      <a href={r.source_url} target="_blank" rel="noreferrer">
                        {r.source_url}
                      </a>
                    </p>
                  )}
                  <h4>材料</h4>
                  <ul>
                    {r.ingredients.map((ing, i) => (
                      <li key={i}>{ing}</li>
                    ))}
                  </ul>
                  <h4>手順</h4>
                  <ol>
                    {r.steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                  {r.memo && <p className="muted">{r.memo}</p>}
                  <button className="ghost" onClick={() => startEdit(r)}>
                    編集
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
