import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services.claude_client import propose_menu
from ..services.dish_genre_classifier import resolve_genre
from ..services.suggestion_prompt import build_prompt

router = APIRouter()


def _get_or_create_draft(
    db: Session, household_id: int, target_date, meal_type: str
) -> models.Meal:
    draft = (
        db.query(models.Meal)
        .filter(
            models.Meal.household_id == household_id,
            models.Meal.date == target_date,
            models.Meal.meal_type == meal_type,
            models.Meal.is_draft.is_(True),
        )
        .first()
    )
    if draft is None:
        draft = models.Meal(
            household_id=household_id, date=target_date, meal_type=meal_type, is_draft=True
        )
        db.add(draft)
    return draft


@router.post("", response_model=schemas.SuggestionResponse)
def suggest_menu(
    request: schemas.SuggestionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    prompt = build_prompt(
        db=db,
        household_id=current_user.household_id,
        meal_type=request.meal_type,
        servings=request.servings,
        user_request=request.user_request,
        target_date=request.target_date,
        avoid_days_dish_name=current_user.avoid_days_dish_name,
        avoid_days_genre=current_user.avoid_days_genre,
        avoid_days_method_protein=current_user.avoid_days_method_protein,
        avoid_days_cuisine=current_user.avoid_days_cuisine,
        cuisine_preference=request.cuisine_preference,
        desired_dishes=request.desired_dishes,
        desired_ingredients=request.desired_ingredients,
        current_menu=(
            [d.model_dump() for d in request.current_menu] if request.current_menu else None
        ),
        refinement_request=request.refinement_request,
    )
    menu_data, usage = propose_menu(prompt)

    # 生成結果を(household, target_date, meal_type)スロットの下書きとして保存する(#38)。
    # 同じスロットに既に下書きがあれば上書きする(微調整#26での再生成も同じ扱い)。
    draft = _get_or_create_draft(
        db, current_user.household_id, request.target_date, request.meal_type
    )
    draft.servings = request.servings
    draft.estimated = True
    draft.memo = menu_data.get("reasoning", "")
    nutrition = menu_data.get("nutrition_per_serving") or {}
    draft.calories_kcal = nutrition.get("calories_kcal")
    draft.protein_g = nutrition.get("protein_g")
    draft.fat_g = nutrition.get("fat_g")
    draft.carb_g = nutrition.get("carb_g")
    draft.cost_yen_per_serving = menu_data.get("estimated_cost_yen_per_serving")
    draft.timeline_json = json.dumps(menu_data.get("timeline", []), ensure_ascii=False)

    draft.dishes = []
    for dish in menu_data.get("dishes", []):
        db_dish = models.MealDish(
            name=dish["name"],
            role=dish.get("role"),
            genre=resolve_genre(db, dish["name"]),
        )
        db_dish.ingredients = [
            models.MealDishIngredient(name=n) for n in dish.get("ingredients", [])
        ]
        draft.dishes.append(db_dish)

    draft.tags = []
    for category, values in (menu_data.get("tags") or {}).items():
        for value in values:
            draft.tags.append(models.MealTag(category=category, value=value))

    db.add(draft)
    db.commit()
    db.refresh(draft)

    return schemas.SuggestionResponse(
        meal_id=draft.id,
        dishes=[schemas.SuggestedDish(**d) for d in menu_data["dishes"]],
        timeline=menu_data["timeline"],
        nutrition_per_serving=menu_data["nutrition_per_serving"],
        estimated_cost_yen_per_serving=menu_data.get("estimated_cost_yen_per_serving"),
        tags=menu_data["tags"],
        reasoning=menu_data["reasoning"],
        api_usage=usage,
    )
