import asyncio
import logging
from typing import Optional
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.config import settings
from app.database import SessionLocal
from app.models import User, Notification
from app.services.parser import BookMyShowParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBotService:
    """Telegram bot service for notifications and user interaction"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.bot = None
        self.application = None
        self.parser = BookMyShowParser()
        
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
            self.application = Application.builder().token(self.bot_token).build()
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup command and message handlers"""
        if not self.application:
            return
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("subscribe", self._subscribe_command))
        self.application.add_handler(CommandHandler("list", self._list_subscriptions))
        self.application.add_handler(CommandHandler("unsubscribe", self._unsubscribe_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Create or get user in database
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.telegram_id == str(user.id)).first()
            if not db_user:
                db_user = User(
                    telegram_id=str(user.id),
                    telegram_username=user.username
                )
                db.add(db_user)
                db.commit()
            
            welcome_message = (
                "🎬 Welcome to BookMyShow Movie Tracker!\n\n"
                "I'll help you track movie showtimes and notify you when:\n"
                "• New movies become available\n"
                "• New showtimes are added\n\n"
                "Commands:\n"
                "/subscribe - Start tracking a movie\n"
                "/list - View your subscriptions\n"
                "/unsubscribe - Stop tracking a movie\n"
                "/help - Show this help message\n\n"
                "To get started, send me a BookMyShow theater URL!"
            )
            
            await update.message.reply_text(welcome_message)
            
        finally:
            db.close()
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🎬 BookMyShow Movie Tracker Help\n\n"
            "How to use:\n"
            "1. Send me a BookMyShow theater URL\n"
            "2. I'll extract theater and date info\n"
            "3. Confirm the details\n"
            "4. Tell me which movie to track\n"
            "5. Get notifications for new shows!\n\n"
            "Example URL:\n"
            "https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20250924\n\n"
            "Commands:\n"
            "/start - Start using the bot\n"
            "/subscribe - Start tracking a movie\n"
            "/list - View your subscriptions\n"
            "/unsubscribe - Stop tracking a movie\n"
            "/help - Show this help message"
        )
        
        await update.message.reply_text(help_message)
    
    async def _subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        await update.message.reply_text(
            "To subscribe to movie notifications, please send me a BookMyShow theater URL.\n\n"
            "Example:\n"
            "https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20250924"
        )
    
    async def _list_subscriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command"""
        user = update.effective_user
        db = SessionLocal()
        
        try:
            db_user = db.query(User).filter(User.telegram_id == str(user.id)).first()
            if not db_user:
                await update.message.reply_text("You don't have any subscriptions yet. Use /subscribe to start!")
                return
            
            subscriptions = [sub for sub in db_user.subscriptions if sub.is_active]
            
            if not subscriptions:
                await update.message.reply_text("You don't have any active subscriptions. Use /subscribe to start!")
                return
            
            message = "📋 Your Active Subscriptions:\n\n"
            for i, sub in enumerate(subscriptions, 1):
                message += f"{i}. Movie: {sub.movie_name}\n"
                message += f"   Theater: {sub.theater.name}\n"
                message += f"   Date: {sub.target_date.strftime('%B %d, %Y')}\n"
                message += f"   ID: {sub.id}\n\n"
            
            message += "To unsubscribe, use: /unsubscribe <ID>"
            await update.message.reply_text(message)
            
        finally:
            db.close()
    
    async def _unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unsubscribe command"""
        if not context.args:
            await update.message.reply_text("Please provide subscription ID. Use /list to see your subscriptions.")
            return
        
        try:
            subscription_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid subscription ID. Please provide a valid number.")
            return
        
        user = update.effective_user
        db = SessionLocal()
        
        try:
            from app.models import UserSubscription
            subscription = db.query(UserSubscription).filter(
                UserSubscription.id == subscription_id,
                UserSubscription.user.has(telegram_id=str(user.id)),
                UserSubscription.is_active == True
            ).first()
            
            if not subscription:
                await update.message.reply_text("Subscription not found or already inactive.")
                return
            
            subscription.is_active = False
            subscription.deactivated_reason = 'user_unsubscribed'
            subscription.deactivated_at = datetime.now()
            db.commit()
            
            await update.message.reply_text(
                f"✅ Successfully unsubscribed from '{subscription.movie_name}' "
                f"at {subscription.theater.name}"
            )
            
        finally:
            db.close()
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        message_text = update.message.text.strip()
        
        # Check if it's a BookMyShow URL
        if "bookmyshow.com" in message_text and "cinemas" in message_text:
            await self._handle_bms_url(update, message_text)
        else:
            await update.message.reply_text(
                "Please send me a BookMyShow theater URL to start tracking movies.\n\n"
                "Use /help for more information."
            )
    
    async def _handle_bms_url(self, update: Update, url: str):
        """Handle BookMyShow URL parsing and confirmation"""
        try:
            url_info = self.parser.parse_bms_url(url)
            
            confirmation_message = (
                "🎭 Theater Information Extracted:\n\n"
                f"🏢 Theater: {url_info['display_name']}\n"
                f"🌍 City: {url_info['city'].title()}\n"
                f"📅 Date: {url_info['formatted_date']}\n"
                f"🔗 Code: {url_info['theater_code']}\n\n"
                "Is this information correct? If yes, please tell me which movie you want to track.\n\n"
                "Example: 'Demon Slayer' or 'Jolly LLB'"
            )
            
            await update.message.reply_text(confirmation_message)
            
            # Store URL info in user context for next steps
            # In a real implementation, you'd want to use a more persistent storage
            # For now, we'll just acknowledge the URL
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Error parsing URL: {str(e)}")
    
    async def send_notification(self, user_telegram_id: str, message: str) -> bool:
        """Send notification to a specific user"""
        if not self.bot:
            logger.error("Telegram bot not configured")
            return False
        
        try:
            await self.bot.send_message(chat_id=user_telegram_id, text=message)
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {user_telegram_id}: {e}")
            return False
    
    async def process_pending_notifications(self):
        """Process and send pending notifications"""
        if not self.bot:
            return
        
        db = SessionLocal()
        try:
            # Get unsent notifications
            notifications = db.query(Notification).filter(
                Notification.is_sent == False
            ).limit(50).all()  # Process in batches
            
            for notification in notifications:
                user = notification.user
                if user.telegram_id:
                    success = await self.send_notification(user.telegram_id, notification.message)
                    
                    if success:
                        notification.is_sent = True
                        notification.sent_via = 'telegram'
                        notification.sent_at = func.now()
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing notifications: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def start_bot(self):
        """Start the Telegram bot"""
        if not self.application:
            logger.error("Telegram bot not configured - missing bot token")
            return
        
        try:
            await self.application.initialize()
            await self.application.start()
            logger.info("Telegram bot started successfully")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.application:
            try:
                await self.application.stop()
                logger.info("Telegram bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram bot: {e}")

# Global bot instance
telegram_bot = TelegramBotService()
