"""
API Gateway - Main entry point for the Voice AI Platform.
Routes requests to microservices, handles auth, and CORS.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

import sys
from pathlib import Path
# Add parent dir for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gateway")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager."""
        from shared.settings import config
        from shared.database import connect_to_database, close_database_connection
        
        logger.info("Starting API Gateway...")
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        
        # Connect to MongoDB
        await connect_to_database(config.MONGODB_URI, config.MONGODB_DB_NAME)
        logger.info("MongoDB connected")
        
        yield
        
        # Shutdown
        logger.info("Shutting down API Gateway...")
        await close_database_connection()
    
    # Create app
    app = FastAPI(
        title="Vobiz Voice AI Platform - Gateway",
        description="API Gateway for Voice AI Platform microservices",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add Rate Limiting
    from shared.middleware.rate_limiter import RateLimitMiddleware, rate_limiter
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
    
    # Register routers
    from gateway.routers import calls, health, assistants, phone_numbers, sip_configs, campaigns, tools, job_queue, auth, knowledge
    from shared.auth.dependencies import get_current_user
    
    # Public routes (no auth required)
    app.include_router(health.router, tags=["Health"])
    app.include_router(auth.router, prefix="/api", tags=["Authentication"])
    
    # Protected routes (require auth when AUTH_ENABLED=true)
    app.include_router(assistants.router, prefix="/api", tags=["Assistants"], dependencies=[Depends(get_current_user)])
    app.include_router(phone_numbers.router, prefix="/api", tags=["Phone Numbers"], dependencies=[Depends(get_current_user)])
    app.include_router(sip_configs.router, prefix="/api", tags=["SIP Configs"], dependencies=[Depends(get_current_user)])
    app.include_router(campaigns.router, prefix="/api", tags=["Campaigns"], dependencies=[Depends(get_current_user)])
    app.include_router(tools.router, prefix="/api", tags=["Tools"], dependencies=[Depends(get_current_user)])
    app.include_router(knowledge.router, prefix="/api", tags=["Knowledge"], dependencies=[Depends(get_current_user)])
    app.include_router(calls.router, prefix="/api", tags=["Calls"], dependencies=[Depends(get_current_user)])
    app.include_router(job_queue.router, prefix="/api", tags=["Queue"], dependencies=[Depends(get_current_user)])
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    from shared.settings import config
    
    uvicorn.run(
        "gateway.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
    )
