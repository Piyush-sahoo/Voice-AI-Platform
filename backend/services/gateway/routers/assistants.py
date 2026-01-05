"""Assistants API endpoints with multi-tenancy support."""
import logging
from typing import Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models import (
    CreateAssistantRequest,
    UpdateAssistantRequest,
    AssistantResponse,
)
from services.config.assistant_service import AssistantService
from services.analytics.webhook_service import WebhookService
from shared.database.models import CallRecord, CallStatus, CallAnalysis
from shared.auth.dependencies import get_current_user_optional
from shared.auth.models import User

logger = logging.getLogger("api.assistants")
router = APIRouter()


@router.post("/assistants", response_model=AssistantResponse)
async def create_assistant(
    request: CreateAssistantRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Create a new AI assistant.
    
    - **name**: Name of the assistant
    - **instructions**: System prompt for the AI
    - **first_message**: What the AI says when call connects
    - **voice**: Voice configuration (provider, voice_id)
    - **webhook_url**: URL for call event notifications
    """
    try:
        workspace_id = user.workspace_id if user else None
        assistant = await AssistantService.create_assistant(request, workspace_id=workspace_id)
        
        return AssistantResponse(
            assistant_id=assistant.assistant_id,
            name=assistant.name,
            message="Assistant created successfully",
        )
        
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistants")
async def list_assistants(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """List all assistants for current workspace."""
    workspace_id = user.workspace_id if user else None
    assistants = await AssistantService.list_assistants(
        workspace_id=workspace_id,
        is_active=is_active,
        limit=limit,
        skip=skip,
    )
    
    return {
        "assistants": [a.to_dict() for a in assistants],
        "count": len(assistants),
    }


@router.get("/assistants/{assistant_id}")
async def get_assistant(
    assistant_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific assistant."""
    workspace_id = user.workspace_id if user else None
    assistant = await AssistantService.get_assistant(assistant_id, workspace_id=workspace_id)
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return assistant.to_dict()


@router.patch("/assistants/{assistant_id}")
async def update_assistant(
    assistant_id: str,
    request: UpdateAssistantRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Update an assistant."""
    workspace_id = user.workspace_id if user else None
    assistant = await AssistantService.update_assistant(assistant_id, request, workspace_id=workspace_id)
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return AssistantResponse(
        assistant_id=assistant.assistant_id,
        name=assistant.name,
        message="Assistant updated successfully",
    )


@router.delete("/assistants/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete an assistant."""
    workspace_id = user.workspace_id if user else None
    deleted = await AssistantService.delete_assistant(assistant_id, workspace_id=workspace_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return {"message": "Assistant deleted successfully"}


class TestWebhookRequest(BaseModel):
    webhook_url: Optional[str] = None


@router.post("/assistants/{assistant_id}/test-webhook")
async def test_webhook(
    assistant_id: str,
    request: TestWebhookRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Test webhook for an assistant."""
    workspace_id = user.workspace_id if user else None
    
    # Get assistant to ensure access
    assistant = await AssistantService.get_assistant(assistant_id, workspace_id=workspace_id)
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
        
    url = request.webhook_url or assistant.webhook_url
    if not url:
        raise HTTPException(status_code=400, detail="No webhook URL provided")
        
    # Create dummy call record for testing
    dummy_call = CallRecord(
        call_id=f"test_webhook_{uuid.uuid4().hex[:8]}",
        workspace_id=workspace_id,
        phone_number="+1234567890",
        from_number="+1987654321",
        room_name="test-room",
        status=CallStatus.COMPLETED,
        assistant_id=assistant_id,
        webhook_url=url,
        created_at=datetime.now(timezone.utc),
        duration_seconds=42,
        analysis=CallAnalysis(
            success=True,
            sentiment="positive",
            summary="This is a test call summary from the Vobiz dashboard.",
            key_topics=["Product Demo", "Pricing"],
            action_items=["Send pricing PDF"],
        )
    )
    
    success = await WebhookService.send_completed(dummy_call)
    
    if success:
        return {"message": "Webhook sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send webhook")

@router.post("/assistants/analysis/{call_id}")
async def trigger_call_analysis(
    call_id: str,
    background_tasks: BackgroundTasks,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Trigger post-call analysis manually or from agent."""
    from services.analytics.analysis_service import AnalysisService
    
    # We allow this to be called by anyone (or the agent) for now
    # In production, verify the agent's token or internal API key
    
    background_tasks.add_task(AnalysisService.analyze_call, call_id)
    return {"message": "Analysis triggered in background"}
