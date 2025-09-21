from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
from pydantic import BaseModel
from app.database import get_db
from app.models import User, Theater, UserSubscription
from app.services.parser import BookMyShowParser
from app.services.scraper import ScrapingService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Pydantic models
class SubscriptionCreate(BaseModel):
    bms_url: str
    movie_name: str
    telegram_id: str
    notify_new_shows: bool = True
    notify_new_times: bool = True

class SubscriptionResponse(BaseModel):
    id: int
    movie_name: str
    target_date: date
    theater_name: str
    theater_city: str
    is_active: bool
    notify_new_shows: bool
    notify_new_times: bool
    created_at: datetime

class TheaterInfo(BaseModel):
    name: str
    city: str
    code: str
    url_path: str
    date: str
    formatted_date: str

class URLParseResponse(BaseModel):
    success: bool
    theater_info: TheaterInfo = None
    error: str = None

@router.post("/parse-url", response_model=URLParseResponse)
async def parse_bms_url(url: str):
    """Parse BookMyShow URL to extract theater and date information"""
    try:
        parser = BookMyShowParser()
        url_info = parser.parse_bms_url(url)
        
        theater_info = TheaterInfo(
            name=url_info['display_name'],
            city=url_info['city'],
            code=url_info['theater_code'],
            url_path=url_info['theater_path'],
            date=url_info['date'],
            formatted_date=url_info['formatted_date']
        )
        
        return URLParseResponse(success=True, theater_info=theater_info)
    
    except ValueError as e:
        return URLParseResponse(success=False, error=str(e))

@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    """Create a new movie subscription"""
    try:
        # Parse URL
        parser = BookMyShowParser()
        url_info = parser.parse_bms_url(subscription.bms_url)
        
        # Get or create user
        user = db.query(User).filter(User.telegram_id == subscription.telegram_id).first()
        if not user:
            user = User(telegram_id=subscription.telegram_id)
            db.add(user)
            db.flush()
        
        # Get or create theater
        theater = db.query(Theater).filter(Theater.bms_code == url_info['theater_code']).first()
        if not theater:
            theater = Theater(
                name=url_info['display_name'],
                city=url_info['city'],
                bms_code=url_info['theater_code'],
                bms_url_path=url_info['theater_path']
            )
            db.add(theater)
            db.flush()
        
        # Parse date
        target_date = datetime.strptime(url_info['date'], '%Y%m%d').date()
        
        # Check if subscription already exists
        existing = db.query(UserSubscription).filter(
            UserSubscription.user_id == user.id,
            UserSubscription.theater_id == theater.id,
            UserSubscription.movie_name == subscription.movie_name,
            UserSubscription.target_date == target_date
        ).first()
        
        if existing:
            if existing.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subscription already exists for this movie, theater, and date"
                )
            else:
                # Reactivate existing subscription
                existing.is_active = True
                existing.notify_new_shows = subscription.notify_new_shows
                existing.notify_new_times = subscription.notify_new_times
                db.commit()
                db.refresh(existing)
                
                return SubscriptionResponse(
                    id=existing.id,
                    movie_name=existing.movie_name,
                    target_date=existing.target_date,
                    theater_name=existing.theater.name,
                    theater_city=existing.theater.city,
                    is_active=existing.is_active,
                    notify_new_shows=existing.notify_new_shows,
                    notify_new_times=existing.notify_new_times,
                    created_at=existing.created_at
                )
        
        # Create new subscription
        new_subscription = UserSubscription(
            user_id=user.id,
            theater_id=theater.id,
            movie_name=subscription.movie_name,
            target_date=target_date,
            notify_new_shows=subscription.notify_new_shows,
            notify_new_times=subscription.notify_new_times
        )
        
        db.add(new_subscription)
        db.commit()
        db.refresh(new_subscription)
        
        return SubscriptionResponse(
            id=new_subscription.id,
            movie_name=new_subscription.movie_name,
            target_date=new_subscription.target_date,
            theater_name=new_subscription.theater.name,
            theater_city=new_subscription.theater.city,
            is_active=new_subscription.is_active,
            notify_new_shows=new_subscription.notify_new_shows,
            notify_new_times=new_subscription.notify_new_times,
            created_at=new_subscription.created_at
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/user/{telegram_id}", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(telegram_id: str, db: Session = Depends(get_db)):
    """Get all subscriptions for a user"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return []
    
    subscriptions = db.query(UserSubscription).filter(
        UserSubscription.user_id == user.id,
        UserSubscription.is_active == True
    ).all()
    
    result = []
    for sub in subscriptions:
        result.append(SubscriptionResponse(
            id=sub.id,
            movie_name=sub.movie_name,
            target_date=sub.target_date,
            theater_name=sub.theater.name,
            theater_city=sub.theater.city,
            is_active=sub.is_active,
            notify_new_shows=sub.notify_new_shows,
            notify_new_times=sub.notify_new_times,
            created_at=sub.created_at
        ))
    
    return result

@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Deactivate a subscription"""
    subscription = db.query(UserSubscription).filter(UserSubscription.id == subscription_id).first()
    
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    subscription.is_active = False
    db.commit()
    
    return {"message": "Subscription deactivated successfully"}

@router.post("/test-scraping")
async def test_scraping(bms_url: str):
    """Test scraping functionality with a BookMyShow URL"""
    try:
        scraping_service = ScrapingService()
        result = await scraping_service.scrape_and_update_theater(bms_url)
        scraping_service.cleanup()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
