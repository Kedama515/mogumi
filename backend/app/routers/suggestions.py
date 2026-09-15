from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services.claude_client import propose_menu
from ..services.suggestion_prompt import build_prompt

router = APIRouter()


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
        lookback_days=request.lookback_days,
        target_date=request.target_date,
    )
    menu_data, usage = propose_menu(prompt)
    return schemas.SuggestionResponse(**menu_data, api_usage=usage)
