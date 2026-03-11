"""
Service for managing per-workspace integrations (LiveKit, AI providers, telephony).
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from shared.database.connection import get_database
from shared.database.models import WorkspaceIntegrations
from shared.security.crypto import encrypt_secret, decrypt_secret
from shared.logging_utils import log_resolution


logger = logging.getLogger("workspace_integrations_service")


class WorkspaceIntegrationService:
    """CRUD operations for workspace_integrations collection."""

    COLLECTION = "workspace_integrations"

    @staticmethod
    async def _get_collection():
        db = get_database()
        col = db[WorkspaceIntegrationService.COLLECTION]
        await col.create_index("workspace_id", unique=True)
        return col

    @staticmethod
    async def create_workspace_integrations(workspace_id: str, data: Dict[str, Any]) -> WorkspaceIntegrations:
        col = await WorkspaceIntegrationService._get_collection()

        existing = await col.find_one({"workspace_id": workspace_id})
        if existing:
            raise ValueError("Integrations already exist for this workspace")

        doc = WorkspaceIntegrationService._build_document(workspace_id, data, existing=None)
        await col.insert_one(doc.to_dict())
        logger.info("Created workspace integrations for workspace_id=%s", workspace_id)
        return doc

    @staticmethod
    async def get_workspace_integrations(
        workspace_id: str,
        decrypt: bool = False,
        redacted: bool = False,
    ) -> Optional[Dict[str, Any]]:
        col = await WorkspaceIntegrationService._get_collection()
        raw = await col.find_one({"workspace_id": workspace_id})
        if not raw:
            return None

        integrations = WorkspaceIntegrations.from_dict(raw)

        log_resolution(
            "Workspace integrations",
            workspace_id,
            "database",
            {
                "livekit": bool(integrations.livekit and integrations.livekit.url),
                "ai_providers": bool(integrations.ai_providers),
                "telephony": bool(integrations.telephony and (integrations.telephony.sip_domain or integrations.telephony.sip_username)),
            },
        )

        if decrypt:
            return WorkspaceIntegrationService._to_decrypted_dict(integrations)
        if redacted:
            return WorkspaceIntegrationService._to_redacted_dict(integrations)

        return integrations.to_dict()

    @staticmethod
    async def update_workspace_integrations(workspace_id: str, data: Dict[str, Any]) -> Optional[WorkspaceIntegrations]:
        col = await WorkspaceIntegrationService._get_collection()
        existing_raw = await col.find_one({"workspace_id": workspace_id})
        if not existing_raw:
            return None

        existing = WorkspaceIntegrations.from_dict(existing_raw)
        updated = WorkspaceIntegrationService._build_document(workspace_id, data, existing=existing)
        await col.update_one({"workspace_id": workspace_id}, {"$set": updated.to_dict()})
        logger.info("Updated workspace integrations for workspace_id=%s", workspace_id)
        return updated

    @staticmethod
    async def delete_workspace_integrations(workspace_id: str) -> bool:
        col = await WorkspaceIntegrationService._get_collection()
        result = await col.delete_one({"workspace_id": workspace_id})
        return result.deleted_count > 0

    @staticmethod
    def _build_document(
        workspace_id: str,
        data: Dict[str, Any],
        existing: Optional[WorkspaceIntegrations] = None,
    ) -> WorkspaceIntegrations:
        base = existing or WorkspaceIntegrations(workspace_id=workspace_id)

        livekit = data.get("livekit") or {}
        if livekit:
            if "url" in livekit and livekit["url"] is not None:
                base.livekit.url = livekit["url"]
            if "api_key" in livekit and livekit["api_key"]:
                base.livekit.api_key_encrypted = encrypt_secret(livekit["api_key"])
            if "api_secret" in livekit and livekit["api_secret"]:
                base.livekit.api_secret_encrypted = encrypt_secret(livekit["api_secret"])

        ai = data.get("ai_providers") or {}
        if ai:
            mapping = {
                "openai_key": "openai_key_encrypted",
                "deepgram_key": "deepgram_key_encrypted",
                "google_key": "google_key_encrypted",
                "elevenlabs_key": "elevenlabs_key_encrypted",
                "cartesia_key": "cartesia_key_encrypted",
                "anthropic_key": "anthropic_key_encrypted",
                "assemblyai_key": "assemblyai_key_encrypted",
            }
            for plain, field_name in mapping.items():
                if plain in ai and ai[plain]:
                    setattr(base.ai_providers, field_name, encrypt_secret(ai[plain]))

        tel = data.get("telephony") or {}
        if tel:
            if "sip_domain" in tel and tel["sip_domain"] is not None:
                base.telephony.sip_domain = tel["sip_domain"]
            if "sip_username" in tel and tel["sip_username"] is not None:
                base.telephony.sip_username = tel["sip_username"]
            if "sip_password" in tel and tel["sip_password"]:
                base.telephony.sip_password_encrypted = encrypt_secret(tel["sip_password"])
            if "outbound_number" in tel and tel["outbound_number"] is not None:
                base.telephony.outbound_number = tel["outbound_number"]

        base.updated_at = datetime.now(timezone.utc)
        if not base.created_at:
            base.created_at = base.updated_at
        return base

    @staticmethod
    def _to_redacted_dict(integrations: WorkspaceIntegrations) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "workspace_id": integrations.workspace_id,
            "created_at": integrations.created_at.isoformat(),
            "updated_at": integrations.updated_at.isoformat(),
            "livekit": {
                "url": integrations.livekit.url,
                "api_key": "****" if integrations.livekit.api_key_encrypted else None,
            },
            "ai_providers": {},
            "telephony": {
                "sip_domain": integrations.telephony.sip_domain,
                "sip_username": integrations.telephony.sip_username,
                "outbound_number": integrations.telephony.outbound_number,
                "sip_password": "****" if integrations.telephony.sip_password_encrypted else None,
            },
        }

        ai_flags = {
            "openai": integrations.ai_providers.openai_key_encrypted,
            "deepgram": integrations.ai_providers.deepgram_key_encrypted,
            "google": integrations.ai_providers.google_key_encrypted,
            "elevenlabs": integrations.ai_providers.elevenlabs_key_encrypted,
            "cartesia": integrations.ai_providers.cartesia_key_encrypted,
            "anthropic": integrations.ai_providers.anthropic_key_encrypted,
            "assemblyai": integrations.ai_providers.assemblyai_key_encrypted,
        }
        for provider, value in ai_flags.items():
            if value:
                data["ai_providers"][provider] = "****"
        return data

    @staticmethod
    def _to_decrypted_dict(integrations: WorkspaceIntegrations) -> Dict[str, Any]:
        livekit = {
            "url": integrations.livekit.url,
            "api_key": decrypt_secret(integrations.livekit.api_key_encrypted),
            "api_secret": decrypt_secret(integrations.livekit.api_secret_encrypted),
        }

        ai_providers = {
            "openai_key": decrypt_secret(integrations.ai_providers.openai_key_encrypted),
            "deepgram_key": decrypt_secret(integrations.ai_providers.deepgram_key_encrypted),
            "google_key": decrypt_secret(integrations.ai_providers.google_key_encrypted),
            "elevenlabs_key": decrypt_secret(integrations.ai_providers.elevenlabs_key_encrypted),
            "cartesia_key": decrypt_secret(integrations.ai_providers.cartesia_key_encrypted),
            "anthropic_key": decrypt_secret(integrations.ai_providers.anthropic_key_encrypted),
            "assemblyai_key": decrypt_secret(integrations.ai_providers.assemblyai_key_encrypted),
        }

        telephony = {
            "sip_domain": integrations.telephony.sip_domain,
            "sip_username": integrations.telephony.sip_username,
            "sip_password": decrypt_secret(integrations.telephony.sip_password_encrypted),
            "outbound_number": integrations.telephony.outbound_number,
        }

        return {
            "workspace_id": integrations.workspace_id,
            "created_at": integrations.created_at.isoformat(),
            "updated_at": integrations.updated_at.isoformat(),
            "livekit": livekit,
            "ai_providers": ai_providers,
            "telephony": telephony,
        }

