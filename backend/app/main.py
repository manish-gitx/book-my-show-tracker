from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
from contextlib import asynccontextmanager

from app.database import get_db, init_db
from app.routers import subscriptions, theaters, movies
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.telegram_bot import telegram_bot
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    start_scheduler()
    
    # Start Telegram bot if configured
    if settings.TELEGRAM_BOT_TOKEN:
        await telegram_bot.start_bot()
        print("Telegram bot started")
    else:
        print("Telegram bot not configured - missing TELEGRAM_BOT_TOKEN")
    
    yield
    
    # Shutdown
    stop_scheduler()
    
    # Stop Telegram bot
    if settings.TELEGRAM_BOT_TOKEN:
        await telegram_bot.stop_bot()

app = FastAPI(
    title="BookMyShow Movie Tracker",
    description="Real-time movie show tracker with notifications",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(theaters.router, prefix="/api/v1")
app.include_router(movies.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "BookMyShow Movie Tracker API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
