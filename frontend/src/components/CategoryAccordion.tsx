import type { ReactNode } from 'react'
import { useState } from 'react'

export const CATEGORY_ORDER = [
  '野菜',
  '肉',
  '魚介',
  '卵・乳製品',
  '主食',
  '果物',
  '調味料',
  '油',
  '乾物・缶詰',
  '作り置き料理',
  'その他',
]

function groupByCategory<T extends { category: string }>(items: T[]): [string, T[]][] {
  const groups = new Map<string, T[]>()
  for (const item of items) {
    const list = groups.get(item.category) ?? []
    list.push(item)
    groups.set(item.category, list)
  }
  const known = CATEGORY_ORDER.filter((c) => groups.has(c))
  const unknown = [...groups.keys()].filter((c) => !CATEGORY_ORDER.includes(c))
  return [...known, ...unknown].map((c) => [c, groups.get(c)!])
}

export function CategoryAccordion<T extends { id: number; category: string }>({
  items,
  renderItem,
}: {
  items: T[]
  renderItem: (item: T) => ReactNode
}) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})

  function toggle(category: string) {
    setCollapsed((prev) => ({ ...prev, [category]: !prev[category] }))
  }

  return (
    <>
      {groupByCategory(items).map(([category, categoryItems]) => {
        const isCollapsed = Boolean(collapsed[category])
        return (
          <div key={category} className="fridge-group">
            <button className="fridge-group-title" onClick={() => toggle(category)}>
              <span className="fridge-group-arrow">{isCollapsed ? '▶' : '▼'}</span>
              {category} <span className="muted">({categoryItems.length})</span>
            </button>
            {!isCollapsed && <ul className="item-list">{categoryItems.map(renderItem)}</ul>}
          </div>
        )
      })}
    </>
  )
}
