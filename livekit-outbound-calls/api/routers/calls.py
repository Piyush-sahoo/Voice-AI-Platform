"""Calls API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from database.models import CallStatus, CreateCallRequest, CallResponse
from services import CallService, WebhookService
from services.s3_service import S3Service
from auth.dependencies import get_current_user
from auth.models import User

logger = logging.getLogger("api.calls")
router = APIRouter()


@router.post("/calls", response_model=CallResponse)
async def create_call(request: CreateCallRequest):
    """
    Trigger a new outbound call.
    
    - **phone_number**: Phone number to call (E.164 format)
    - **instructions**: Optional custom instructions for the AI
    - **webhook_url**: Optional URL for call event notifications
    - **metadata**: Optional custom metadata
    """
    if not request.phone_number.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in E.164 format (e.g., +919148227303)"
        )
    
    try:
        call = await CallService.create_call(request)
        
        if call.webhook_url:
            await WebhookService.send_initiated(call)
        
        logger.info(f"Call created: {call.call_id}")
        
        return CallResponse(
            call_id=call.call_id,
            status=call.status.value,
            room_name=call.room_name,
            message="Call initiated successfully",
        )
        
    except Exception as e:
        logger.error(f"Failed to create call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}")
async def get_call(call_id: str):
    """Get details of a specific call."""
    call = await CallService.get_call(call_id)
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    data = call.to_dict()
    if data.get("recording_url"):
        data["recording_url"] = S3Service.generate_presigned_url(data["recording_url"])
        
    return data


@router.get("/calls")
async def list_calls(
    status: Optional[str] = Query(None),
    phone_number: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """List calls with optional filters."""
    status_enum = None
    if status:
        try:
            status_enum = CallStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in CallStatus]}"
            )
    
    calls = await CallService.list_calls(
        status=status_enum,
        phone_number=phone_number,
        limit=limit,
        skip=skip,
    )
    
    call_dicts = []
    for call in calls:
        data = call.to_dict()
        if data.get("recording_url"):
            data["recording_url"] = S3Service.generate_presigned_url(data["recording_url"])
        call_dicts.append(data)

    return {
        "calls": call_dicts,
        "count": len(calls),
        "limit": limit,
        "skip": skip,
    }


@router.get("/calls/{call_id}/analysis")
async def get_call_analysis(call_id: str):
    """Get post-call analysis for a specific call."""
    call = await CallService.get_call(call_id)
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if not call.analysis:
        raise HTTPException(status_code=404, detail="Analysis not available")
    
    return {
        "call_id": call_id,
        "analysis": call.analysis.model_dump() if hasattr(call.analysis, 'model_dump') else call.analysis,
    }


@router.post("/calls/{call_id}/analyze")
async def trigger_analysis(call_id: str):
    """Manually trigger post-call analysis."""
    from services import AnalysisService
    
    call = await CallService.get_call(call_id)
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if call.status != CallStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Can only analyze completed calls")
    
    analysis = await AnalysisService.analyze_call(call_id)
    
    if not analysis:
        raise HTTPException(status_code=500, detail="Analysis failed")
    
    return {
        "call_id": call_id,
        "analysis": analysis.model_dump(),
        "message": "Analysis completed",
    }


@router.get("/analytics/calls")
async def get_call_analytics():
    """Get aggregated call analytics."""
    from database.connection import get_database
    
    db = get_database()
    
    # Get total counts by status
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_duration": {"$sum": "$duration_seconds"},
        }}
    ]
    
    status_stats = {}
    async for doc in db.calls.aggregate(pipeline):
        status_stats[doc["_id"]] = {
            "count": doc["count"],
            "total_duration_seconds": doc["total_duration"],
        }
    
    # Get today's calls
    from datetime import datetime, timezone, timedelta
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_count = await db.calls.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # Total calls
    total_calls = await db.calls.count_documents({})
    
    # Sentiment distribution (from analyzed calls)
    sentiment_pipeline = [
        {"$match": {"analysis.sentiment": {"$exists": True}}},
        {"$group": {"_id": "$analysis.sentiment", "count": {"$sum": 1}}}
    ]
    
    sentiment_stats = {}
    async for doc in db.calls.aggregate(sentiment_pipeline):
        sentiment_stats[doc["_id"]] = doc["count"]
    
    return {
        "total_calls": total_calls,
        "today_calls": today_count,
        "by_status": status_stats,
        "by_sentiment": sentiment_stats,
    }


@router.get("/analytics/summary")
async def get_analytics_summary(
    days: int = Query(7, ge=1, le=90),
):
    """Get call summary for the last N days."""
    from database.connection import get_database
    from datetime import datetime, timezone, timedelta
    
    db = get_database()
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Daily breakdown
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date.isoformat()}}},
        {"$addFields": {
            "date_str": {"$substr": ["$created_at", 0, 10]}
        }},
        {"$group": {
            "_id": "$date_str",
            "total": {"$sum": 1},
            "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "answered": {"$sum": {"$cond": [{"$eq": ["$status", "answered"]}, 1, 0]}},
            "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]
    
    daily_stats = []
    async for doc in db.calls.aggregate(pipeline):
        daily_stats.append({
            "date": doc["_id"],
            "total": doc["total"],
            "completed": doc["completed"],
            "answered": doc["answered"],
            "failed": doc["failed"],
        })
    
    return {
        "period_days": days,
        "daily_breakdown": daily_stats,
    }
