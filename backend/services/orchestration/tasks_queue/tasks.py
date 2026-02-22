"""
Celery tasks for campaign execution.
"""
import logging
import asyncio
import re
from io import BytesIO
from datetime import datetime, timezone
from typing import Dict, Any, List
from urllib.parse import urlparse

import boto3
import httpx
import tiktoken
from bson import ObjectId
from docx import Document as DocxDocument
from PyPDF2 import PdfReader
from celery import group
from .celery_app import celery_app
from shared.ai import embed_texts
from shared.settings import config

logger = logging.getLogger("queue.tasks")


def _token_count(text: str, encoder) -> int:
    if not text:
        return 0
    return len(encoder.encode(text))


def _chunk_text(text: str, encoder, chunk_size: int = 700, overlap: int = 100) -> List[Dict[str, Any]]:
    token_ids = encoder.encode(text)
    if not token_ids:
        return []

    chunks: List[Dict[str, Any]] = []
    start = 0
    while start < len(token_ids):
        end = min(start + chunk_size, len(token_ids))
        chunk_tokens = token_ids[start:end]
        chunks.append(
            {
                "chunk_text": encoder.decode(chunk_tokens),
                "token_count": len(chunk_tokens),
            }
        )
        if end == len(token_ids):
            break
        start = max(0, end - overlap)

    return chunks


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages)


def _extract_text_from_docx(file_bytes: bytes) -> str:
    document = DocxDocument(BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in document.paragraphs if paragraph.text])


def _guess_file_extension(storage_url: str) -> str:
    parsed = urlparse(storage_url)
    key = parsed.path.lower()
    if key.endswith(".pdf"):
        return "pdf"
    if key.endswith(".docx"):
        return "docx"
    return "txt"


def _strip_html(raw_html: str) -> str:
    no_script = re.sub(r"<script.*?>.*?</script>", "", raw_html, flags=re.IGNORECASE | re.DOTALL)
    no_style = re.sub(r"<style.*?>.*?</style>", "", no_script, flags=re.IGNORECASE | re.DOTALL)
    no_tags = re.sub(r"<[^>]+>", " ", no_style)
    normalized = re.sub(r"\s+", " ", no_tags)
    return normalized.strip()


async def _load_document_text(doc: Dict[str, Any]) -> str:
    source_type = doc.get("source_type")

    if source_type == "text":
        return (doc.get("raw_text") or "").strip()

    if source_type == "url":
        source_url = (doc.get("source_url") or "").strip()
        if not source_url:
            raise ValueError("Knowledge URL source is missing source_url")
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(source_url)
            response.raise_for_status()
            return _strip_html(response.text)

    storage_url = doc.get("storage_url")
    if not storage_url or not str(storage_url).startswith("s3://"):
        raise ValueError("Knowledge file source is missing storage_url")

    parsed = urlparse(storage_url)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_REGION,
    )
    object_bytes = s3.get_object(Bucket=bucket, Key=key)["Body"].read()

    ext = _guess_file_extension(storage_url)
    if ext == "pdf":
        return _extract_text_from_pdf(object_bytes)
    if ext == "docx":
        return _extract_text_from_docx(object_bytes)
    return object_bytes.decode("utf-8", errors="ignore")


async def _ingest_knowledge_async(document_id: str) -> Dict[str, Any]:
    from shared.database.connection import connect_to_database, get_database

    await connect_to_database(config.MONGODB_URI, config.MONGODB_DB_NAME)
    db = get_database()

    if not ObjectId.is_valid(document_id):
        raise ValueError("Invalid knowledge document id")

    mongo_id = ObjectId(document_id)
    doc = await db.knowledge_documents.find_one({"_id": mongo_id})
    if not doc:
        raise ValueError("Knowledge document not found")

    workspace_id = doc.get("workspace_id")
    assistant_ids = doc.get("assigned_assistant_ids", [])

    try:
        await db.knowledge_documents.update_one(
            {"_id": mongo_id},
            {"$set": {"status": "processing", "error_message": None}},
        )

        content = (await _load_document_text(doc)).strip()
        if not content:
            raise ValueError("No extractable text found in source")

        encoder = tiktoken.get_encoding("cl100k_base")
        total_tokens = _token_count(content, encoder)
        raw_chunks = _chunk_text(content, encoder, chunk_size=700, overlap=100)

        await db.knowledge_chunks.delete_many({"document_id": document_id})

        chunk_texts = [chunk["chunk_text"] for chunk in raw_chunks]
        embeddings = await embed_texts(chunk_texts)

        if len(embeddings) != len(raw_chunks):
            raise ValueError("Embedding count mismatch")

        rows = []
        for idx, chunk in enumerate(raw_chunks):
            rows.append(
                {
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "document_name": doc.get("name", "Untitled"),
                    "assistant_ids": assistant_ids,
                    "chunk_text": chunk["chunk_text"],
                    "embedding": embeddings[idx],
                    "token_count": chunk["token_count"],
                }
            )

        if rows:
            await db.knowledge_chunks.insert_many(rows, ordered=False)

        now = datetime.now(timezone.utc)
        await db.knowledge_documents.update_one(
            {"_id": mongo_id},
            {
                "$set": {
                    "status": "ready",
                    "error_message": None,
                    "token_count": total_tokens,
                    "last_synced_at": now,
                }
            },
        )

        logger.info(
            "Knowledge ingest complete: document_id=%s chunks=%s workspace=%s",
            document_id,
            len(rows),
            workspace_id,
        )
        return {
            "success": True,
            "document_id": document_id,
            "chunks": len(rows),
            "token_count": total_tokens,
        }

    except Exception as exc:
        await db.knowledge_documents.update_one(
            {"_id": mongo_id},
            {
                "$set": {
                    "status": "error",
                    "error_message": str(exc),
                }
            },
        )
        logger.error("Knowledge ingest failed for %s: %s", document_id, exc)
        raise


def run_async(coro):
    """Helper to run async code in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
)
def make_single_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single outbound call.
    
    Args:
        call_data: Dictionary containing:
            - phone_number: Target phone number
            - assistant_id: Which assistant to use
            - campaign_id: Parent campaign ID
            - contact_index: Index in contacts list
            
    Returns:
        Call result with status
    """
    from services.analytics.call_service import CallService
    from shared.database.models import CreateCallRequest
    
    phone_number = call_data.get("phone_number")
    assistant_id = call_data.get("assistant_id")
    campaign_id = call_data.get("campaign_id")
    contact_index = call_data.get("contact_index", 0)
    
    logger.info(f"[Task {self.request.id}] Making call to {phone_number}")
    
    try:
        # Create call request
        request = CreateCallRequest(
            phone_number=phone_number,
            assistant_id=assistant_id,
            metadata={"campaign_id": campaign_id, "contact_index": contact_index}
        )
        
        # Create call (async)
        async def create_call():
            return await CallService.create_call(request)
        
        call = run_async(create_call())
        
        logger.info(f"[Task {self.request.id}] Call created: {call.call_id}")
        
        return {
            "success": True,
            "call_id": call.call_id,
            "phone_number": phone_number,
            "status": call.status.value,
        }
        
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Call failed: {e}")
        
        if self.request.retries >= self.max_retries:
            # Max retries reached, mark as failed
            return {
                "success": False,
                "phone_number": phone_number,
                "error": str(e),
            }
        
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(bind=True)
def execute_campaign(self, campaign_id: str) -> Dict[str, Any]:
    """
    Execute a campaign by processing contacts in batches.
    
    Args:
        campaign_id: Campaign to execute
        
    Returns:
        Campaign execution result
    """
    from shared.database.connection import connect_to_database
    from shared.settings import config
    
    logger.info(f"[Campaign {campaign_id}] Starting execution")
    
    async def run_campaign():
        # Connect to database
        await connect_to_database(config.MONGODB_URI, config.MONGODB_DB_NAME)
        
        from services.campaign_service import CampaignService
        
        # Get campaign
        campaign = await CampaignService.get_campaign(campaign_id)
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return {"success": False, "error": "Campaign not found"}
        
        # Get pending contacts
        pending_contacts = [
            (i, c) for i, c in enumerate(campaign.contacts)
            if c.status == "pending"
        ]
        
        if not pending_contacts:
            logger.info(f"[Campaign {campaign_id}] No pending contacts")
            return {"success": True, "message": "No pending contacts"}
        
        max_concurrent = campaign.max_concurrent_calls or 2
        logger.info(f"[Campaign {campaign_id}] Processing {len(pending_contacts)} contacts, max concurrent: {max_concurrent}")
        
        # Process in batches
        batch_results = []
        for batch_start in range(0, len(pending_contacts), max_concurrent):
            batch = pending_contacts[batch_start:batch_start + max_concurrent]
            
            # Create tasks for this batch
            tasks = []
            for contact_index, contact in batch:
                call_data = {
                    "phone_number": contact.phone_number,
                    "assistant_id": campaign.assistant_id,
                    "campaign_id": campaign_id,
                    "contact_index": contact_index,
                }
                tasks.append(make_single_call.s(call_data))
            
            # Execute batch in parallel
            job = group(tasks)
            result = job.apply_async()
            
            # Wait for batch to complete
            batch_result = result.get(timeout=600)  # 10 min timeout per batch
            batch_results.extend(batch_result)
            
            logger.info(f"[Campaign {campaign_id}] Batch completed: {len(batch_result)} calls")
        
        # Mark campaign as completed
        from shared.database.connection import get_database
        db = get_database()
        await db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {"$set": {
                "status": "completed",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "total_calls": len(batch_results),
            "successful": sum(1 for r in batch_results if r.get("success")),
            "failed": sum(1 for r in batch_results if not r.get("success")),
        }
    
    try:
        result = run_async(run_campaign())
        logger.info(f"[Campaign {campaign_id}] Execution complete: {result}")
        return result
    except Exception as e:
        logger.error(f"[Campaign {campaign_id}] Execution failed: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task
def health_check() -> Dict[str, Any]:
    """Simple health check task for testing Celery connectivity."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=120,
)
def ingest_knowledge(self, document_id: str) -> Dict[str, Any]:
    """Ingest a knowledge document and persist chunks + embeddings."""
    logger.info("[Task %s] Starting knowledge ingest for document=%s", self.request.id, document_id)
    try:
        result = run_async(_ingest_knowledge_async(document_id))
        logger.info("[Task %s] Knowledge ingest completed successfully", self.request.id)
        return result
    except Exception as exc:
        logger.error("[Task %s] Knowledge ingest failed for %s: %s", self.request.id, document_id, exc)
        raise
