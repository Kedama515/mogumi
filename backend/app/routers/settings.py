from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user

router = APIRouter()


@router.get("", response_model=schemas.UserSettings)
def get_settings(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("", response_model=schemas.UserSettings)
def update_settings(
    settings: schemas.UserSettings,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user.default_servings = settings.default_servings
    current_user.avoid_days_dish_name = settings.avoid_days_dish_name
    current_user.avoid_days_genre = settings.avoid_days_genre
    current_user.avoid_days_method_protein = settings.avoid_days_method_protein
    current_user.avoid_days_cuisine = settings.avoid_days_cuisine
    current_user.suggestion_mode = settings.suggestion_mode
    db.commit()
    db.refresh(current_user)
    return current_user
