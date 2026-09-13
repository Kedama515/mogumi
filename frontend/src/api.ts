import type {
  FridgeItem,
  Meal,
  PantryItem,
  Recipe,
  SuggestionRequest,
  SuggestionResponse,
} from './types'

const TOKEN_KEY = 'mogumi_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

const COST_KEY = 'mogumi_api_cost_total_usd'

export function getTotalCost(): number {
  const raw = localStorage.getItem(COST_KEY)
  return raw ? parseFloat(raw) : 0
}

export interface CostUpdate {
  last: number
  total: number
}

let costListeners: ((update: CostUpdate) => void)[] = []
export function onCostChange(listener: (update: CostUpdate) => void): () => void {
  costListeners.push(listener)
  return () => {
    costListeners = costListeners.filter((l) => l !== listener)
  }
}

function addCost(amount: number) {
  const total = getTotalCost() + amount
  localStorage.setItem(COST_KEY, String(total))
  costListeners.forEach((l) => l({ last: amount, total }))
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`/api${path}`, { headers, ...options })

  if (res.status === 401) {
    clearToken()
    onUnauthorized?.()
    throw new Error('認証が必要です')
  }
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  login: async (username: string, password: string): Promise<void> => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    })
    if (!res.ok) {
      throw new Error('ユーザー名またはパスワードが違います')
    }
    const data = await res.json()
    setToken(data.access_token)
  },

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

  suggest: async (req: SuggestionRequest) => {
    const result = await request<SuggestionResponse>('/suggestions', {
      method: 'POST',
      body: JSON.stringify(req),
    })
    if (result.api_usage.cost_usd != null) {
      addCost(result.api_usage.cost_usd)
    }
    return result
  },

  listRecipes: () => request<Recipe[]>('/recipes'),
  createRecipe: (recipe: Omit<Recipe, 'id'>) =>
    request<Recipe>('/recipes', { method: 'POST', body: JSON.stringify(recipe) }),
  deleteRecipe: (id: number) => request<void>(`/recipes/${id}`, { method: 'DELETE' }),
}
