from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FridgeItemIn(BaseModel):
    name: str
    added_date: Optional[date] = None
    memo: str = ""


class FridgeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    added_date: date
    memo: str = ""


class FridgeItemDateUpdate(BaseModel):
    added_date: date


PANTRY_STATUS_VOCAB = ["たっぷり", "そろそろ切れそう", "切れた"]


class PantryItemIn(BaseModel):
    name: str
    memo: str = ""


class PantryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    memo: str = ""
    status: str = "たっぷり"


class PantryItemStatusUpdate(BaseModel):
    status: str


class UserSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    default_servings: int = 2
    avoid_days_dish_name: int = 14
    avoid_days_genre: int = 5
    avoid_days_method_protein: int = 2
    avoid_days_cuisine: int = 1
    suggestion_mode: str = "batch"


class Tags(BaseModel):
    protein: list[str] = []
    cuisine: list[str] = []
    cooking_method: list[str] = []
    style: list[str] = []


class NutritionPerServing(BaseModel):
    calories_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carb_g: Optional[float] = None


class TimelineStep(BaseModel):
    step: int
    dish: str
    description: str


class MealDishIn(BaseModel):
    name: str
    role: Optional[str] = None
    recipe_id: Optional[int] = None
    ingredients: list[str] = []
    is_batch_cooked: bool = False


class MealDishOut(BaseModel):
    id: int
    name: str
    role: Optional[str] = None
    recipe_id: Optional[int] = None
    genre: Optional[str] = None
    ingredients: list[str] = []
    is_batch_cooked: bool = False


class MealIn(BaseModel):
    date: date
    meal_type: str
    servings: int = 2
    estimated: bool = True
    memo: str = ""
    menu: list[MealDishIn]
    nutrition_per_serving: NutritionPerServing = NutritionPerServing()
    cost_yen_per_serving: Optional[float] = None
    tags: Tags = Tags()


class MealOut(BaseModel):
    id: int
    date: date
    meal_type: str
    servings: int
    estimated: bool
    memo: str = ""
    menu: list[MealDishOut]
    nutrition_per_serving: NutritionPerServing
    cost_yen_per_serving: Optional[float] = None
    tags: Tags
    is_draft: bool = False
    timeline: list[TimelineStep] = []


class ConfirmMealRequest(BaseModel):
    batch_cooked_dish_names: list[str] = []


class MealStatus(BaseModel):
    confirmed_meal: Optional[MealOut] = None
    draft_for_slot: Optional[MealOut] = None
    stale_draft: Optional[MealOut] = None


class FridgeMatchCandidate(BaseModel):
    fridge_item_id: int
    fridge_item_name: str
    dish_name: str


class PantryMatchCandidate(BaseModel):
    pantry_item_id: int
    pantry_item_name: str
    dish_name: str
    current_status: str


class ConsumableResponse(BaseModel):
    fridge_candidates: list[FridgeMatchCandidate] = []
    pantry_candidates: list[PantryMatchCandidate] = []


class PantryStatusChange(BaseModel):
    pantry_item_id: int
    status: str


class ConsumeRequest(BaseModel):
    fridge_item_ids: list[int] = []
    pantry_updates: list[PantryStatusChange] = []


class SuggestedDish(BaseModel):
    name: str
    role: str
    ingredients: list[str] = []


class SuggestionRequest(BaseModel):
    meal_type: str = "夕食"
    servings: int = 2
    user_request: str = ""
    target_date: date = Field(default_factory=date.today)
    cuisine_preference: Optional[str] = None  # 未指定(おまかせ)ならNone。「和食」等を明示指定できる

    # 食べたいメニュー・使いたい食材の希望(タグ入力)。user_requestはそれ以外の希望用
    desired_dishes: list[str] = []
    desired_ingredients: list[str] = []

    # 微調整(#26): 直前の提案結果を渡してステートレスに再生成させる場合に指定する
    current_menu: Optional[list[SuggestedDish]] = None
    refinement_request: str = ""


class ApiUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_usd: Optional[float] = None


class SuggestionResponse(BaseModel):
    meal_id: int
    dishes: list[SuggestedDish]
    timeline: list[TimelineStep]
    nutrition_per_serving: NutritionPerServing
    estimated_cost_yen_per_serving: Optional[float] = None
    tags: Tags
    reasoning: str
    api_usage: ApiUsage


class RecipeIn(BaseModel):
    dish_name: str
    source_url: str = ""
    ingredients: list[str]
    steps: list[str]
    memo: str = ""
    tags: Tags = Tags()


class RecipeOut(BaseModel):
    id: int
    dish_name: str
    source_url: str = ""
    ingredients: list[str]
    steps: list[str]
    memo: str = ""
    tags: Tags
