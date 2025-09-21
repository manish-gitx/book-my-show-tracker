from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models import Theater

router = APIRouter(prefix="/theaters", tags=["theaters"])

class TheaterResponse(BaseModel):
    id: int
    name: str
    city: str
    bms_code: str
    bms_url_path: str
    address: str = None

@router.get("/search", response_model=List[TheaterResponse])
async def search_theaters(city: str = None, name: str = None, db: Session = Depends(get_db)):
    """Search theaters by city or name"""
    query = db.query(Theater)
    
    if city:
        query = query.filter(Theater.city.ilike(f"%{city}%"))
    
    if name:
        query = query.filter(Theater.name.ilike(f"%{name}%"))
    
    theaters = query.all()
    
    result = []
    for theater in theaters:
        result.append(TheaterResponse(
            id=theater.id,
            name=theater.name,
            city=theater.city,
            bms_code=theater.bms_code,
            bms_url_path=theater.bms_url_path,
            address=theater.address
        ))
    
    return result

@router.get("/{theater_id}", response_model=TheaterResponse)
async def get_theater(theater_id: int, db: Session = Depends(get_db)):
    """Get theater by ID"""
    theater = db.query(Theater).filter(Theater.id == theater_id).first()
    
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    
    return TheaterResponse(
        id=theater.id,
        name=theater.name,
        city=theater.city,
        bms_code=theater.bms_code,
        bms_url_path=theater.bms_url_path,
        address=theater.address
    )
