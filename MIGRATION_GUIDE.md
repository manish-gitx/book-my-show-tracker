# Migration Guide: Telegram → Email Notifications

This guide explains how to migrate from Telegram notifications to Gmail notifications.

## 🎯 What Changed?

### Backend Changes:
1. ✅ **Removed**: Telegram bot service and dependencies
2. ✅ **Added**: Gmail email notification service
3. ✅ **Updated**: User model now uses `email` instead of `telegram_id`
4. ✅ **Updated**: Notification system sends emails instead of Telegram messages
5. ✅ **Updated**: Configuration to use Gmail credentials

### Frontend Changes:
1. ✅ **Updated**: All forms now ask for email instead of Telegram ID
2. ✅ **Updated**: Subscription management uses email lookup
3. ✅ **Updated**: User-facing text mentions email notifications

## 📋 Migration Steps

### Step 1: Backup Your Database
```bash
cd backend
cp bookmyshow_tracker.db bookmyshow_tracker.db.backup
```

### Step 2: Run Migration Script
```bash
cd backend
python migrate_to_email.py
```

### Step 3: Update Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend (no changes needed)
cd frontend
npm install
```

### Step 4: Configure Gmail Credentials

#### Option A: Use .env file (Recommended)
Create a `.env` file in the `backend` directory:
```env
GMAIL_USERNAME=manish.23bcs10099@sst.scaler.com
GMAIL_APP_PASSWORD=ytvgsvzdmladyucd
```

#### Option B: Update config.py directly
The credentials are already set in `backend/app/core/config.py`:
```python
GMAIL_USERNAME: Optional[str] = "manish.23bcs10099@sst.scaler.com"
GMAIL_APP_PASSWORD: Optional[str] = "ytvgsvzdmladyucd"
```

### Step 5: Generate Gmail App Password (if needed)

If you need to use a different Gmail account:

1. Go to Google Account settings
2. Navigate to Security → 2-Step Verification
3. Scroll to "App passwords"
4. Generate a new app password for "Mail"
5. Update the credentials in your `.env` or `config.py`

### Step 6: Start the Application

#### Backend:
```bash
cd backend
# Activate venv if needed
source ../venv/bin/activate  # On macOS/Linux
# or
..\venv\Scripts\activate  # On Windows

python -m uvicorn app.main:app --reload
```

#### Frontend:
```bash
cd frontend
npm start
```

## 🧪 Testing the Email Notifications

### 1. Create a Test Subscription
- Go to http://localhost:3000
- Enter a BookMyShow URL
- Enter your email address
- Complete the subscription

### 2. Verify Email Sending
The backend will:
- Check for new movies every 2 minutes
- Send email notifications when changes are detected
- Log all email activities to console

### 3. Check Logs
Watch the backend console for messages like:
```
Email sent successfully to: your.email@example.com
Processing 1 pending notifications
Email notification service configured and ready
```

## 📧 Email Notification Features

### Email Format:
- **Subject**: 🎬 Movie Alert - BookMyShow Tracker
- **HTML Template**: Beautiful, responsive email design
- **Content**: 
  - Movie name and theater
  - Show date and times
  - Language and rating info
  - Automatic unsubscribe notification

### Example Email:
```
🎬 Movie Alert!

'Demon Slayer: Kimetsu no Yaiba' is now available at Prasads Multiplex
Date: September 24, 2025
Language: Japanese
Rating: UA
Showtimes: 10:00 AM, 1:00 PM, 4:00 PM, 7:00 PM

Book now on BookMyShow!

✅ Your subscription has been automatically stopped since the movie is now available.
```

## 🔧 Troubleshooting

### Problem: "Gmail not configured" error
**Solution**: Check that `GMAIL_USERNAME` and `GMAIL_APP_PASSWORD` are set correctly.

### Problem: "Authentication failed" error
**Solution**: 
1. Verify your app password is correct
2. Enable "Less secure app access" if using a regular password (not recommended)
3. Use an app-specific password instead

### Problem: Emails not sending
**Solution**:
1. Check the backend logs for error messages
2. Verify your Gmail account allows SMTP access
3. Check if notifications are being created in the database
4. Ensure the scheduler is running (check console output)

### Problem: Old users can't be found
**Solution**: Old users with only Telegram IDs need to re-subscribe with their email addresses.

## 🎯 Next Steps

1. ✅ All users must re-subscribe using their email addresses
2. ✅ Test email notifications with a real subscription
3. ✅ Monitor backend logs for any issues
4. ✅ Consider setting up email rate limiting if needed

## 📝 Important Notes

1. **Auto-unsubscribe**: Subscriptions are automatically deactivated after sending a notification
2. **Rate Limiting**: Small delays (0.5s) between emails to avoid Gmail rate limits
3. **HTML Emails**: Emails are sent in both plain text and HTML format
4. **Error Handling**: Failed emails are logged but don't crash the service

## 🔐 Security Recommendations

1. **Never commit** `.env` files or credentials to Git
2. Add `.env` to your `.gitignore`
3. Use **App Passwords** instead of regular passwords
4. Rotate credentials periodically
5. Monitor your Gmail account for unusual activity

## 📞 Support

If you encounter issues:
1. Check the backend console logs
2. Review the `MIGRATION_GUIDE.md` (this file)
3. Verify your Gmail settings
4. Test with a simple email first

---

**Migration completed successfully! 🎉**

Your BookMyShow tracker now uses email notifications instead of Telegram!

