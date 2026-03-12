### Overview

This document summarizes all architecture and code changes made in this session to:

- Enforce **strict multi-tenant isolation** for calls and telephony.
- Introduce a **workspace-centric integrations model** (`workspace_integrations`).
- Add a **frontend onboarding wizard** to configure LiveKit, AI providers, and telephony per workspace.

The goals were:

- Each workspace has its own LiveKit + AI + telephony credentials.
- Telephony credentials are stored **once** (in `workspace_integrations.telephony`).
- All calls are **workspace-scoped** and never leaked across tenants.

---

### Backend Changes

#### 1. Central configuration / environment loading

File: `backend/shared/settings.py` (existing, behavior clarified)

- Continues to load **deployment-level** env vars:
  - LiveKit: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.
  - AI providers: `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`, `ANTHROPIC_API_KEY`, `CARTESIA_API_KEY`, `ASSEMBLYAI_API_KEY`.
  - Infra: `MONGODB_URI`, `MONGODB_DB_NAME`, `REDIS_URL`, `QDRANT_URL`, `AWS_*`, `JWT_SECRET_KEY`, `INTERNAL_API_KEY`, `OUTBOUND_TRUNK_ID`.
- These now act as **global defaults** when workspace-specific integrations are missing.

No breaking changes here; this remains the deployment config source.

#### 2. Workspace integrations model & encryption

**Models**

File: `backend/shared/database/models/workspace_integrations.py`

- New Pydantic models:
  - `LiveKitIntegration`:
    - `url`, `api_key_encrypted`, `api_secret_encrypted`.
  - `AIProvidersIntegration`:
    - `openai_key_encrypted`, `deepgram_key_encrypted`, `google_key_encrypted`,
      `elevenlabs_key_encrypted`, `cartesia_key_encrypted`, `anthropic_key_encrypted`,
      `assemblyai_key_encrypted`.
  - `TelephonyIntegration`:
    - `sip_domain`, `sip_username`, `sip_password_encrypted`, `outbound_number`.
  - `WorkspaceIntegrations`:
    - `workspace_id` (string, indexed), `livekit`, `ai_providers`, `telephony`,
      `created_at`, `updated_at`, with `to_dict` / `from_dict` helpers.

File: `backend/shared/database/models/__init__.py`

- Exports new models:
  - `WorkspaceIntegrations`, `LiveKitIntegration`, `AIProvidersIntegration`, `TelephonyIntegration`.

**Encryption**

File: `backend/shared/security/crypto.py`

- New AES-256-GCM helpers:
  - `encrypt_secret(secret: Optional[str]) -> Optional[str>`
  - `decrypt_secret(encrypted_secret: Optional[str]) -> Optional[str>`
- Master key:
  - Primary: `INTEGRATION_SECRET_KEY` (preferred).
  - Fallback (for dev / backward compatibility): `JWT_SECRET_KEY` or a static `"development-integration-key"`.
- Encryption layout:
  - `base64( iv (12 bytes) || tag (16 bytes) || ciphertext )`.
- Dependency added to `backend/requirements.txt`:
  - `cryptography>=42.0.0`.

**Service**

File: `backend/services/config/workspace_integrations_service.py`

- Collection: `workspace_integrations` with `unique` index on `workspace_id`.
- Methods:
  - `create_workspace_integrations(workspace_id, data)`:
    - Fails if doc already exists.
    - Encrypts secrets and inserts a `WorkspaceIntegrations` document.
  - `get_workspace_integrations(workspace_id, decrypt=False, redacted=False)`:
    - `decrypt=True`: returns plaintext-keys structure (internal use only).
    - `redacted=True`: masks all secrets as `"****"` (API-safe view).
  - `update_workspace_integrations(workspace_id, data)`:
    - Patches existing doc, encrypting updated secrets.
  - `delete_workspace_integrations(workspace_id)`:
    - Deletes doc for that workspace.
- Internal helpers:
  - `_build_document(...)`: merges updates, encrypts secrets.
  - `_to_redacted_dict(...)`: redacted API representation.
  - `_to_decrypted_dict(...)`: decrypted internal representation.

#### 3. Workspace integrations API (Config + Gateway services)

**Config Service**

File: `backend/services/config/routers/workspace_integrations.py`

- Endpoints:
  - `POST /workspace/integrations`:
    - Requires authenticated `User`.
    - Only `owner` / `admin` (by `user.role`) may create.
    - Accepts:
      - `livekit: { url, api_key, api_secret }`
      - `ai_providers: { openai_key, deepgram_key, google_key, elevenlabs_key, cartesia_key, anthropic_key, assemblyai_key }`
      - `telephony: { sip_domain, sip_username, sip_password, outbound_number }`
    - Writes encrypted values via `WorkspaceIntegrationService.create_workspace_integrations`.
    - Returns **redacted** view (`"****"` for secrets).
  - `GET /workspace/integrations`:
    - Returns redacted view for `user.workspace_id`.
  - `PATCH /workspace/integrations`:
    - Partial update (only fields present are modified).
    - Redacted response.
  - `DELETE /workspace/integrations`:
    - Deletes workspace’s integrations (owner/admin only).

**Gateway Service**

File: `backend/services/gateway/routers/workspace_integrations.py`

- Proxies the above routes through `/api/workspace/integrations`:
  - Adds `X-Workspace-ID` via `build_proxy_headers(req, user.workspace_id)`.
  - Does not see decrypted secrets; all responses remain redacted.

File: `backend/services/gateway/main.tsx`

- Adds router:
  - `app.include_router(workspace_integrations.router, prefix="/api", tags=["Workspace Integrations"], dependencies=[Depends(get_current_user)])`.

#### 4. Agent worker: per-workspace AI provider keys

File: `backend/services/agent/worker.py`

- Enhancements in `entrypoint(ctx: agents.JobContext)`:
  - After parsing metadata and extracting `workspace_id`, the worker now loads per-workspace integrations:

    ```python
    integrations = await WorkspaceIntegrationService.get_workspace_integrations(
        workspace_id, decrypt=True
    )
    ```

  - Builds `api_keys` by merging workspace-level keys with env defaults:

    ```python
    api_keys = {
      "openai":  ai_cfg.get("openai_key")  or config.OPENAI_API_KEY,
      "deepgram": ai_cfg.get("deepgram_key") or config.DEEPRAM_API_KEY,
      ...
    }
    ```

  - Logs (without secrets) which path is used:
    - When workspace keys present:
      - `"Using workspace-specific AI provider credentials for workspace_id=..."`
    - When falling back to env:
      - `"No workspace-specific AI provider credentials found, falling back to env for workspace_id=..."`
    - On error loading integrations:
      - `"Failed to load workspace integrations: ..."`

  - Passes `api_keys` into the model factory:

    ```python
    if mode == "pipeline":
        session = AgentSession(
            stt=get_stt(voice_config, api_keys=api_keys),
            llm=get_llm(voice_config, api_keys=api_keys),
            tts=get_tts(voice_config, api_keys=api_keys),
        )
    else:
        session = AgentSession(
            llm=get_realtime_model(voice_config, api_keys=api_keys),
        )
    ```

#### 5. Model factory: inject provider keys into LiveKit plugins

File: `backend/services/agent/model_factory.py`

- New helpers:
  - `_provider_env(api_keys)` builds the provider env var map.
  - `_scoped_env(env_updates)` temporarily applies env vars only during client construction.

  This avoids **process-global credential bleed** across jobs/workspaces while still allowing LiveKit plugin clients to pick up the correct per-workspace credentials at construction time.

- Updated signatures (backward compatible: `api_keys` optional):
  - `get_stt(voice_config, api_keys=None)`
  - `get_llm(voice_config, api_keys=None)`
  - `get_tts(voice_config, api_keys=None)`
  - `get_realtime_model(voice_config, api_keys=None)`

- Each function calls `_apply_api_keys(api_keys)` before constructing plugin clients.
  - Each function constructs the provider client inside `_scoped_env(_provider_env(api_keys))`.

#### 9. Inbound SIP (LiveKit) dispatch + multi-tenant bootstrap

This session uncovered a key gap in the inbound SIP pipeline: LiveKit SIP dispatch can start an agent job **without** going through the existing `/inbound-call` handler, meaning the worker receives no `ctx.job.metadata` and therefore cannot resolve `assistant_id` / `workspace_id` or use workspace-scoped keys.

**Config Service – correct SIP dispatch rule construction**

File: `backend/services/config/phone_sip_service.py`

- Fixed SIP dispatch rule creation to use LiveKit’s supported schema:
  - `SIPDispatchRuleIndividual` configures room routing (`room_prefix="call-"`).
  - Agent attachment is configured via `room_config.agents[]` (`RoomAgentDispatch(agent_name="voice-assistant", ...)`) rather than an invalid `agent_name` field on `SIPDispatchRuleIndividual`.
- Added agent dispatch metadata to the rule:
  - `metadata={"is_inbound": true, "to_number": "<provisioned DID>"}` (JSON string)
  - This ensures the worker can reliably determine the **dialed inbound number** (DID), not the caller’s number.

**Agent Service – inbound runtime tenant/assistant resolution**

File: `backend/services/agent/worker.py`

- Added inbound bootstrap logic for LiveKit-driven inbound jobs where `ctx.job.metadata` is missing or incomplete:
  - Reads `to_number` from metadata when available (provided by SIP dispatch rule agent metadata).
  - Falls back to inspecting room participants / room name heuristics only when needed.
  - Resolves assistant/workspace by DID:

    - `PhoneNumberService.get_assistant_by_number(to_number)`
    - Optionally enriches with `AssistantService.get_assistant_for_call(assistant_id)` (e.g. webhook URL)

- Ensures calls dispatched directly by LiveKit still participate in analytics + webhooks:
  - Creates a `CallRecord` in Mongo for the LiveKit room name (`call_id == room_name == ctx.room.name`) via `ensure_inbound_call_record(...)`.
  - Marks `answered`/`completed` and triggers analytics post-call as the existing worker already does.

- Ensures workspace-scoped AI credentials are used for inbound:
  - After resolving `workspace_id`, the worker loads `WorkspaceIntegrationService.get_workspace_integrations(workspace_id, decrypt=True)` and uses those keys for STT/LLM/TTS construction.

**Result**

- Inbound calls now:
  - Resolve `assistant_id` and `workspace_id` correctly.
  - Use workspace-level AI provider keys (no platform-env fallback when configured).
  - Create a `CallRecord`, enabling analytics/webhook flows to work for inbound SIP calls that bypass `/inbound-call`.

#### 6. LiveKit per workspace: Config + Analytics services

**Analytics Service**

File: `backend/services/analytics/call_service.py`

- `_dispatch_agent(...)` now derives LiveKit credentials as:
  - Defaults from `shared.settings.config` (`LIVEKIT_*`).
  - If `call.workspace_id` has integrations:
    - Override with `workspace_integrations.livekit.{url, api_key, api_secret}`.

This allows each workspace to target its own LiveKit project.

**Config Service (SIP/phone numbers)**

File: `backend/services/config/phone_sip_service.py`

- Inbound number creation / cleanup and SIP trunk creation already use LiveKit per above; we further refactored outbound trunk creation (see below under telephony).

#### 7. Strict multi-tenant call isolation

File: `backend/services/analytics/call_service.py`

- **Create call**:

  ```python
  async def create_call(..., workspace_id: Optional[str] = None, ...):
      if not workspace_id:
          raise ValueError("workspace_id is required when creating a call")

      call = CallRecord(
          call_id=call_id,
          workspace_id=workspace_id,
          ...
      )
      await db.calls.insert_one(call.to_dict())
  ```

  - Enforces that every call has a workspace.
  - Prevents accidental creation of unscoped call records.

- **Get call**:

  ```python
  query = {"call_id": call_id}
  if workspace_id:
      query["workspace_id"] = workspace_id
  ```

  - Removes legacy `$or` on `workspace_id is null/absent`.
  - Strictly enforces workspace filter when called from tenant-aware endpoints.

- **List calls**:

  ```python
  if not workspace_id:
      return []

  if status is None and phone_number is None and skip == 0:
      cached = await SessionCache.get_recent_calls(workspace_id)
      ...

  query = {"workspace_id": workspace_id}
  if status: query["status"] = status.value
  if phone_number: query["phone_number"] = phone_number
  ```

  - No more `$or` including calls with `workspace_id == null`.
  - Hard requirement: you can only list calls for a specific workspace.

**Internal callers updated to pass workspace_id**

- Campaigns:

  File: `backend/services/orchestration/campaign_service.py`

  ```python
  call = await CallService.create_call(
      call_request,
      workspace_id=campaign.workspace_id,
  )
  ```

- Celery campaign tasks:

  File: `backend/services/orchestration/tasks_queue/tasks.py`

  - Each batch contact includes:

    ```python
    call_data = {
        "phone_number": contact.phone_number,
        "assistant_id": campaign.assistant_id,
        "campaign_id": campaign_id,
        "contact_index": contact_index,
        "workspace_id": campaign.workspace_id,
    }
    ```

  - The async `create_call` helper passes `workspace_id=call_data["workspace_id"]` into `CallService.create_call`.

Result: **All new calls created by campaigns and background tasks are workspace-scoped**.

#### 8. Telephony credentials: single source of truth

**Goal**

- `workspace_integrations.telephony` holds **provider credentials** (SIP domain, username, password, outbound number).
- `sip_configs` hold **trunk configuration only** (name, from_number, trunk_id, defaults, description) and remain workspace-scoped.

**Implementation**

File: `backend/services/config/phone_sip_service.py`

- `SipConfigService.create_sip_config` now:

  - Requires `workspace_id`:

    ```python
    if not workspace_id:
        raise ValueError("workspace_id is required when creating SIP configs")
    ```

  - Loads telephony integration:

    ```python
    integrations = await WorkspaceIntegrationService.get_workspace_integrations(
        workspace_id, decrypt=True
    )
    telephony = integrations.get("telephony") if integrations else None
    if not telephony:
        raise ValueError(
            "Telephony provider must be configured in workspace integrations before creating SIP configs"
        )
    sip_domain = telephony.get("sip_domain")
    sip_username = telephony.get("sip_username")
    sip_password = telephony.get("sip_password")
    if not sip_domain or not sip_username or not sip_password:
        raise ValueError("Telephony provider configuration is incomplete for this workspace")
    ```

  - Uses **telephony credentials from integrations** when creating new LiveKit outbound trunk:

    ```python
    trunk_request = api.CreateSIPOutboundTrunkRequest(
        trunk=api.SIPOutboundTrunkInfo(
            name=request.name,
            address=sip_domain,
            numbers=[request.from_number],
            auth_username=sip_username,
            auth_password=sip_password,
        )
    )
    ```

  - Still persists the full `SipConfig` object (including `sip_domain`, `sip_username`, `sip_password`, `from_number`, etc.) for backwards compatibility, but those fields are no longer used for new trunk creation logic.

**Workspace isolation checks**

- Existing methods already ensure:
  - `list_sip_configs`, `get_sip_config`, `get_default_sip_config`, `update_sip_config`, `delete_sip_config` all filter by `workspace_id` when provided.
  - `PhoneNumberService` consistently uses `workspace_id` when listing/inserting/deleting phone numbers, and inbound assistant resolution uses `phone_numbers.workspace_id`.

---

### Frontend Changes

#### 1. API client for workspace integrations

File: `frontend/src/lib/api.ts`

- Added typed interfaces:

  - `LiveKitIntegrationsResponse`, `AIProvidersIntegrationsResponse`, `TelephonyIntegrationsResponse`, `WorkspaceIntegrationsResponse`.
  - `WorkspaceIntegrationsPayload` for POST/PATCH payloads.

- Added `workspaceIntegrationsApi`:

  ```ts
  export const workspaceIntegrationsApi = {
    get: () => api.get<WorkspaceIntegrationsResponse>("/api/workspace/integrations"),
    create: (data: WorkspaceIntegrationsPayload) =>
      api.post<WorkspaceIntegrationsResponse>("/api/workspace/integrations", data),
    update: (data: WorkspaceIntegrationsPayload) =>
      api.patch<WorkspaceIntegrationsResponse>("/api/workspace/integrations", data),
    delete: () => api.delete<{ message: string }>("/api/workspace/integrations"),
  };
  ```

Secrets are always redacted (`"****"`) by the backend; the frontend never stores plaintext secrets coming from responses.

#### 2. Onboarding wizard route

File: `frontend/src/App.tsx`

- Imported onboarding page:

  ```tsx
  import Onboarding from "./pages/onboarding";
  ```

- Added protected route:

  ```tsx
  <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
  ```

#### 3. Sidebar link to onboarding

File: `frontend/src/components/layout/AppSidebar.tsx`

- Added `Sparkles` icon to imports.
- Added “Onboarding” entry to `bottomNavigation`:

  ```ts
  const bottomNavigation = [
    { name: "Onboarding", href: "/onboarding", icon: Sparkles },
    { name: "Documentation", href: "...", icon: FileText },
    { name: "Settings", href: "/settings", icon: Settings },
  ];
  ```

Users can now open the wizard from the sidebar instead of manually navigating.

#### 4. Onboarding step components

Folder: `frontend/src/components/onboarding/`

**`LiveKitStep.tsx`**

- Stateless component handling LiveKit fields:
  - `url`, `api_key`, `api_secret`, and flags `apiKeyConfigured`, `apiSecretConfigured`.
- Shows `Configured ✓` badge when backend returned `"****"` for those fields.
- Uses password inputs for secrets; typing clears the configured flag locally (meaning “overwrite on save”).

**`AIProvidersStep.tsx`**

- Stateless component handling AI provider keys:
  - `openai_key`, `deepgram_key`, `google_key`, `elevenlabs_key`, `cartesia_key`, `anthropic_key`, `assemblyai_key`.
  - `configured` flags per provider to indicate previously configured keys.
- All inputs are password fields; new input clears the corresponding `configured` flag.
- Provides minimal UX guidance: at least one provider recommended.

**`TelephonyStep.tsx`**

- Stateless telephony form:
  - Required: `sip_domain`, `sip_username`.
  - Optional: `sip_password`, `outbound_number`.
  - Flag `sipPasswordConfigured` for masked existing password.

**`ReviewStep.tsx`**

- Read-only summary for:
  - LiveKit, AI providers, Telephony.
- All secret fields are displayed as:
  - `********` if configured (either legacy or newly provided).
  - `Not configured` when empty.
- Ensures plaintext secrets are never shown, even immediately after entry.

#### 5. Onboarding page (`/onboarding`)

File: `frontend/src/pages/onboarding/index.tsx`

- Maintains the full wizard state:

  ```ts
  interface OnboardingFormState {
    livekit: LiveKitFormState;
    ai_providers: AIProvidersFormState;
    telephony: TelephonyFormState;
  }
  ```

- On mount:
  - `GET /api/workspace/integrations`:
    - If 404 → no existing integrations; wizard starts blank.
    - If found → populates non-secret fields and sets `configured` flags based on `"****"` from backend.
  - Secret inputs always start empty; backend values are never mirrored into inputs.

- Navigation & validation:
  - 4 steps with “Step X of 4” indicator.
  - Validation:
    - Step 1: `livekit.url` is required.
    - Step 3: `telephony.sip_domain` and `sip_username` required.
  - Buttons:
    - `Back`, `Next`, `Finish` with proper disabling during submit.

- Submission:
  - Builds `WorkspaceIntegrationsPayload` including **only non-empty fields**:
    - Secret fields are omitted when left empty → backend keeps existing encrypted values.
  - Uses:
    - `POST` when no existing doc (`hasExisting === false`).
    - `PATCH` when doc exists (`hasExisting === true`).
  - On success:
    - Shows success toast.
    - Redirects to `/dashboard`.

- Security:
  - Never stores or displays plaintext secrets from backend.
  - Only uses plaintext secrets that user just typed into the form, and only sends them once to the backend for encryption.

---

### Summary of Outcomes

- **Multi-tenancy**:
  - All new calls are created with a non-null `workspace_id`.
  - Tenant-visible call APIs (`GET /api/calls`, `GET /api/calls/{id}` with user context) strictly filter by `workspace_id`.
  - Campaigns and Celery tasks create calls in the correct workspace.

- **Integrations model**:
  - `workspace_integrations` is now the central, encrypted store for:
    - `livekit`, `ai_providers`, and `telephony` settings per workspace.
  - API endpoints exist for owners/admins to configure integrations; responses are redacted.

- **Telephony**:
  - SIP credentials (domain/username/password) are taken from `workspace_integrations.telephony`.
  - `sip_configs` represent trunk metadata (name, from_number, trunk_id, description, defaults) and remain workspace-scoped.
  - Existing `sip_configs` fields for credentials remain in the DB but are no longer trusted for new trunk creation.

- **Frontend**:
  - `/onboarding` wizard walks new workspaces through LiveKit, AI provider, and telephony configuration.
  - Wizard integrates with new backend APIs, honors masking, and never leaks secrets.
  - Sidebar now includes an “Onboarding” tab for easier discovery. 
