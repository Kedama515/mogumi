from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


def _meal_to_out(meal: models.Meal) -> schemas.MealOut:
    tags: dict[str, list[str]] = {"protein": [], "cuisine": [], "cooking_method": [], "style": []}
    for tag in meal.tags:
        tags.setdefault(tag.category, []).append(tag.value)

    return schemas.MealOut(
        id=meal.id,
        date=meal.date,
        meal_type=meal.meal_type,
        servings=meal.servings,
        estimated=meal.estimated,
        memo=meal.memo or "",
        menu=[dish.name for dish in meal.dishes],
        nutrition_per_serving=schemas.NutritionPerServing(
            calories_kcal=meal.calories_kcal,
            protein_g=meal.protein_g,
            fat_g=meal.fat_g,
            carb_g=meal.carb_g,
        ),
        cost_yen_per_serving=meal.cost_yen_per_serving,
        tags=schemas.MealTags(**tags),
    )


@router.get("", response_model=list[schemas.MealOut])
def list_meals(days: int = 7, db: Session = Depends(get_db)):
    since = date.today() - timedelta(days=days)
    meals = db.scalars(
        select(models.Meal).where(models.Meal.date >= since).order_by(models.Meal.date.desc())
    ).all()
    return [_meal_to_out(meal) for meal in meals]


@router.post("", response_model=schemas.MealOut, status_code=201)
def create_meal(meal: schemas.MealIn, db: Session = Depends(get_db)):
    db_meal = models.Meal(
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
    for name in meal.menu:
        db_meal.dishes.append(models.MealDish(name=name))
    for category, values in meal.tags.model_dump().items():
        for value in values:
            db_meal.tags.append(models.MealTag(category=category, value=value))

    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return _meal_to_out(db_meal)
