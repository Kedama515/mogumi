import { useEffect, useState } from 'react'
import { api } from '../api'
import type { ConsumableResponse } from '../types'

const PANTRY_STATUS_OPTIONS = ['たっぷり', 'そろそろ切れそう', '切れた']

export function ConsumePanel({ mealId }: { mealId: number }) {
  const [data, setData] = useState<ConsumableResponse | null>(null)
  const [checkedFridge, setCheckedFridge] = useState<Record<number, boolean>>({})
  const [pantryStatus, setPantryStatus] = useState<Record<number, string>>({})
  const [state, setState] = useState<'idle' | 'saving' | 'saved'>('idle')

  useEffect(() => {
    api.getConsumable(mealId).then((res) => {
      setData(res)
      setCheckedFridge(
        Object.fromEntries(res.fridge_candidates.map((c) => [c.fridge_item_id, true])),
      )
      setPantryStatus(
        Object.fromEntries(
          res.pantry_candidates.map((c) => [c.pantry_item_id, c.current_status]),
        ),
      )
    })
  }, [mealId])

  if (!data || (data.fridge_candidates.length === 0 && data.pantry_candidates.length === 0)) {
    return null
  }
  if (state === 'saved') {
    return <p className="muted">在庫を更新しました。</p>
  }

  async function handleSubmit() {
    setState('saving')
    const fridgeIds = data!.fridge_candidates
      .filter((c) => checkedFridge[c.fridge_item_id])
      .map((c) => c.fridge_item_id)
    const pantryUpdates = data!.pantry_candidates
      .filter((c) => pantryStatus[c.pantry_item_id] !== c.current_status)
      .map((c) => ({ pantry_item_id: c.pantry_item_id, status: pantryStatus[c.pantry_item_id] }))
    await api.consume(mealId, fridgeIds, pantryUpdates)
    setState('saved')
  }

  return (
    <div className="card">
      <h3>使った食材を整理する</h3>
      {data.fridge_candidates.length > 0 && (
        <ul className="item-list">
          {data.fridge_candidates.map((c) => (
            <li key={c.fridge_item_id}>
              <label>
                <input
                  type="checkbox"
                  checked={Boolean(checkedFridge[c.fridge_item_id])}
                  onChange={(e) =>
                    setCheckedFridge((prev) => ({
                      ...prev,
                      [c.fridge_item_id]: e.target.checked,
                    }))
                  }
                />
                {c.fridge_item_name} <span className="muted">({c.dish_name}で使用)</span>
              </label>
            </li>
          ))}
        </ul>
      )}
      {data.pantry_candidates.length > 0 && (
        <ul className="item-list">
          {data.pantry_candidates.map((c) => (
            <li key={c.pantry_item_id}>
              <span>
                {c.pantry_item_name} <span className="muted">({c.dish_name}で使用)</span>
              </span>
              <select
                value={pantryStatus[c.pantry_item_id] ?? c.current_status}
                onChange={(e) =>
                  setPantryStatus((prev) => ({ ...prev, [c.pantry_item_id]: e.target.value }))
                }
              >
                {PANTRY_STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </li>
          ))}
        </ul>
      )}
      <button onClick={handleSubmit} disabled={state === 'saving'}>
        {state === 'saving' ? '更新中…' : '在庫を更新する'}
      </button>
    </div>
  )
}
