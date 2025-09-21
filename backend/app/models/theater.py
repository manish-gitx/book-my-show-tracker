from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Theater(Base):
    __tablename__ = "theaters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    bms_code = Column(String, unique=True, nullable=False, index=True)  # e.g., "PRHN"
    bms_url_path = Column(String, nullable=False)  # e.g., "hyderabad/prasads-multiplex-hyderabad"
    address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    movies = relationship("Movie", back_populates="theater")
    subscriptions = relationship("UserSubscription", back_populates="theater")
