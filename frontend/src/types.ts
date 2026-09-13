export interface FridgeItem {
  id: number
  name: string
  added_date: string
  memo: string
}

export interface PantryItem {
  id: number
  name: string
  memo: string
}

export interface Tags {
  protein: string[]
  cuisine: string[]
  cooking_method: string[]
  style: string[]
}

export interface NutritionPerServing {
  calories_kcal: number | null
  protein_g: number | null
  fat_g: number | null
  carb_g: number | null
}

export interface Meal {
  id: number
  date: string
  meal_type: string
  servings: number
  estimated: boolean
  memo: string
  menu: string[]
  nutrition_per_serving: NutritionPerServing
  cost_yen_per_serving: number | null
  tags: Tags
}

export interface SuggestionRequest {
  meal_type: string
  servings: number
  user_request: string
  lookback_days: number
}

export interface SuggestedDish {
  name: string
  role: string
}

export interface TimelineStep {
  step: number
  dish: string
  description: string
}

export interface SuggestionResponse {
  dishes: SuggestedDish[]
  timeline: TimelineStep[]
  nutrition_per_serving: NutritionPerServing
  estimated_cost_yen_per_serving: number | null
  tags: Tags
  reasoning: string
}

export interface Recipe {
  id: number
  dish_name: string
  source_url: string
  ingredients: string[]
  steps: string[]
  memo: string
  tags: Tags
}
