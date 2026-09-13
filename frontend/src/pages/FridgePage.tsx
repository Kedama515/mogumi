import { useEffect, useState } from 'react'
import { api } from '../api'
import type { FridgeItem } from '../types'

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
        <ul className="item-list">
          {items.map((item) => (
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
      )}
    </div>
  )
}
