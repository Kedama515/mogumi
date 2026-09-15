from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services.ingredient_categorizer import resolve_category

router = APIRouter()


@router.get("", response_model=list[schemas.FridgeItemOut])
def list_fridge_items(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.FridgeItem)
        .filter(models.FridgeItem.household_id == current_user.household_id)
        .order_by(models.FridgeItem.category, models.FridgeItem.added_date)
        .all()
    )


@router.post("", response_model=schemas.FridgeItemOut, status_code=201)
def add_fridge_item(
    item: schemas.FridgeItemIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_item = models.FridgeItem(
        household_id=current_user.household_id,
        name=item.name,
        category=resolve_category(db, item.name),
        added_date=item.added_date or date.today(),
        memo=item.memo,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{item_id}", response_model=schemas.FridgeItemOut)
def update_fridge_item_date(
    item_id: int,
    update: schemas.FridgeItemDateUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_item = (
        db.query(models.FridgeItem)
        .filter(
            models.FridgeItem.id == item_id,
            models.FridgeItem.household_id == current_user.household_id,
        )
        .first()
    )
    if db_item is None:
        raise HTTPException(status_code=404, detail="item not found")
    db_item.added_date = update.added_date
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=204)
def delete_fridge_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_item = (
        db.query(models.FridgeItem)
        .filter(
            models.FridgeItem.id == item_id,
            models.FridgeItem.household_id == current_user.household_id,
        )
        .first()
    )
    if db_item is None:
        raise HTTPException(status_code=404, detail="item not found")
    db.delete(db_item)
    db.commit()
