import { useEffect, useState } from 'react'
import { api } from '../api'
import type { FridgeItem } from '../types'

const CATEGORY_ORDER = ['野菜', '肉', '魚介', '卵・乳製品', '主食', '果物', 'その他']

function groupByCategory(items: FridgeItem[]): [string, FridgeItem[]][] {
  const groups = new Map<string, FridgeItem[]>()
  for (const item of items) {
    const list = groups.get(item.category) ?? []
    list.push(item)
    groups.set(item.category, list)
  }
  const known = CATEGORY_ORDER.filter((c) => groups.has(c))
  const unknown = [...groups.keys()].filter((c) => !CATEGORY_ORDER.includes(c))
  return [...known, ...unknown].map((c) => [c, groups.get(c)!])
}

export function FridgePage() {
  const [items, setItems] = useState<FridgeItem[]>([])
  const [name, setName] = useState('')
  const [memo, setMemo] = useState('')
  const [loading, setLoading] = useState(true)

  async function reload() {
    setItems(await api.listFridge())
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    await api.addFridgeItem({ name: name.trim(), memo: memo.trim() })
    setName('')
    setMemo('')
    await reload()
  }

  async function handleDelete(id: number) {
    await api.deleteFridgeItem(id)
    await reload()
  }

  return (
    <div className="page">
      <form className="card inline-form" onSubmit={handleAdd}>
        <input placeholder="食材名" value={name} onChange={(e) => setName(e.target.value)} />
        <input placeholder="メモ(任意)" value={memo} onChange={(e) => setMemo(e.target.value)} />
        <button type="submit">追加</button>
      </form>

      {loading ? (
        <p>読み込み中…</p>
      ) : items.length === 0 ? (
        <p>冷蔵庫は空です。</p>
      ) : (
        groupByCategory(items).map(([category, categoryItems]) => (
          <div key={category} className="fridge-group">
            <h3 className="fridge-group-title">
              {category} <span className="muted">({categoryItems.length})</span>
            </h3>
            <ul className="item-list">
              {categoryItems.map((item) => (
                <li key={item.id} className="card">
                  <div>
                    <strong>{item.name}</strong>
                    <span className="muted"> 追加日: {item.added_date}</span>
                    {item.memo && <div className="muted">{item.memo}</div>}
                  </div>
                  <button className="ghost" onClick={() => handleDelete(item.id)}>
                    削除
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </div>
  )
}
