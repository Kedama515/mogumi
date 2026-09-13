import type {
  FridgeItem,
  Meal,
  PantryItem,
  SuggestionRequest,
  SuggestionResponse,
} from './types'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  listFridge: () => request<FridgeItem[]>('/fridge'),
  addFridgeItem: (item: { name: string; memo?: string }) =>
    request<FridgeItem>('/fridge', { method: 'POST', body: JSON.stringify(item) }),
  deleteFridgeItem: (id: number) => request<void>(`/fridge/${id}`, { method: 'DELETE' }),

  listPantry: () => request<PantryItem[]>('/pantry'),
  addPantryItem: (item: { name: string; memo?: string }) =>
    request<PantryItem>('/pantry', { method: 'POST', body: JSON.stringify(item) }),
  deletePantryItem: (id: number) => request<void>(`/pantry/${id}`, { method: 'DELETE' }),

  listMeals: (days = 14) => request<Meal[]>(`/meals?days=${days}`),
  createMeal: (meal: Omit<Meal, 'id'>) =>
    request<Meal>('/meals', { method: 'POST', body: JSON.stringify(meal) }),

  suggest: (req: SuggestionRequest) =>
    request<SuggestionResponse>('/suggestions', { method: 'POST', body: JSON.stringify(req) }),
}
