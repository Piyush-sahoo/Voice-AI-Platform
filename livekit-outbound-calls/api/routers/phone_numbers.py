"""Phone Numbers API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from database.models import CreatePhoneNumberRequest
from services import PhoneNumberService
from auth.dependencies import get_current_user
from auth.models import User

logger = logging.getLogger("api.phone_numbers")
router = APIRouter()


@router.post("/phone-numbers")
async def add_phone_number(request: CreatePhoneNumberRequest):
    """Add a new phone number."""
    if not request.number.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in E.164 format (e.g., +919148227303)"
        )
    
    try:
        phone = await PhoneNumberService.add_phone_number(request)
        return {
            "phone_id": phone.phone_id,
            "number": phone.number,
            "message": "Phone number added successfully",
        }
    except Exception as e:
        logger.error(f"Failed to add phone number: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phone-numbers")
async def list_phone_numbers(is_active: Optional[bool] = Query(None)):
    """List all phone numbers."""
    phones = await PhoneNumberService.list_phone_numbers(is_active=is_active)
    return {
        "phone_numbers": [p.to_dict() for p in phones],
        "count": len(phones),
    }


@router.get("/phone-numbers/{phone_id}")
async def get_phone_number(phone_id: str):
    """Get a specific phone number."""
    phone = await PhoneNumberService.get_phone_number(phone_id)
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")
    return phone.to_dict()


@router.delete("/phone-numbers/{phone_id}")
async def delete_phone_number(phone_id: str):
    """Delete a phone number."""
    deleted = await PhoneNumberService.delete_phone_number(phone_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Phone number not found")
    return {"message": "Phone number deleted successfully"}
