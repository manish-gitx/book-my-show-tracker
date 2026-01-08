from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
from pydantic import BaseModel
from app.database import get_db
from app.models import User, Theater, UserSubscription
from app.services.parser import BookMyShowParser
from app.services.scraper import ScrapingService
from app.services.movie_tracker import MovieComparisonService
from app.services.email_service import email_service
import asyncio

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Test endpoint for email
class TestEmailRequest(BaseModel):
    to_email: str

@router.post("/test-email")
async def test_email(request: TestEmailRequest):
    """Send a test email to verify configuration"""
    success = await email_service.send_email_async(
        recipient_email=request.to_email,
        subject="🎬 Test Email - BookMyShow Tracker",
        message="Hello! This is a test email from your BookMyShow Movie Tracker.\n\nIf you receive this, your email configuration is working correctly! 🎉"
    )
    
    if success:
        return {
            "success": True,
            "message": f"Test email sent successfully to {request.to_email}",
            "note": "Check your inbox (and spam folder)"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send test email. Check server logs for details."
        )

async def send_subscription_confirmation(
    user_email: str, 
    movie_name: str, 
    bms_url: str, 
    theater_name: str, 
    target_date: date
):
    """
    Send immediate confirmation email when subscription is created.
    Checks if movie already exists or not.
    """
    try:
        # Scrape the theater to check current availability
        scraping_service = ScrapingService()
        result = await scraping_service.scrape_and_update_theater(bms_url)
        scraping_service.cleanup()
        
        if not result['success']:
            # If scraping fails, send generic confirmation
            message = f"""🎬 Subscription Created Successfully!

Thank you for subscribing to track '{movie_name}' at {theater_name} on {target_date.strftime('%B %d, %Y')}.

We'll check for availability and notify you as soon as we have updates!

⏱️ We check for new movies and showtimes every 2 minutes.
📧 You'll receive an email when:
  • The movie becomes available
  • New showtimes are added

✅ Your subscription is now active and monitoring!"""
            
            await email_service.send_email_async(
                user_email,
                "🎬 Subscription Confirmed - Movie Tracking Active",
                message
            )
            return
        
        # Use MovieComparisonService to find matching movies
        from app.database import SessionLocal
        temp_db = SessionLocal()
        try:
            comparison_service = MovieComparisonService(temp_db)
            matching_movies = comparison_service.find_matching_movies(
                movie_name, 
                result['data']['movies'],
                threshold=70
            )
            
            if matching_movies:
                # Movie already exists!
                matched_movie = matching_movies[0]
                showtimes_str = ", ".join([show['time'] for show in matched_movie['showtimes']])
                
                message = f"""🎬 Great News! Movie Already Available!

'{matched_movie['title']}' is ALREADY showing at {theater_name}!

📅 Date: {target_date.strftime('%B %d, %Y')}
🎭 Theater: {theater_name}
🗣️ Language: {matched_movie['language']}
⭐ Rating: {matched_movie['rating']}
🕐 Available Showtimes: {showtimes_str}

🎟️ You can book your tickets right now on BookMyShow!

📢 Don't worry, we'll keep monitoring:
  • We'll notify you if NEW showtimes are added
  • We'll alert you if the movie schedule changes

✅ Your subscription is active and watching for updates!

Happy watching! 🍿"""
                
                await email_service.send_email_async(
                    user_email,
                    f"✅ '{matched_movie['title']}' is Available Now!",
                    message
                )
            else:
                # Movie doesn't exist yet
                message = f"""🎬 Subscription Activated - Movie Not Available Yet

Thank you for subscribing to track '{movie_name}'!

📅 Target Date: {target_date.strftime('%B %d, %Y')}
🎭 Theater: {theater_name}

📊 Current Status: The movie is not yet showing at this theater on this date.

🔔 We'll notify you immediately when:
  • The movie becomes available
  • Showtimes are added to the schedule

⏱️ We're checking every 2 minutes, so you'll be among the first to know!

✅ Your subscription is active. Sit back and relax - we've got this covered!

We'll send you an email as soon as '{movie_name}' appears in the schedule. 📧"""
                
                await email_service.send_email_async(
                    user_email,
                    f"🔔 Tracking '{movie_name}' - We'll Notify You!",
                    message
                )
        finally:
            temp_db.close()
            
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        # Don't fail the subscription creation if email fails

# Pydantic models
class SubscriptionCreate(BaseModel):
    bms_url: str
    movie_name: str
    email: str
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
        user = db.query(User).filter(User.email == subscription.email).first()
        if not user:
            user = User(email=subscription.email)
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
                
                ##Send confirmation email for reactivated subscription
                asyncio.create_task(
                    send_subscription_confirmation(
                        subscription.email,
                        subscription.movie_name,
                        subscription.bms_url,
                        existing.theater.name,
                        target_date
                    )
                )
                
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
        
        # Send immediate confirmation email based on current availability
        asyncio.create_task(
            send_subscription_confirmation(
                subscription.email,
                subscription.movie_name,
                subscription.bms_url,
                theater.name,
                target_date
            )
        )
        
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

@router.get("/user/{email}", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(email: str, db: Session = Depends(get_db)):
    """Get all subscriptions for a user"""
    user = db.query(User).filter(User.email == email).first()
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
