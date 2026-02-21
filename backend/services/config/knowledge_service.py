"""Knowledge service for document metadata and lifecycle operations."""
import hashlib
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import boto3
from bson import ObjectId
from fastapi import UploadFile

from shared.database.connection import get_database
from shared.database.models import KnowledgeDocument, KnowledgeSourceType, KnowledgeStatus
from shared.settings import config

logger = logging.getLogger("knowledge_service")


class KnowledgeService:
    """Service layer for knowledge metadata and document storage."""

    @staticmethod
    def _get_s3_client():
        if not all([config.AWS_ACCESS_KEY_ID, config.AWS_SECRET_ACCESS_KEY, config.AWS_BUCKET_NAME]):
            raise ValueError("AWS S3 configuration is incomplete")

        return boto3.client(
            "s3",
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION,
        )

    @staticmethod
    def _s3_uri_from_key(key: str) -> str:
        return f"s3://{config.AWS_BUCKET_NAME}/{key}"

    @staticmethod
    def _parse_s3_uri(s3_uri: str) -> Tuple[Optional[str], Optional[str]]:
        if not s3_uri or not s3_uri.startswith("s3://"):
            return None, None

        parsed = urlparse(s3_uri)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        return bucket, key

    @staticmethod
    async def create_document(
        *,
        workspace_id: Optional[str],
        name: str,
        source_type: KnowledgeSourceType,
        assigned_assistant_ids: List[str],
        file: Optional[UploadFile] = None,
        text: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a knowledge document metadata entry and persist source content."""
        db = get_database()
        now = datetime.now(timezone.utc)

        content_hash_input = ""
        storage_url: Optional[str] = None
        file_size = 0

        if source_type == KnowledgeSourceType.FILE:
            if not file:
                raise ValueError("File upload is required for source_type=file")

            file_bytes = await file.read()
            if not file_bytes:
                raise ValueError("Uploaded file is empty")

            file_size = len(file_bytes)
            content_hash_input = hashlib.sha256(file_bytes).hexdigest()

            file_ext = ""
            if file.filename and "." in file.filename:
                file_ext = file.filename[file.filename.rfind("."):]

            object_key = (
                f"knowledge/{workspace_id or 'global'}/{now.strftime('%Y/%m/%d')}/"
                f"{content_hash_input[:16]}{file_ext}"
            )

            s3 = KnowledgeService._get_s3_client()
            s3.upload_fileobj(
                Fileobj=BytesIO(file_bytes),
                Bucket=config.AWS_BUCKET_NAME,
                Key=object_key,
                ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
            )
            storage_url = KnowledgeService._s3_uri_from_key(object_key)

        elif source_type == KnowledgeSourceType.TEXT:
            if not text or not text.strip():
                raise ValueError("Text content is required for source_type=text")
            content_hash_input = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
            file_size = len(text.encode("utf-8"))

        elif source_type == KnowledgeSourceType.URL:
            if not url or not url.strip():
                raise ValueError("URL is required for source_type=url")
            content_hash_input = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()
            file_size = len(url.encode("utf-8"))

        document = KnowledgeDocument(
            workspace_id=workspace_id,
            name=name,
            source_type=source_type,
            storage_url=storage_url,
            file_size=file_size,
            content_hash=content_hash_input,
            assigned_assistant_ids=assigned_assistant_ids,
            status=KnowledgeStatus.PROCESSING,
            token_count=0,
            created_at=now,
            last_synced_at=None,
        )

        payload = document.to_dict()
        if source_type == KnowledgeSourceType.TEXT and text:
            payload["raw_text"] = text
        if source_type == KnowledgeSourceType.URL and url:
            payload["source_url"] = url

        result = await db.knowledge_documents.insert_one(payload)

        created = await db.knowledge_documents.find_one({"_id": result.inserted_id})
        created["id"] = str(created["_id"])
        created.pop("_id", None)

        logger.info(
            "Created knowledge document: %s (workspace=%s, source=%s)",
            created["id"],
            workspace_id,
            source_type.value,
        )
        return created

    @staticmethod
    async def list_documents(workspace_id: Optional[str]) -> List[Dict[str, Any]]:
        """List knowledge documents scoped by workspace."""
        db = get_database()

        query: Dict[str, Any] = {}
        if workspace_id:
            query["workspace_id"] = workspace_id

        cursor = db.knowledge_documents.find(query).sort("created_at", -1)

        documents: List[Dict[str, Any]] = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            doc.pop("_id", None)
            doc.pop("raw_text", None)
            documents.append(doc)

        return documents

    @staticmethod
    async def get_document_by_id(document_id: str, workspace_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get one document by id with workspace ownership validation."""
        db = get_database()

        if not ObjectId.is_valid(document_id):
            return None

        query: Dict[str, Any] = {"_id": ObjectId(document_id)}
        if workspace_id:
            query["workspace_id"] = workspace_id

        doc = await db.knowledge_documents.find_one(query)
        if not doc:
            return None

        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        return doc

    @staticmethod
    async def delete_document(document_id: str, workspace_id: Optional[str]) -> bool:
        """Delete a document, related chunks, and backing S3 object when present."""
        db = get_database()

        doc = await KnowledgeService.get_document_by_id(document_id, workspace_id)
        if not doc:
            return False

        await db.knowledge_chunks.delete_many({"document_id": document_id})
        await db.knowledge_documents.delete_one({"_id": ObjectId(document_id)})

        storage_url = doc.get("storage_url")
        if storage_url:
            try:
                bucket, key = KnowledgeService._parse_s3_uri(storage_url)
                if bucket and key:
                    s3 = KnowledgeService._get_s3_client()
                    s3.delete_object(Bucket=bucket, Key=key)
            except Exception as exc:
                logger.warning("Failed to delete S3 object for knowledge %s: %s", document_id, exc)

        logger.info("Deleted knowledge document: %s (workspace=%s)", document_id, workspace_id)
        return True

    @staticmethod
    async def mark_processing_and_clear_chunks(document_id: str, workspace_id: Optional[str]) -> bool:
        """Set document to processing and clear existing chunks before re-ingestion."""
        db = get_database()

        if not ObjectId.is_valid(document_id):
            return False

        query: Dict[str, Any] = {"_id": ObjectId(document_id)}
        if workspace_id:
            query["workspace_id"] = workspace_id

        result = await db.knowledge_documents.update_one(
            query,
            {
                "$set": {
                    "status": KnowledgeStatus.PROCESSING.value,
                    "error_message": None,
                }
            },
        )

        if result.matched_count == 0:
            return False

        await db.knowledge_chunks.delete_many({"document_id": document_id})
        logger.info("Resync requested for knowledge document: %s", document_id)
        return True
