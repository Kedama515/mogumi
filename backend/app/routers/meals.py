import json
from calendar import monthrange
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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
                is_batch_cooked=dish.is_batch_cooked,
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
        is_draft=meal.is_draft,
        timeline=json.loads(meal.timeline_json) if meal.timeline_json else [],
    )


@router.get("", response_model=list[schemas.MealOut])
def list_meals(
    days: int = 7,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """year・monthを指定するとその月1ヶ月分、指定しなければ直近days日分を返す(カレンダー表示用)。
    仮(下書き)の献立は確定するまで表示しない(#38)。"""
    conditions = [
        models.Meal.household_id == current_user.household_id,
        models.Meal.is_draft.is_(False),
    ]
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


@router.get("/status", response_model=schemas.MealStatus)
def get_meal_status(
    meal_type: str,
    date_: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """指定スロット(date, meal_type)の確定済み献立・下書きの有無と、household全体の
    放置された過去の下書きの有無を返す(#37・#38の事前チェック用)。"""
    household_id = current_user.household_id

    confirmed = (
        db.query(models.Meal)
        .filter(
            models.Meal.household_id == household_id,
            models.Meal.date == date_,
            models.Meal.meal_type == meal_type,
            models.Meal.is_draft.is_(False),
        )
        .first()
    )
    draft_for_slot = (
        db.query(models.Meal)
        .filter(
            models.Meal.household_id == household_id,
            models.Meal.date == date_,
            models.Meal.meal_type == meal_type,
            models.Meal.is_draft.is_(True),
        )
        .first()
    )
    stale_draft = (
        db.query(models.Meal)
        .filter(
            models.Meal.household_id == household_id,
            models.Meal.is_draft.is_(True),
            models.Meal.date < date.today(),
        )
        .order_by(models.Meal.date.asc())
        .first()
    )

    return schemas.MealStatus(
        confirmed_meal=_meal_to_out(confirmed) if confirmed else None,
        draft_for_slot=_meal_to_out(draft_for_slot) if draft_for_slot else None,
        stale_draft=_meal_to_out(stale_draft) if stale_draft else None,
    )


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
            is_batch_cooked=dish.is_batch_cooked,
        )
        db_dish.ingredients = [
            models.MealDishIngredient(name=name) for name in dish.ingredients
        ]
        db_meal.dishes.append(db_dish)
        if dish.is_batch_cooked:
            db.add(
                models.FridgeItem(
                    household_id=current_user.household_id,
                    name=dish.name,
                    category="作り置き料理",
                    added_date=meal.date,
                )
            )
    for category, values in meal.tags.model_dump().items():
        for value in values:
            db_meal.tags.append(models.MealTag(category=category, value=value))

    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return _meal_to_out(db_meal)


@router.post("/{meal_id}/confirm", response_model=schemas.MealOut)
def confirm_meal(
    meal_id: int,
    request: schemas.ConfirmMealRequest = schemas.ConfirmMealRequest(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """献立提案の下書きを正式な献立として確定する(#38)。作り置き品目があれば冷蔵庫へ登録する。"""
    db_meal = (
        db.query(models.Meal)
        .filter(
            models.Meal.id == meal_id,
            models.Meal.household_id == current_user.household_id,
        )
        .first()
    )
    if db_meal is None:
        raise HTTPException(status_code=404, detail="meal not found")

    db_meal.is_draft = False
    for dish in db_meal.dishes:
        if dish.name in request.batch_cooked_dish_names:
            dish.is_batch_cooked = True
        if dish.is_batch_cooked:
            db.add(
                models.FridgeItem(
                    household_id=current_user.household_id,
                    name=dish.name,
                    category="作り置き料理",
                    added_date=db_meal.date,
                )
            )
    db.commit()
    db.refresh(db_meal)
    return _meal_to_out(db_meal)


@router.delete("/{meal_id}", status_code=204)
def delete_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_meal = (
        db.query(models.Meal)
        .filter(
            models.Meal.id == meal_id,
            models.Meal.household_id == current_user.household_id,
        )
        .first()
    )
    if db_meal is None:
        raise HTTPException(status_code=404, detail="meal not found")
    db.delete(db_meal)
    db.commit()
