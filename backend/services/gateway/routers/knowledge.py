"""Knowledge API endpoints."""
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from services.config.knowledge_service import KnowledgeService
from services.orchestration.tasks_queue.tasks import ingest_knowledge
from shared.auth.dependencies import get_current_user_optional
from shared.auth.models import User
from shared.database.models import KnowledgeSourceType

logger = logging.getLogger("api.knowledge")
router = APIRouter()


def _normalize_assistant_ids(raw_ids: Optional[List[str]], raw_json: Optional[str]) -> List[str]:
    if raw_ids:
        return [value for value in raw_ids if value]

    if raw_json:
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, list):
                return [str(value) for value in parsed if value]
        except json.JSONDecodeError:
            logger.warning("Invalid assigned_assistant_ids_json payload")

    return []


@router.post("/knowledge")
async def create_knowledge(
    name: str = Form(...),
    file: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
    url: Optional[str] = Form(default=None),
    assigned_assistant_ids: Optional[List[str]] = Form(default=None),
    assigned_assistant_ids_json: Optional[str] = Form(default=None),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Create a knowledge document and queue ingestion."""
    workspace_id = user.workspace_id if user else None

    if not name.strip():
        raise HTTPException(status_code=400, detail="name is required")

    source_count = sum(bool(x) for x in [file, text and text.strip(), url and url.strip()])
    if source_count != 1:
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one source: file, text, or url",
        )

    source_type = (
        KnowledgeSourceType.FILE
        if file
        else KnowledgeSourceType.URL
        if url and url.strip()
        else KnowledgeSourceType.TEXT
    )

    assistant_ids = _normalize_assistant_ids(assigned_assistant_ids, assigned_assistant_ids_json)

    try:
        document = await KnowledgeService.create_document(
            workspace_id=workspace_id,
            name=name.strip(),
            source_type=source_type,
            assigned_assistant_ids=assistant_ids,
            file=file,
            text=text,
            url=url,
        )

        task = ingest_knowledge.delay(document["id"])
        document["task_id"] = task.id
        return document

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Failed to create knowledge: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create knowledge") from exc


@router.get("/knowledge")
async def list_knowledge(user: Optional[User] = Depends(get_current_user_optional)):
    """List knowledge documents for the authenticated workspace."""
    workspace_id = user.workspace_id if user else None

    try:
        documents = await KnowledgeService.list_documents(workspace_id)
        return {"documents": documents, "count": len(documents)}
    except Exception as exc:
        logger.error("Failed to list knowledge: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list knowledge") from exc


@router.delete("/knowledge/{document_id}")
async def delete_knowledge(
    document_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Delete one knowledge document and all its chunks."""
    workspace_id = user.workspace_id if user else None

    try:
        deleted = await KnowledgeService.delete_document(document_id, workspace_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Knowledge document not found")
        return {"message": "Knowledge deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to delete knowledge %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete knowledge") from exc


@router.post("/knowledge/{document_id}/resync")
async def resync_knowledge(
    document_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Mark document as processing, clear chunks, and queue a fresh ingest."""
    workspace_id = user.workspace_id if user else None

    try:
        updated = await KnowledgeService.mark_processing_and_clear_chunks(document_id, workspace_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Knowledge document not found")

        task = ingest_knowledge.delay(document_id)
        return {
            "message": "Knowledge resync started",
            "document_id": document_id,
            "status": "processing",
            "task_id": task.id,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to resync knowledge %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Failed to resync knowledge") from exc
