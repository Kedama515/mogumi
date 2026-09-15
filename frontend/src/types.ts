export interface FridgeItem {
  id: number
  name: string
  category: string
  added_date: string
  memo: string
}

export interface PantryItem {
  id: number
  name: string
  category: string
  memo: string
  status: string
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

export interface MealDish {
  id: number
  name: string
  role: string | null
  recipe_id: number | null
  genre: string | null
  ingredients: string[]
  is_batch_cooked: boolean
}

export interface UserSettings {
  default_servings: number
  avoid_days_dish_name: number
  avoid_days_genre: number
  avoid_days_method_protein: number
  avoid_days_cuisine: number
  suggestion_mode: 'batch' | 'confirm_menu'
}

export interface TimelineStep {
  step: number
  dish: string
  description: string
}

export interface Meal {
  id: number
  date: string
  meal_type: string
  servings: number
  estimated: boolean
  memo: string
  menu: MealDish[]
  nutrition_per_serving: NutritionPerServing
  cost_yen_per_serving: number | null
  tags: Tags
  is_draft: boolean
  timeline: TimelineStep[]
}

export interface MealStatus {
  confirmed_meal: Meal | null
  draft_for_slot: Meal | null
  stale_draft: Meal | null
}

export interface SuggestedDish {
  name: string
  role: string
  ingredients: string[]
}

export interface SuggestionRequest {
  meal_type: string
  servings: number
  user_request: string
  target_date: string
  cuisine_preference: string | null
  current_menu?: SuggestedDish[]
  refinement_request?: string
}

export interface ApiUsage {
  input_tokens: number
  output_tokens: number
  cost_usd: number | null
}

export interface SuggestionResponse {
  meal_id: number
  dishes: SuggestedDish[]
  timeline: TimelineStep[]
  nutrition_per_serving: NutritionPerServing
  estimated_cost_yen_per_serving: number | null
  tags: Tags
  reasoning: string
  api_usage: ApiUsage
}

export interface FridgeMatchCandidate {
  fridge_item_id: number
  fridge_item_name: string
  dish_name: string
}

export interface PantryMatchCandidate {
  pantry_item_id: number
  pantry_item_name: string
  dish_name: string
  current_status: string
}

export interface ConsumableResponse {
  fridge_candidates: FridgeMatchCandidate[]
  pantry_candidates: PantryMatchCandidate[]
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
