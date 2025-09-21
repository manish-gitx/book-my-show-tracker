from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    language = Column(String, nullable=False)
    rating = Column(String, nullable=True)  # e.g., "UA13+", "A"
    format_type = Column(String, nullable=True)  # e.g., "2D", "3D", "IMAX"
    bms_movie_id = Column(String, nullable=True)  # e.g., "ET00436673"
    bms_url_path = Column(String, nullable=True)  # e.g., "/movies/hyderabad/demon-slayer-kimetsu-no-yaiba-infinity-castle/ET00436673"
    show_date = Column(Date, nullable=False, index=True)
    theater_id = Column(Integer, ForeignKey("theaters.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    theater = relationship("Theater", back_populates="movies")
    showtimes = relationship("Showtime", back_populates="movie", cascade="all, delete-orphan")

class Showtime(Base):
    __tablename__ = "showtimes"
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    show_time = Column(String, nullable=False)  # e.g., "09:20 AM"
    screen_type = Column(String, nullable=True)  # e.g., "PCX SCREEN"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    movie = relationship("Movie", back_populates="showtimes")
