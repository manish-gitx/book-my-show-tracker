import httpx
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.config import settings
from app.database import SessionLocal
from app.models import Notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending email notifications using Brevo API"""
    
    def __init__(self):
        self.api_key = settings.brevo_api_key
        self.api_url = settings.brevo_api_url
        self.email_from = settings.email_from
        self.email_from_name = settings.email_from_name
        logger.info(f"🔧 EmailService initialized")
        logger.info(f"   API URL: {self.api_url}")
        logger.info(f"   From: {self.email_from_name} <{self.email_from}>")
        logger.info(f"   API Key: {'✓ Configured' if self.api_key else '❌ Missing'}")
    
    def send_email_sync(self, recipient_email: str, subject: str, message: str) -> bool:
        """Send email using Brevo API (synchronous) - Text content only"""
        logger.info(f"=" * 60)
        logger.info(f"Starting email send process to: {recipient_email}")
        logger.info(f"Subject: {subject}")
        
        if not self.api_key:
            logger.error("❌ Brevo API key not configured")
            return False
        
        logger.info(f"✓ API Key configured: {self.api_key[:10]}...")
        
        try:
            # Format text content nicely
            text_content = f"""
🎬 BookMyShow Movie Tracker
{'=' * 50}

{message}

{'=' * 50}
You received this email because you subscribed to movie notifications.
Visit the app to manage your subscriptions.
"""
            
            # Prepare the email payload for Brevo API (text only)
            payload = {
                "sender": {
                    "name": self.email_from_name,
                    "email": self.email_from
                },
                "to": [
                    {
                        "email": recipient_email,
                        "name": recipient_email.split('@')[0]
                    }
                ],
                "subject": subject,
                "textContent": text_content
            }
            
            logger.info(f"📧 Email payload prepared:")
            logger.info(f"  - From: {self.email_from_name} <{self.email_from}>")
            logger.info(f"  - To: {recipient_email}")
            logger.info(f"  - Subject: {subject}")
            logger.info(f"  - Content length: {len(text_content)} chars")
            
            # Send via Brevo API
            headers = {
                "accept": "application/json",
                "api-key": self.api_key,
                "content-type": "application/json"
            }
            
            logger.info(f"🚀 Sending POST request to: {self.api_url}")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, json=payload, headers=headers)
                
                logger.info(f"📥 Response received:")
                logger.info(f"  - Status Code: {response.status_code}")
                logger.info(f"  - Response Body: {response.text}")
                
                response.raise_for_status()
                
                # Parse response
                response_data = response.json()
                message_id = response_data.get('messageId', 'N/A')
                
                logger.info(f"✅ Email sent successfully!")
                logger.info(f"  - Recipient: {recipient_email}")
                logger.info(f"  - Message ID: {message_id}")
                logger.info(f"=" * 60)
                
                return True
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP Error sending email:")
            logger.error(f"  - Status Code: {e.response.status_code}")
            logger.error(f"  - Response: {e.response.text}")
            logger.error(f"  - Recipient: {recipient_email}")
            logger.error(f"=" * 60)
            return False
        
        except httpx.TimeoutException as e:
            logger.error(f"❌ Timeout error sending email to {recipient_email}")
            logger.error(f"  - Error: {str(e)}")
            logger.error(f"=" * 60)
            return False
        
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email to {recipient_email}")
            logger.error(f"  - Error type: {type(e).__name__}")
            logger.error(f"  - Error message: {str(e)}")
            logger.error(f"=" * 60)
            return False
    
    async def send_email_async(self, recipient_email: str, subject: str, message: str) -> bool:
        """Send email asynchronously"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                self.send_email_sync,
                recipient_email,
                subject,
                message
            )
        return result
    
    async def send_notification(self, user_email: str, message: str) -> bool:
        """Send notification to a specific user"""
        subject = "🎬 Movie Alert - BookMyShow Tracker"
        logger.info(f"📤 Preparing to send notification email...")
        logger.info(f"   To: {user_email}")
        logger.info(f"   Message preview: {message[:100]}...")
        result = await self.send_email_async(user_email, subject, message)
        return result
    
    async def process_pending_notifications(self):
        """Process and send pending notifications"""
        logger.info("\n" + "🔔 " * 20)
        logger.info("Starting notification processing job...")
        
        if not self.api_key:
            logger.warning("⚠️  Email not configured - skipping notification processing")
            logger.warning("   Please set BREVO_API_KEY in .env file")
            return
        
        db = SessionLocal()
        try:
            # Get unsent notifications
            notifications = db.query(Notification).filter(
                Notification.is_sent == False
            ).limit(50).all()  # Process in batches
            
            if not notifications:
                logger.info("✓ No pending notifications to process")
                logger.info("🔔 " * 20 + "\n")
                return
            
            logger.info(f"📬 Found {len(notifications)} pending notification(s) to process")
            
            success_count = 0
            failed_count = 0
            
            for idx, notification in enumerate(notifications, 1):
                user = notification.user
                logger.info(f"\n--- Processing notification {idx}/{len(notifications)} ---")
                logger.info(f"Notification ID: {notification.id}")
                logger.info(f"User ID: {user.id}")
                logger.info(f"User Email: {user.email}")
                
                if user.email:
                    success = await self.send_notification(user.email, notification.message)
                    
                    if success:
                        notification.is_sent = True
                        notification.sent_via = 'email'
                        notification.sent_at = func.now()
                        success_count += 1
                        logger.info(f"✅ Notification {notification.id} marked as sent")
                    else:
                        failed_count += 1
                        logger.error(f"❌ Failed to send notification {notification.id}")
                    
                    # Small delay to avoid rate limiting
                    logger.info("⏱️  Waiting 0.5s to avoid rate limiting...")
                    await asyncio.sleep(0.5)
                else:
                    logger.warning(f"⚠️  User {user.id} has no email configured - skipping")
                    failed_count += 1
            
            db.commit()
            logger.info("\n" + "=" * 60)
            logger.info(f"📊 Notification Processing Summary:")
            logger.info(f"   ✅ Successfully sent: {success_count}")
            logger.info(f"   ❌ Failed: {failed_count}")
            logger.info(f"   📝 Total processed: {len(notifications)}")
            logger.info("=" * 60)
            logger.info("🔔 " * 20 + "\n")
            
        except Exception as e:
            logger.error(f"\n❌ CRITICAL ERROR processing notifications:")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error message: {str(e)}")
            logger.error(f"   Rolling back database changes...")
            db.rollback()
            logger.error("🔔 " * 20 + "\n")
        finally:
            db.close()


# Global email service instance
email_service = EmailService()

