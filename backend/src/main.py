"""
AI Database Query Tool - FastAPI Backend

Entry point for the backend service.
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router
from src.database.sqlite_db import init_database
from src.database.mysql_pool import MySQLPoolManager
from src.services.encryption import Encryptor

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: initialize database and encryption
    init_database()
    Encryptor.initialize()
    yield
    # Shutdown: close all MySQL pools
    await MySQLPoolManager.close_all_pools()


app = FastAPI(
    title="AI Database Query Tool",
    description="Multi-database query tool with natural language support",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
