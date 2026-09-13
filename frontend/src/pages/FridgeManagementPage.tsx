import { useState } from 'react'
import { FridgePage } from './FridgePage'
import { PantryPage } from './PantryPage'

const SUB_TABS = [
  { key: 'fridge', label: '冷蔵庫', Component: FridgePage },
  { key: 'pantry', label: '常備品', Component: PantryPage },
] as const

export function FridgeManagementPage() {
  const [sub, setSub] = useState<(typeof SUB_TABS)[number]['key']>('fridge')
  const Active = SUB_TABS.find((t) => t.key === sub)!.Component

  return (
    <div>
      <div className="sub-tabs">
        {SUB_TABS.map((t) => (
          <button
            key={t.key}
            className={t.key === sub ? 'sub-tab active' : 'sub-tab'}
            onClick={() => setSub(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <Active />
    </div>
  )
}
