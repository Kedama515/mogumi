import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { Meal } from '../types'

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土']

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function toDateKey(year: number, month: number, day: number) {
  return `${year}-${pad(month)}-${pad(day)}`
}

export function CalendarPage() {
  const today = new Date()
  const [viewYear, setViewYear] = useState(today.getFullYear())
  const [viewMonth, setViewMonth] = useState(today.getMonth() + 1)
  const [meals, setMeals] = useState<Meal[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState(
    toDateKey(today.getFullYear(), today.getMonth() + 1, today.getDate()),
  )

  useEffect(() => {
    setLoading(true)
    api
      .listMealsForMonth(viewYear, viewMonth)
      .then(setMeals)
      .finally(() => setLoading(false))
  }, [viewYear, viewMonth])

  const mealsByDate = useMemo(() => {
    const map = new Map<string, Meal[]>()
    for (const meal of meals) {
      const list = map.get(meal.date) ?? []
      list.push(meal)
      map.set(meal.date, list)
    }
    return map
  }, [meals])

  function goPrevMonth() {
    if (viewMonth === 1) {
      setViewYear((y) => y - 1)
      setViewMonth(12)
    } else {
      setViewMonth((m) => m - 1)
    }
  }

  function goNextMonth() {
    if (viewMonth === 12) {
      setViewYear((y) => y + 1)
      setViewMonth(1)
    } else {
      setViewMonth((m) => m + 1)
    }
  }

  const firstWeekday = new Date(viewYear, viewMonth - 1, 1).getDay()
  const daysInMonth = new Date(viewYear, viewMonth, 0).getDate()
  const cells: (number | null)[] = [
    ...Array(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]

  const selectedMeals = mealsByDate.get(selectedDate) ?? []

  return (
    <div className="page">
      <div className="card calendar-card">
        <div className="calendar-header">
          <button className="ghost" onClick={goPrevMonth}>
            ‹
          </button>
          <strong>
            {viewYear}年{viewMonth}月
          </strong>
          <button className="ghost" onClick={goNextMonth}>
            ›
          </button>
        </div>
        <div className="calendar-grid">
          {WEEKDAYS.map((w) => (
            <div key={w} className="calendar-weekday">
              {w}
            </div>
          ))}
          {cells.map((day, i) => {
            if (day === null) return <div key={i} className="calendar-cell empty" />
            const dateKey = toDateKey(viewYear, viewMonth, day)
            const hasMeal = mealsByDate.has(dateKey)
            const isSelected = dateKey === selectedDate
            return (
              <button
                key={i}
                className={
                  'calendar-cell' + (isSelected ? ' selected' : '') + (hasMeal ? ' has-meal' : '')
                }
                onClick={() => setSelectedDate(dateKey)}
              >
                {day}
                {hasMeal && <span className="calendar-dot" />}
              </button>
            )
          })}
        </div>
      </div>

      {loading ? (
        <p>読み込み中…</p>
      ) : selectedMeals.length === 0 ? (
        <p className="muted">{selectedDate} の献立記録はありません。</p>
      ) : (
        <ul className="item-list">
          {selectedMeals.map((meal) => (
            <li key={meal.id} className="card meal-card">
              <div className="meal-header">
                <strong>
                  {meal.date} {meal.meal_type}
                </strong>
                <span className="muted">{meal.servings}人前</span>
              </div>
              <div>
                {meal.menu.map((dish, i) => (
                  <span key={i}>
                    {dish.role && <span className="dish-role">{dish.role}</span>}
                    {dish.name}
                    {i < meal.menu.length - 1 && ' / '}
                  </span>
                ))}
              </div>
              <div className="nutrition-row">
                <span>{meal.nutrition_per_serving.calories_kcal ?? '-'} kcal</span>
                <span>たんぱく質 {meal.nutrition_per_serving.protein_g ?? '-'} g</span>
                <span>{meal.cost_yen_per_serving ?? '-'} 円/人前</span>
              </div>
              {meal.memo && <div className="muted">{meal.memo}</div>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
