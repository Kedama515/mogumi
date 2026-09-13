from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


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
    added_date: date
    memo: str = ""


class PantryItemIn(BaseModel):
    name: str
    memo: str = ""


class PantryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    memo: str = ""


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


class MealIn(BaseModel):
    date: date
    meal_type: str
    servings: int = 2
    estimated: bool = True
    memo: str = ""
    menu: list[str]
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
    menu: list[str]
    nutrition_per_serving: NutritionPerServing
    cost_yen_per_serving: Optional[float] = None
    tags: Tags


class SuggestionRequest(BaseModel):
    meal_type: str = "夕食"
    servings: int = 2
    user_request: str = ""
    lookback_days: int = 3


class SuggestedDish(BaseModel):
    name: str
    role: str


class TimelineStep(BaseModel):
    step: int
    dish: str
    description: str


class ApiUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_usd: Optional[float] = None


class SuggestionResponse(BaseModel):
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
