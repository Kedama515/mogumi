from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services.ingredient_categorizer import resolve_category

router = APIRouter()


@router.get("", response_model=list[schemas.PantryItemOut])
def list_pantry_items(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.PantryItem)
        .filter(models.PantryItem.household_id == current_user.household_id)
        .order_by(models.PantryItem.category, models.PantryItem.name)
        .all()
    )


@router.post("", response_model=schemas.PantryItemOut, status_code=201)
def add_pantry_item(
    item: schemas.PantryItemIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_item = models.PantryItem(
        household_id=current_user.household_id,
        name=item.name,
        category=resolve_category(db, item.name),
        memo=item.memo,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=204)
def delete_pantry_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_item = (
        db.query(models.PantryItem)
        .filter(
            models.PantryItem.id == item_id,
            models.PantryItem.household_id == current_user.household_id,
        )
        .first()
    )
    if db_item is None:
        raise HTTPException(status_code=404, detail="item not found")
    db.delete(db_item)
    db.commit()
