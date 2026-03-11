"""
Configuration Service - Microservice for managing AI agent configurations.
Handles: Assistants, Phone Numbers, SIP Configs
Includes Redis caching for fast access during calls.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys
from pathlib import Path
# Add parent dir for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.routers import assistants, phone_numbers, sip_configs, workspace_integrations
from config.cache.redis_cache import RedisCache
from services.config.assistant_service import AssistantService
from shared.database.connection import connect_to_database, close_database_connection
from shared.settings import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("config-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Configuration Service...")
    
    # Connect to MongoDB (required for routers)
    await connect_to_database(config.MONGODB_URI, config.MONGODB_DB_NAME)
    logger.info("MongoDB connected")
    
    # Connect to Redis cache
    await RedisCache.connect()

    # One-time startup migration: OpenAI-configured assistants -> Google Gemini pipeline
    migrated_count = await AssistantService.migrate_openai_assistants_to_google()
    if migrated_count:
        logger.info("Assistant migration complete: %d updated", migrated_count)

    logger.info("Configuration Service ready on port 8002")
    
    yield
    
    logger.info("Shutting down Configuration Service...")
    await RedisCache.disconnect()
    await close_database_connection()


app = FastAPI(
    title="Configuration Service",
    description="Microservice for AI agent configurations with Redis caching",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assistants.router, prefix="/assistants", tags=["Assistants"])
app.include_router(phone_numbers.router, prefix="/phone-numbers", tags=["Phone Numbers"])
app.include_router(sip_configs.router, prefix="/sip-configs", tags=["SIP Configs"])
app.include_router(workspace_integrations.router, tags=["Workspace Integrations"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_ok = await RedisCache.ping()
    return {
        "status": "healthy" if redis_ok else "degraded",
        "service": "config",
        "redis": "connected" if redis_ok else "disconnected",
    }


@app.get("/")
async def root():
    return {"service": "Configuration Service", "version": "1.0.0"}
