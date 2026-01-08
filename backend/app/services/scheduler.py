import asyncio
import schedule
import threading
import time
from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from app.database import SessionLocal
from app.models import UserSubscription, Theater
from app.services.scraper import ScrapingService
from app.services.movie_tracker import MovieComparisonService
from app.services.email_service import email_service
from app.core.config import settings

class SchedulerService:
    """Service to handle scheduled tasks"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.scraping_service = ScrapingService()
    
    def start_scheduler(self):
        """Start the scheduler in a separate thread"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Schedule tasks
        schedule.every(settings.SCRAPING_INTERVAL_MINUTES).minutes.do(self._run_scraping_job)
        schedule.every(1).minutes.do(self._run_notification_job)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print(f"Scheduler started - scraping every {settings.SCRAPING_INTERVAL_MINUTES} minutes")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.scraping_service.cleanup()
        print("Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def _run_scraping_job(self):
        """Run the scraping job"""
        try:
            asyncio.run(self._scrape_active_subscriptions())
        except Exception as e:
            print(f"Error in scraping job: {e}")
    
    def _run_notification_job(self):
        """Run the notification job"""
        try:
            asyncio.run(self._process_notifications())
        except Exception as e:
            print(f"Error in notification job: {e}")
    
    async def _scrape_active_subscriptions(self):
        """Scrape theaters for active subscriptions"""
        db = SessionLocal()
        try:
            # Get active subscriptions for today and future dates
            today = date.today()
            active_subscriptions = db.query(UserSubscription).filter(
                UserSubscription.is_active == True,
                UserSubscription.target_date >= today
            ).all()
            
            if not active_subscriptions:
                print("No active subscriptions to process")
                return
            
            # Group by theater and date
            theater_dates = {}
            for sub in active_subscriptions:
                key = (sub.theater_id, sub.target_date)
                if key not in theater_dates:
                    theater_dates[key] = []
                theater_dates[key].append(sub)
            
            print(f"Processing {len(theater_dates)} theater-date combinations")
            
            # Process each theater-date combination
            for (theater_id, target_date), subscriptions in theater_dates.items():
                await self._process_theater_date(db, theater_id, target_date, subscriptions)
                
                # Small delay between theaters to avoid overwhelming the server
                await asyncio.sleep(2)
        
        finally:
            db.close()
    
    async def _process_theater_date(self, db: Session, theater_id: int, target_date: date, subscriptions: List[UserSubscription]):
        """Process a specific theater and date"""
        try:
            theater = db.query(Theater).filter(Theater.id == theater_id).first()
            if not theater:
                print(f"Theater {theater_id} not found")
                return
            
            # Build the BookMyShow URL
            date_str = target_date.strftime('%Y%m%d')
            bms_url = f"https://in.bookmyshow.com/cinemas/{theater.bms_url_path}/buytickets/{theater.bms_code}/{date_str}"
            
            print(f"Scraping: {theater.name} for {target_date}")
            
            # Scrape the theater
            result = await self.scraping_service.scrape_and_update_theater(bms_url)
            
            if not result['success']:
                print(f"Failed to scrape {theater.name}: {result.get('error', 'Unknown error')}")
                return
            
            # Process the data with movie comparison service
            comparison_service = MovieComparisonService(db)
            
            # Update database and check for notifications
            await comparison_service.check_subscriptions_and_notify(
                theater_id, 
                target_date, 
                result['data']
            )
            
            # Update database with new data
            comparison_service.update_database_with_new_data(
                theater_id, 
                target_date, 
                result['data']['movies']
            )
            
            print(f"Successfully processed {theater.name} - found {result['data']['total_movies']} movies")
            
        except Exception as e:
            print(f"Error processing theater {theater_id} for {target_date}: {e}")
    
    async def _process_notifications(self):
        """Process pending notifications"""
        try:
            await email_service.process_pending_notifications()
        except Exception as e:
            print(f"Error processing notifications: {e}")

# Global scheduler instance
scheduler_service = SchedulerService()

def start_scheduler():
    """Start the global scheduler"""
    scheduler_service.start_scheduler()

def stop_scheduler():
    """Stop the global scheduler"""
    scheduler_service.stop_scheduler()
