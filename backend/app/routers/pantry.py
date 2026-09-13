from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.PantryItemOut])
def list_pantry_items(db: Session = Depends(get_db)):
    return db.query(models.PantryItem).order_by(models.PantryItem.name).all()


@router.post("", response_model=schemas.PantryItemOut, status_code=201)
def add_pantry_item(item: schemas.PantryItemIn, db: Session = Depends(get_db)):
    db_item = models.PantryItem(name=item.name, memo=item.memo)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=204)
def delete_pantry_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.get(models.PantryItem, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="item not found")
    db.delete(db_item)
    db.commit()
