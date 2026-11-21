from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import models
from . import schemas
from .database import get_db

router = APIRouter(
    prefix="/api/items",
    tags=["Items (Chá»§ Ä‘á» 13)"]
)

@router.post("/", response_model=schemas.ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    try:
        new_item = models.Item(**item.model_dump())
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    except SQLAlchemyError as e:
        db.rollback()
        # Log lá»—i ra console cho Dev, tráº£ vá» lá»—i 500 cho Frontend
        print(f"Database Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Lá»—i há»‡ thá»‘ng khi lÆ°u dá»¯ liá»‡u.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="ÄÃ£ xáº£y ra lá»—i khÃ´ng xÃ¡c Ä‘á»‹nh.")

@router.get("/", response_model=list[schemas.ItemResponse])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        items = db.query(models.Item).offset(skip).limit(limit).all()
        return items
    except Exception:
        raise HTTPException(status_code=500, detail="KhÃ´ng thá»ƒ táº£i danh sÃ¡ch.")

@router.get("/{item_id}", response_model=schemas.ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"KhÃ´ng tÃ¬m tháº¥y Ä‘á»‘i tÆ°á»£ng vá»›i ID {item_id}")
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Äá»‘i tÆ°á»£ng khÃ´ng tá»“n táº¡i Ä‘á»ƒ xÃ³a.")
    
    try:
        db.delete(item)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lá»—i khi xÃ³a dá»¯ liá»‡u.")
