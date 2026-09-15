from calendar import monthrange
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services.dish_genre_classifier import resolve_genre
from ..tag_utils import tags_to_schema

router = APIRouter()


def _meal_to_out(meal: models.Meal) -> schemas.MealOut:
    return schemas.MealOut(
        id=meal.id,
        date=meal.date,
        meal_type=meal.meal_type,
        servings=meal.servings,
        estimated=meal.estimated,
        memo=meal.memo or "",
        menu=[
            schemas.MealDishOut(
                name=dish.name,
                role=dish.role,
                recipe_id=dish.recipe_id,
                genre=dish.genre,
                ingredients=[i.name for i in dish.ingredients],
            )
            for dish in meal.dishes
        ],
        nutrition_per_serving=schemas.NutritionPerServing(
            calories_kcal=meal.calories_kcal,
            protein_g=meal.protein_g,
            fat_g=meal.fat_g,
            carb_g=meal.carb_g,
        ),
        cost_yen_per_serving=meal.cost_yen_per_serving,
        tags=tags_to_schema(meal.tags),
    )


@router.get("", response_model=list[schemas.MealOut])
def list_meals(
    days: int = 7,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """year・monthを指定するとその月1ヶ月分、指定しなければ直近days日分を返す(カレンダー表示用)。"""
    conditions = [models.Meal.household_id == current_user.household_id]
    if year is not None and month is not None:
        last_day = monthrange(year, month)[1]
        conditions.append(models.Meal.date >= date(year, month, 1))
        conditions.append(models.Meal.date <= date(year, month, last_day))
    else:
        conditions.append(models.Meal.date >= date.today() - timedelta(days=days))

    meals = db.scalars(
        select(models.Meal).where(*conditions).order_by(models.Meal.date.desc())
    ).all()
    return [_meal_to_out(meal) for meal in meals]


@router.post("", response_model=schemas.MealOut, status_code=201)
def create_meal(
    meal: schemas.MealIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_meal = models.Meal(
        household_id=current_user.household_id,
        date=meal.date,
        meal_type=meal.meal_type,
        servings=meal.servings,
        estimated=meal.estimated,
        memo=meal.memo,
        calories_kcal=meal.nutrition_per_serving.calories_kcal,
        protein_g=meal.nutrition_per_serving.protein_g,
        fat_g=meal.nutrition_per_serving.fat_g,
        carb_g=meal.nutrition_per_serving.carb_g,
        cost_yen_per_serving=meal.cost_yen_per_serving,
    )
    for dish in meal.menu:
        recipe_id = dish.recipe_id
        if recipe_id is None:
            # 名前が完全一致するお気に入りレシピがあれば自動でリンクする(ベストエフォート)
            matched = (
                db.query(models.Recipe)
                .filter(
                    models.Recipe.household_id == current_user.household_id,
                    models.Recipe.dish_name == dish.name,
                )
                .first()
            )
            recipe_id = matched.id if matched else None
        db_dish = models.MealDish(
            name=dish.name,
            role=dish.role,
            recipe_id=recipe_id,
            genre=resolve_genre(db, dish.name),
        )
        db_dish.ingredients = [
            models.MealDishIngredient(name=name) for name in dish.ingredients
        ]
        db_meal.dishes.append(db_dish)
    for category, values in meal.tags.model_dump().items():
        for value in values:
            db_meal.tags.append(models.MealTag(category=category, value=value))

    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return _meal_to_out(db_meal)
