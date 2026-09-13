from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services.claude_client import propose_menu
from ..services.suggestion_prompt import build_prompt

router = APIRouter()


@router.post("", response_model=schemas.SuggestionResponse)
def suggest_menu(request: schemas.SuggestionRequest, db: Session = Depends(get_db)):
    prompt = build_prompt(
        db=db,
        meal_type=request.meal_type,
        servings=request.servings,
        user_request=request.user_request,
        lookback_days=request.lookback_days,
    )
    menu_data, usage = propose_menu(prompt)
    return schemas.SuggestionResponse(**menu_data, api_usage=usage)
