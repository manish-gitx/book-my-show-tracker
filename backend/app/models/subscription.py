from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    theater_id = Column(Integer, ForeignKey("theaters.id"), nullable=False)
    movie_name = Column(String, nullable=False, index=True)  # Partial name for matching
    target_date = Column(Date, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    notify_new_shows = Column(Boolean, default=True)
    notify_new_times = Column(Boolean, default=True)
    deactivated_reason = Column(String, nullable=True)  # 'notification_sent', 'user_unsubscribed', etc.
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    theater = relationship("Theater", back_populates="subscriptions")
