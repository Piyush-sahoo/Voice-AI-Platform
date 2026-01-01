"""Phone Numbers API endpoints with multi-tenancy support."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models import CreatePhoneNumberRequest, CreateInboundNumberRequest
from services import PhoneNumberService
from shared.auth.dependencies import get_current_user_optional
from shared.auth.models import User

logger = logging.getLogger("api.phone_numbers")
router = APIRouter()


@router.post("/phone-numbers")
@router.post("/phone-numbers/outbound")
async def add_phone_number(
    request: CreatePhoneNumberRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Add a new phone number (outbound)."""
    if not request.number.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in E.164 format (e.g., +919148227303)"
        )
    
    try:
        workspace_id = user.workspace_id if user else None
        phone = await PhoneNumberService.add_phone_number(request, workspace_id=workspace_id)
        return {
            "phone_id": phone.phone_id,
            "number": phone.number,
            "direction": phone.direction,
            "message": "Phone number added successfully",
        }
    except Exception as e:
        logger.error(f"Failed to add phone number: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/phone-numbers/inbound")
async def add_inbound_number(
    request: CreateInboundNumberRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Set up an inbound phone number.
    Creates LiveKit inbound trunk and dispatch rule for automatic agent dispatch.
    """
    if not request.number.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in E.164 format (e.g., +912271264190)"
        )
    
    try:
        workspace_id = user.workspace_id if user else None
        phone = await PhoneNumberService.create_inbound_number(request, workspace_id=workspace_id)
        return {
            "phone_id": phone.phone_id,
            "number": phone.number,
            "direction": "inbound",
            "assistant_id": phone.assistant_id,
            "inbound_trunk_id": phone.inbound_trunk_id,
            "dispatch_rule_id": phone.dispatch_rule_id,
            "message": "Inbound number configured successfully. Update your Vobiz trunk Primary URI to route calls.",
        }
    except Exception as e:
        logger.error(f"Failed to create inbound number: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phone-numbers")
async def list_phone_numbers(
    is_active: Optional[bool] = Query(None),
    direction: Optional[str] = Query(None, description="Filter by direction: inbound, outbound, both"),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """List all phone numbers for current workspace."""
    workspace_id = user.workspace_id if user else None
    phones = await PhoneNumberService.list_phone_numbers(workspace_id=workspace_id, is_active=is_active)
    
    # Filter by direction if specified
    if direction:
        phones = [p for p in phones if p.direction == direction]
    
    return {
        "phone_numbers": [p.to_dict() for p in phones],
        "count": len(phones),
    }


@router.get("/phone-numbers/{phone_id}")
async def get_phone_number(
    phone_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific phone number."""
    workspace_id = user.workspace_id if user else None
    phone = await PhoneNumberService.get_phone_number(phone_id, workspace_id=workspace_id)
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")
    return phone.to_dict()


@router.delete("/phone-numbers/{phone_id}")
async def delete_phone_number(
    phone_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete a phone number. Cleans up LiveKit resources for inbound numbers."""
    workspace_id = user.workspace_id if user else None
    
    # Get phone to check type
    phone = await PhoneNumberService.get_phone_number(phone_id, workspace_id=workspace_id)
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    # Use appropriate delete method
    if phone.direction == "inbound":
        deleted = await PhoneNumberService.delete_inbound_number(phone_id, workspace_id=workspace_id)
    else:
        deleted = await PhoneNumberService.delete_phone_number(phone_id, workspace_id=workspace_id)
    
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete phone number")
    return {"message": "Phone number deleted successfully"}

