from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.FridgeItemOut])
def list_fridge_items(db: Session = Depends(get_db)):
    return db.query(models.FridgeItem).order_by(models.FridgeItem.added_date).all()


@router.post("", response_model=schemas.FridgeItemOut, status_code=201)
def add_fridge_item(item: schemas.FridgeItemIn, db: Session = Depends(get_db)):
    db_item = models.FridgeItem(
        name=item.name,
        added_date=item.added_date or date.today(),
        memo=item.memo,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=204)
def delete_fridge_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.get(models.FridgeItem, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="item not found")
    db.delete(db_item)
    db.commit()
