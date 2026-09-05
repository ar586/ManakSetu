from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_db
from app.models.standard import Standard as StandardModel
from app.schemas.standard import Standard as StandardSchema

router = APIRouter()

@router.get("/{standard_id}", response_model=StandardSchema)
def get_standard(standard_id: str, db: Session = Depends(get_db)):
    """
    Fetch details of a specific standard by ID.
    """
    standard = db.query(StandardModel).filter(StandardModel.id == standard_id).first()
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    return standard

@router.get("/", response_model=List[StandardSchema])
def list_standards(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    List all standard metadata (paginated).
    """
    standards = db.query(StandardModel).offset(skip).limit(limit).all()
    return standards
