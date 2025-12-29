"""
Session cache module for caching user data in Redis on login.
Provides fast access to user profile, workspace, assistants, phones, calls, etc.
"""
import os
import json
import logging
from typing import Optional, Any, List, Dict
from datetime import datetime, timezone

import redis.asyncio as redis

logger = logging.getLogger("session-cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# TTL configurations (in seconds)
TTL_USER_PROFILE = 3600      # 1 hour
TTL_WORKSPACE = 3600         # 1 hour
TTL_CONFIG = 300             # 5 minutes (assistants, phones, sip, tools)
TTL_CALLS = 120              # 2 minutes (recent calls)
TTL_STATS = 60               # 1 minute (analytics)
TTL_CAMPAIGNS = 120          # 2 minutes


class SessionCache:
    """
    Centralized session cache for user data.
    
    Cache key patterns:
    - user:{user_id}:profile       - User profile
    - user:{user_id}:workspace     - Workspace info
    - ws:{workspace_id}:assistants - List of assistants
    - ws:{workspace_id}:phones     - List of phone numbers
    - ws:{workspace_id}:sip        - List of SIP trunks
    - ws:{workspace_id}:tools      - List of tools
    - ws:{workspace_id}:calls      - Recent calls
    - ws:{workspace_id}:campaigns  - Active campaigns
    - assistant:{id}               - Single assistant
    - call:{id}                    - Single call record
    """
    
    _client: Optional[redis.Redis] = None
    
    @classmethod
    async def connect(cls) -> None:
        """Connect to Redis."""
        if cls._client is None:
            try:
                cls._client = redis.from_url(REDIS_URL, decode_responses=True)
                await cls._client.ping()
                logger.info(f"SessionCache connected to Redis: {REDIS_URL}")
            except Exception as e:
                logger.warning(f"SessionCache Redis connection failed: {e}")
                cls._client = None
    
    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from Redis."""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("SessionCache disconnected from Redis")
    
    @classmethod
    async def _ensure_connected(cls) -> bool:
        """Ensure Redis connection exists."""
        if cls._client is None:
            await cls.connect()
        return cls._client is not None
    
    # ==================== Core Operations ====================
    
    @classmethod
    async def get(cls, key: str) -> Optional[Dict]:
        """Get cached value by key."""
        try:
            if not await cls._ensure_connected():
                return None
            data = await cls._client.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(data)
            logger.debug(f"Cache MISS: {key}")
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
        return None
    
    @classmethod
    async def set(cls, key: str, value: Any, ttl: int = TTL_CONFIG) -> None:
        """Set cached value with TTL."""
        try:
            if not await cls._ensure_connected():
                return
            await cls._client.setex(key, ttl, json.dumps(value, default=str))
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
    
    @classmethod
    async def delete(cls, key: str) -> None:
        """Delete cached value."""
        try:
            if not await cls._ensure_connected():
                return
            await cls._client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
    
    @classmethod
    async def delete_pattern(cls, pattern: str) -> None:
        """Delete all keys matching pattern."""
        try:
            if not await cls._ensure_connected():
                return
            keys = await cls._client.keys(pattern)
            if keys:
                await cls._client.delete(*keys)
                logger.info(f"Cache INVALIDATED: {len(keys)} keys matching '{pattern}'")
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
    
    # ==================== Session Preload ====================
    
    @classmethod
    async def preload_session(cls, user_id: str, workspace_id: str, user_data: dict, workspace_data: dict = None) -> None:
        """
        Preload ALL user session data on login for fast access.
        Called from AuthService.login() after successful authentication.
        
        This method fetches and caches:
        - User profile
        - Workspace info
        - All assistants for the workspace
        - Recent calls (last 50)
        - Phone numbers
        - SIP configurations
        - Active campaigns
        """
        try:
            if not await cls._ensure_connected():
                logger.warning("Redis not available, skipping session preload")
                return
            
            # Import database services (lazy import to avoid circular deps)
            from shared.database.connection import get_database
            
            db = get_database()
            
            # 1. Cache user profile
            await cls.set(f"user:{user_id}:profile", user_data, TTL_USER_PROFILE)
            logger.debug(f"Cached user profile: {user_id}")
            
            # 2. Cache workspace if provided
            if workspace_data:
                await cls.set(f"user:{user_id}:workspace", workspace_data, TTL_WORKSPACE)
            
            # 3. Fetch and cache assistants
            try:
                assistants_cursor = db.assistants.find({"workspace_id": workspace_id}).sort("created_at", -1).limit(100)
                assistants = []
                async for doc in assistants_cursor:
                    if "_id" in doc:
                        del doc["_id"]
                    assistants.append(doc)
                if assistants:
                    await cls.set(f"ws:{workspace_id}:assistants", assistants, TTL_CONFIG)
                    logger.debug(f"Cached {len(assistants)} assistants for workspace:{workspace_id}")
            except Exception as e:
                logger.warning(f"Failed to preload assistants: {e}")
            
            # 4. Fetch and cache recent calls (last 50)
            try:
                calls_query = {
                    "$or": [
                        {"workspace_id": workspace_id},
                        {"workspace_id": None},
                        {"workspace_id": {"$exists": False}},
                    ]
                }
                calls_cursor = db.calls.find(calls_query).sort("created_at", -1).limit(50)
                calls = []
                async for doc in calls_cursor:
                    if "_id" in doc:
                        del doc["_id"]
                    calls.append(doc)
                if calls:
                    await cls.set(f"ws:{workspace_id}:calls", calls, TTL_CALLS)
                    logger.debug(f"Cached {len(calls)} recent calls for workspace:{workspace_id}")
            except Exception as e:
                logger.warning(f"Failed to preload calls: {e}")
            
            # 5. Fetch and cache phone numbers
            try:
                phones_cursor = db.phone_numbers.find({"workspace_id": workspace_id}).sort("created_at", -1)
                phones = []
                async for doc in phones_cursor:
                    if "_id" in doc:
                        del doc["_id"]
                    phones.append(doc)
                if phones:
                    await cls.set(f"ws:{workspace_id}:phones", phones, TTL_CONFIG)
                    logger.debug(f"Cached {len(phones)} phones for workspace:{workspace_id}")
            except Exception as e:
                logger.warning(f"Failed to preload phones: {e}")
            
            # 6. Fetch and cache SIP configs
            try:
                sip_cursor = db.sip_configs.find({"is_active": True}).sort("created_at", -1)
                sip_configs = []
                async for doc in sip_cursor:
                    if "_id" in doc:
                        del doc["_id"]
                    sip_configs.append(doc)
                if sip_configs:
                    await cls.set(f"ws:{workspace_id}:sip", sip_configs, TTL_CONFIG)
                    logger.debug(f"Cached {len(sip_configs)} SIP configs for workspace:{workspace_id}")
            except Exception as e:
                logger.warning(f"Failed to preload SIP configs: {e}")
            
            # 7. Fetch and cache active campaigns
            try:
                campaigns_cursor = db.campaigns.find({
                    "workspace_id": workspace_id,
                    "status": {"$in": ["draft", "scheduled", "running", "paused"]}
                }).sort("created_at", -1).limit(20)
                campaigns = []
                async for doc in campaigns_cursor:
                    if "_id" in doc:
                        del doc["_id"]
                    campaigns.append(doc)
                if campaigns:
                    await cls.set(f"ws:{workspace_id}:campaigns", campaigns, TTL_CAMPAIGNS)
                    logger.debug(f"Cached {len(campaigns)} campaigns for workspace:{workspace_id}")
            except Exception as e:
                logger.warning(f"Failed to preload campaigns: {e}")
            
            # 8. Fetch and cache tools
            try:
                tools_cursor = db.tools.find({"is_active": True}).sort("created_at", -1)
                tools = []
                async for doc in tools_cursor:
                    if "_id" in doc:
                        del doc["_id"]
                    tools.append(doc)
                if tools:
                    await cls.set(f"ws:{workspace_id}:tools", tools, TTL_CONFIG)
                    logger.debug(f"Cached {len(tools)} tools for workspace:{workspace_id}")
            except Exception as e:
                logger.warning(f"Failed to preload tools: {e}")
            
            logger.info(f"Session FULLY preloaded for user:{user_id}, workspace:{workspace_id}")
            
        except Exception as e:
            logger.error(f"Session preload failed: {e}")
    
    @classmethod
    async def invalidate_session(cls, user_id: str) -> None:
        """Invalidate all session data for a user (on logout)."""
        await cls.delete_pattern(f"user:{user_id}:*")
    
    # ==================== User & Workspace ====================
    
    @classmethod
    async def get_user_profile(cls, user_id: str) -> Optional[Dict]:
        """Get cached user profile."""
        return await cls.get(f"user:{user_id}:profile")
    
    @classmethod
    async def cache_user_profile(cls, user_id: str, data: dict) -> None:
        """Cache user profile."""
        await cls.set(f"user:{user_id}:profile", data, TTL_USER_PROFILE)
    
    @classmethod
    async def get_workspace(cls, user_id: str) -> Optional[Dict]:
        """Get cached workspace for user."""
        return await cls.get(f"user:{user_id}:workspace")
    
    # ==================== Assistants ====================
    
    @classmethod
    async def get_assistants(cls, workspace_id: str) -> Optional[List[Dict]]:
        """Get cached assistants list for workspace."""
        return await cls.get(f"ws:{workspace_id}:assistants")
    
    @classmethod
    async def cache_assistants(cls, workspace_id: str, assistants: List[Dict]) -> None:
        """Cache assistants list for workspace."""
        await cls.set(f"ws:{workspace_id}:assistants", assistants, TTL_CONFIG)
    
    @classmethod
    async def invalidate_assistants(cls, workspace_id: str) -> None:
        """Invalidate assistants cache for workspace."""
        await cls.delete(f"ws:{workspace_id}:assistants")
    
    @classmethod
    async def get_assistant(cls, assistant_id: str) -> Optional[Dict]:
        """Get cached single assistant."""
        return await cls.get(f"assistant:{assistant_id}")
    
    @classmethod
    async def cache_assistant(cls, assistant_id: str, data: dict) -> None:
        """Cache single assistant."""
        await cls.set(f"assistant:{assistant_id}", data, TTL_CONFIG)
    
    @classmethod
    async def invalidate_assistant(cls, assistant_id: str, workspace_id: str = None) -> None:
        """Invalidate assistant cache."""
        await cls.delete(f"assistant:{assistant_id}")
        if workspace_id:
            await cls.invalidate_assistants(workspace_id)
    
    # ==================== Phones & SIP ====================
    
    @classmethod
    async def get_phones(cls, workspace_id: str) -> Optional[List[Dict]]:
        """Get cached phones list."""
        return await cls.get(f"ws:{workspace_id}:phones")
    
    @classmethod
    async def cache_phones(cls, workspace_id: str, phones: List[Dict]) -> None:
        """Cache phones list."""
        await cls.set(f"ws:{workspace_id}:phones", phones, TTL_CONFIG)
    
    @classmethod
    async def invalidate_phones(cls, workspace_id: str) -> None:
        """Invalidate phones cache."""
        await cls.delete(f"ws:{workspace_id}:phones")
    
    @classmethod
    async def get_sip_configs(cls, workspace_id: str) -> Optional[List[Dict]]:
        """Get cached SIP configs list."""
        return await cls.get(f"ws:{workspace_id}:sip")
    
    @classmethod
    async def cache_sip_configs(cls, workspace_id: str, sip_configs: List[Dict]) -> None:
        """Cache SIP configs list."""
        await cls.set(f"ws:{workspace_id}:sip", sip_configs, TTL_CONFIG)
    
    @classmethod
    async def invalidate_sip(cls, workspace_id: str) -> None:
        """Invalidate SIP cache."""
        await cls.delete(f"ws:{workspace_id}:sip")
    
    # ==================== Tools ====================
    
    @classmethod
    async def get_tools(cls, workspace_id: str) -> Optional[List[Dict]]:
        """Get cached tools list."""
        return await cls.get(f"ws:{workspace_id}:tools")
    
    @classmethod
    async def cache_tools(cls, workspace_id: str, tools: List[Dict]) -> None:
        """Cache tools list."""
        await cls.set(f"ws:{workspace_id}:tools", tools, TTL_CONFIG)
    
    @classmethod
    async def invalidate_tools(cls, workspace_id: str) -> None:
        """Invalidate tools cache."""
        await cls.delete(f"ws:{workspace_id}:tools")
    
    # ==================== Calls & Analytics ====================
    
    @classmethod
    async def get_recent_calls(cls, workspace_id: str) -> Optional[List[Dict]]:
        """Get cached recent calls list."""
        return await cls.get(f"ws:{workspace_id}:calls")
    
    @classmethod
    async def cache_recent_calls(cls, workspace_id: str, calls: List[Dict]) -> None:
        """Cache recent calls list."""
        await cls.set(f"ws:{workspace_id}:calls", calls, TTL_CALLS)
    
    @classmethod
    async def invalidate_calls(cls, workspace_id: str) -> None:
        """Invalidate calls cache."""
        await cls.delete(f"ws:{workspace_id}:calls")
    
    @classmethod
    async def get_call(cls, call_id: str) -> Optional[Dict]:
        """Get cached single call."""
        return await cls.get(f"call:{call_id}")
    
    @classmethod
    async def cache_call(cls, call_id: str, data: dict) -> None:
        """Cache single call record."""
        await cls.set(f"call:{call_id}", data, TTL_CALLS)
    
    @classmethod
    async def invalidate_call(cls, call_id: str, workspace_id: str = None) -> None:
        """Invalidate call cache."""
        await cls.delete(f"call:{call_id}")
        if workspace_id:
            await cls.invalidate_calls(workspace_id)
    
    # ==================== Campaigns ====================
    
    @classmethod
    async def get_campaigns(cls, workspace_id: str) -> Optional[List[Dict]]:
        """Get cached campaigns list."""
        return await cls.get(f"ws:{workspace_id}:campaigns")
    
    @classmethod
    async def cache_campaigns(cls, workspace_id: str, campaigns: List[Dict]) -> None:
        """Cache campaigns list."""
        await cls.set(f"ws:{workspace_id}:campaigns", campaigns, TTL_CAMPAIGNS)
    
    @classmethod
    async def invalidate_campaigns(cls, workspace_id: str) -> None:
        """Invalidate campaigns cache."""
        await cls.delete(f"ws:{workspace_id}:campaigns")
