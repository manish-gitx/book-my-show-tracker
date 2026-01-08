import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./bookmyshow_tracker.db"
    
    # Email Configuration (Brevo API) - Real values loaded from .env file
    brevo_api_key: str = ""
    brevo_api_url: str = "https://api.brevo.com/v3/smtp/email"
    email_from: str = ""
    email_from_name: str = "BookMyShow Movie Tracker"
    SCRAPING_INTERVAL_MINUTES: int = 2
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"

settings = Settings()
