import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { Meal } from '../types'

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土']
const MEAL_TYPES = ['朝食', '昼食', '夕食']
const MEAL_TYPE_PRIORITY = ['夕食', '昼食', '朝食']
const MEAL_TYPE_DOT_CLASS: Record<string, string> = {
  朝食: 'calendar-dot-breakfast',
  昼食: 'calendar-dot-lunch',
  夕食: 'calendar-dot-dinner',
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function toDateKey(year: number, month: number, day: number) {
  return `${year}-${pad(month)}-${pad(day)}`
}

function parseDishLine(line: string): { name: string; role: string | null } {
  const [name, role] = line.split('|').map((s) => s.trim())
  return { name, role: role || null }
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
  const [selectedMealType, setSelectedMealType] = useState<string | null>(null)
  const [showManualForm, setShowManualForm] = useState(false)
  const [manualMealType, setManualMealType] = useState('夕食')
  const [manualDishes, setManualDishes] = useState('')
  const [manualMemo, setManualMemo] = useState('')

  async function reload() {
    setLoading(true)
    try {
      setMeals(await api.listMealsForMonth(viewYear, viewMonth))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    reload()
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

  const mealsForSelectedDate = mealsByDate.get(selectedDate) ?? []
  const mealTypesForSelectedDate = MEAL_TYPE_PRIORITY.filter((t) =>
    mealsForSelectedDate.some((m) => m.meal_type === t),
  )

  useEffect(() => {
    setSelectedMealType(mealTypesForSelectedDate[0] ?? null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, meals])

  async function handleManualSubmit(e: React.FormEvent) {
    e.preventDefault()
    const dishLines = manualDishes
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
    if (dishLines.length === 0) return
    const meal: Omit<Meal, 'id'> = {
      date: selectedDate,
      meal_type: manualMealType,
      servings: 2,
      estimated: false,
      memo: manualMemo.trim(),
      menu: dishLines.map((line) => {
        const { name, role } = parseDishLine(line)
        return { name, role, recipe_id: null, genre: null, ingredients: [], is_batch_cooked: false }
      }),
      nutrition_per_serving: {
        calories_kcal: null,
        protein_g: null,
        fat_g: null,
        carb_g: null,
      },
      cost_yen_per_serving: null,
      tags: { protein: [], cuisine: [], cooking_method: [], style: [] },
    }
    await api.createMeal(meal)
    setManualDishes('')
    setManualMemo('')
    setShowManualForm(false)
    await reload()
  }

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

  const mealsForSelectedMealType = mealsForSelectedDate.filter(
    (m) => m.meal_type === selectedMealType,
  )

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
            const dayMeals = mealsByDate.get(dateKey) ?? []
            const dayMealTypes = MEAL_TYPES.filter((t) => dayMeals.some((m) => m.meal_type === t))
            const isSelected = dateKey === selectedDate
            return (
              <button
                key={i}
                className={
                  'calendar-cell' +
                  (isSelected ? ' selected' : '') +
                  (dayMealTypes.length > 0 ? ' has-meal' : '')
                }
                onClick={() => setSelectedDate(dateKey)}
              >
                {day}
                {dayMealTypes.length > 0 && (
                  <span className="calendar-dots">
                    {dayMealTypes.map((t) => (
                      <span key={t} className={`calendar-dot ${MEAL_TYPE_DOT_CLASS[t]}`} />
                    ))}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      <button className="ghost" onClick={() => setShowManualForm((v) => !v)}>
        {showManualForm ? '閉じる' : `＋ ${selectedDate} の献立を手動で追加`}
      </button>

      {showManualForm && (
        <form className="card recipe-form" onSubmit={handleManualSubmit}>
          <label>
            食事
            <select value={manualMealType} onChange={(e) => setManualMealType(e.target.value)}>
              {MEAL_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label>
            料理名(1行に1つ。役割をつける場合は「料理名|役割」)
            <textarea
              placeholder={'カレー|主菜\nサラダ|副菜'}
              value={manualDishes}
              onChange={(e) => setManualDishes(e.target.value)}
            />
          </label>
          <label>
            メモ(任意)
            <textarea value={manualMemo} onChange={(e) => setManualMemo(e.target.value)} />
          </label>
          <button type="submit">追加</button>
        </form>
      )}

      {loading ? (
        <p>読み込み中…</p>
      ) : mealTypesForSelectedDate.length === 0 ? (
        <p className="muted">{selectedDate} の献立記録はありません。</p>
      ) : (
        <>
          <div className="sub-tabs">
            {mealTypesForSelectedDate.map((t) => (
              <button
                key={t}
                className={'sub-tab' + (t === selectedMealType ? ' active' : '')}
                onClick={() => setSelectedMealType(t)}
              >
                {t}
              </button>
            ))}
          </div>
          <ul className="item-list">
            {mealsForSelectedMealType.map((meal) => (
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
        </>
      )}
    </div>
  )
}
