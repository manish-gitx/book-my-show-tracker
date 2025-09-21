from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models import Movie, Showtime

router = APIRouter(prefix="/movies", tags=["movies"])

class ShowtimeResponse(BaseModel):
    id: int
    show_time: str
    screen_type: str = None

class MovieResponse(BaseModel):
    id: int
    title: str
    language: str
    rating: str = None
    format_type: str = None
    bms_movie_id: str = None
    bms_url_path: str = None
    show_date: date
    theater_name: str
    theater_city: str
    showtimes: List[ShowtimeResponse]

@router.get("/theater/{theater_id}", response_model=List[MovieResponse])
async def get_movies_by_theater(
    theater_id: int, 
    show_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get movies for a specific theater and date"""
    query = db.query(Movie).filter(Movie.theater_id == theater_id)
    
    if show_date:
        query = query.filter(Movie.show_date == show_date)
    
    movies = query.all()
    
    result = []
    for movie in movies:
        showtimes = []
        for showtime in movie.showtimes:
            showtimes.append(ShowtimeResponse(
                id=showtime.id,
                show_time=showtime.show_time,
                screen_type=showtime.screen_type
            ))
        
        result.append(MovieResponse(
            id=movie.id,
            title=movie.title,
            language=movie.language,
            rating=movie.rating,
            format_type=movie.format_type,
            bms_movie_id=movie.bms_movie_id,
            bms_url_path=movie.bms_url_path,
            show_date=movie.show_date,
            theater_name=movie.theater.name,
            theater_city=movie.theater.city,
            showtimes=showtimes
        ))
    
    return result

@router.get("/search", response_model=List[MovieResponse])
async def search_movies(
    title: str = None,
    city: str = None,
    language: str = None,
    show_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Search movies by various criteria"""
    query = db.query(Movie)
    
    if title:
        query = query.filter(Movie.title.ilike(f"%{title}%"))
    
    if language:
        query = query.filter(Movie.language.ilike(f"%{language}%"))
    
    if show_date:
        query = query.filter(Movie.show_date == show_date)
    
    if city:
        query = query.join(Movie.theater).filter(Movie.theater.has(city=city))
    
    movies = query.all()
    
    result = []
    for movie in movies:
        showtimes = []
        for showtime in movie.showtimes:
            showtimes.append(ShowtimeResponse(
                id=showtime.id,
                show_time=showtime.show_time,
                screen_type=showtime.screen_type
            ))
        
        result.append(MovieResponse(
            id=movie.id,
            title=movie.title,
            language=movie.language,
            rating=movie.rating,
            format_type=movie.format_type,
            bms_movie_id=movie.bms_movie_id,
            bms_url_path=movie.bms_url_path,
            show_date=movie.show_date,
            theater_name=movie.theater.name,
            theater_city=movie.theater.city,
            showtimes=showtimes
        ))
    
    return result
