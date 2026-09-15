from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user

router = APIRouter()


@router.get("/settings", response_model=schemas.HouseholdSettings)
def get_household_settings(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    household = db.get(models.Household, current_user.household_id)
    return household


@router.put("/settings", response_model=schemas.HouseholdSettings)
def update_household_settings(
    settings: schemas.HouseholdSettings,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    household = db.get(models.Household, current_user.household_id)
    household.default_servings = settings.default_servings
    household.default_lookback_days = settings.default_lookback_days
    db.commit()
    db.refresh(household)
    return household
