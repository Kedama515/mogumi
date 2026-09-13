import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..tag_utils import tags_to_schema

router = APIRouter()


def _recipe_to_out(recipe: models.Recipe) -> schemas.RecipeOut:
    return schemas.RecipeOut(
        id=recipe.id,
        dish_name=recipe.dish_name,
        source_url=recipe.source_url or "",
        ingredients=json.loads(recipe.ingredients),
        steps=json.loads(recipe.steps),
        memo=recipe.memo or "",
        tags=tags_to_schema(recipe.tags),
    )


@router.get("", response_model=list[schemas.RecipeOut])
def list_recipes(db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).order_by(models.Recipe.dish_name).all()
    return [_recipe_to_out(r) for r in recipes]


@router.get("/{recipe_id}", response_model=schemas.RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    return _recipe_to_out(recipe)


@router.post("", response_model=schemas.RecipeOut, status_code=201)
def create_recipe(recipe: schemas.RecipeIn, db: Session = Depends(get_db)):
    db_recipe = models.Recipe(
        dish_name=recipe.dish_name,
        source_url=recipe.source_url,
        ingredients=json.dumps(recipe.ingredients, ensure_ascii=False),
        steps=json.dumps(recipe.steps, ensure_ascii=False),
        memo=recipe.memo,
    )
    for category, values in recipe.tags.model_dump().items():
        for value in values:
            db_recipe.tags.append(models.RecipeTag(category=category, value=value))

    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return _recipe_to_out(db_recipe)


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    db.delete(recipe)
    db.commit()
