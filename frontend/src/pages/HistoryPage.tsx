import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Meal } from '../types'

export function HistoryPage() {
  const [meals, setMeals] = useState<Meal[]>([])
  const [days, setDays] = useState(14)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .listMeals(days)
      .then(setMeals)
      .finally(() => setLoading(false))
  }, [days])

  return (
    <div className="page">
      <div className="card inline-form">
        <label>
          直近
          <input
            type="number"
            min={1}
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          />
          日分
        </label>
      </div>

      {loading ? (
        <p>読み込み中…</p>
      ) : meals.length === 0 ? (
        <p>この期間の献立記録はありません。</p>
      ) : (
        <ul className="item-list">
          {meals.map((meal) => (
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
