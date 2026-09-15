import { useEffect, useState } from 'react'
import { api } from '../api'
import { CategoryAccordion } from '../components/CategoryAccordion'
import type { PantryItem } from '../types'

const PANTRY_STATUS_OPTIONS = ['たっぷり', 'そろそろ切れそう', '切れた']

export function PantryPage() {
  const [items, setItems] = useState<PantryItem[]>([])
  const [name, setName] = useState('')
  const [memo, setMemo] = useState('')
  const [loading, setLoading] = useState(true)

  async function reload() {
    setItems(await api.listPantry())
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    await api.addPantryItem({ name: name.trim(), memo: memo.trim() })
    setName('')
    setMemo('')
    await reload()
  }

  async function handleDelete(id: number) {
    await api.deletePantryItem(id)
    await reload()
  }

  async function handleStatusChange(id: number, status: string) {
    await api.updatePantryItemStatus(id, status)
    await reload()
  }

  return (
    <div className="page">
      <form className="card inline-form" onSubmit={handleAdd}>
        <input placeholder="常備品名" value={name} onChange={(e) => setName(e.target.value)} />
        <input placeholder="メモ(任意)" value={memo} onChange={(e) => setMemo(e.target.value)} />
        <button type="submit">追加</button>
      </form>

      {loading ? (
        <p>読み込み中…</p>
      ) : items.length === 0 ? (
        <p>常備品が登録されていません。</p>
      ) : (
        <CategoryAccordion
          items={items}
          renderItem={(item) => (
            <li key={item.id} className="card">
              <div>
                <strong>{item.name}</strong>
                <select
                  value={item.status}
                  onChange={(e) => handleStatusChange(item.id, e.target.value)}
                >
                  {PANTRY_STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                {item.memo && <div className="muted">{item.memo}</div>}
              </div>
              <button className="ghost" onClick={() => handleDelete(item.id)}>
                削除
              </button>
            </li>
          )}
        />
      )}
    </div>
  )
}
