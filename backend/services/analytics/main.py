"""
Analytics Service - Call management, recordings, and reports.
Port: 8001
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from shared.settings import config
from shared.database.connection import connect_to_database, close_database_connection, get_database
from shared.database.models import CallRecord, CallStatus, CreateCallRequest, CallResponse
from shared.auth.dependencies import get_current_user, get_current_user_optional
from shared.auth.models import User

from .call_service import CallService
from .analysis_service import AnalysisService
from .webhook_service import WebhookService
from .s3_service import S3Service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Analytics Service...")
    await connect_to_database(config.MONGODB_URI, config.MONGODB_DB_NAME)
    logger.info("Analytics Service ready on port 8001")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Analytics Service...")
    await close_database_connection()


app = FastAPI(
    title="Vobiz Analytics Service",
    description="Call management, recordings, and analytics",
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


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics"}


# ============= CALLS API =============

@app.post("/calls", response_model=CallResponse)
async def create_call(
    request: CreateCallRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Create a new outbound call."""
    workspace_id = user.workspace_id if user else None
    call = await CallService.create_call(request, workspace_id)
    return CallResponse.from_call_record(call)


@app.get("/calls")
async def list_calls(
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    skip: int = 0,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """List all calls."""
    workspace_id = user.workspace_id if user else None
    calls = await CallService.list_calls(
        workspace_id=workspace_id,
        status=CallStatus(status) if status else None,
        limit=limit,
        skip=skip
    )
    
    return {
        "calls": [CallResponse.from_call_record(c) for c in calls],
        "count": len(calls),
        "limit": limit,
        "skip": skip
    }


@app.get("/calls/{call_id}")
async def get_call(
    call_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific call."""
    workspace_id = user.workspace_id if user else None
    call = await CallService.get_call(call_id, workspace_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Generate presigned URL for recording
    response = CallResponse.from_call_record(call)
    if call.recording_url and call.recording_url.startswith("s3://"):
        response.recording_url = S3Service.generate_presigned_url(call.recording_url)
    
    return response


@app.post("/calls/{call_id}/analyze")
async def analyze_call(
    call_id: str,
    user: Optional[User] = Depends(get_current_user_optional)  # Allow system auth via API key
):
    """Run post-call analysis on a call."""
    analysis = await AnalysisService.analyze_call(call_id)
    if not analysis:
        raise HTTPException(status_code=400, detail="Analysis failed")
    return analysis


@app.get("/calls/stats")
async def get_call_stats(
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get call statistics."""
    workspace_id = user.workspace_id if user else None
    db = get_database()
    
    pipeline = []
    if workspace_id:
        pipeline.append({"$match": {"workspace_id": workspace_id}})
    
    pipeline.extend([
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "avg_duration": {"$avg": "$duration_seconds"}
        }}
    ])
    
    cursor = db.calls.aggregate(pipeline)
    stats = {}
    async for doc in cursor:
        stats[doc["_id"]] = {
            "count": doc["count"],
            "avg_duration": doc.get("avg_duration", 0)
        }
    
    return stats
