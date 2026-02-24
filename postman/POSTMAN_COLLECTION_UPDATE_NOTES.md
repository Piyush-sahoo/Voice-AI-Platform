# Postman Collection Update Notes

Last updated: 2026-02-23
Collection file: [postman_collection.json](postman_collection.json)

## What was added

### 1) New collection variables
- `accessToken`
- `refreshToken`
- `assistant_id`
- `campaign_id`
- `call_id`
- `document_id`

### 2) Knowledge folder (new)
Added requests for implemented KB/RAG APIs:
- `Create Knowledge (Text)`
- `Create Knowledge (URL)`
- `Create Knowledge (File)`
- `List Knowledge`
- `Resync Knowledge`
- `Delete Knowledge`

### 3) Authentication folder (new)
Added requests for auth APIs:
- `Signup`
- `Login`
- `Refresh Token`
- `Get My Profile`
- `Create API Key`
- `List API Keys`

### 4) Queue folder (new)
Added queue observability requests:
- `Queue Health`
- `Queue Stats`

## What you need to set before running

1. Set `baseUrl` (default is `http://localhost:8000`).
2. Run `Login` and copy tokens into variables:
   - `accessToken`
   - `refreshToken`
3. Set resource IDs as you create data:
   - `assistant_id`
   - `campaign_id`
   - `call_id`
   - `document_id`

## Suggested run order

1. `Authentication -> Signup` (one-time)
2. `Authentication -> Login`
3. `Assistants -> Create Assistant` (save `assistant_id`)
4. `Knowledge -> Create Knowledge (Text/URL/File)`
5. `Knowledge -> List Knowledge` (save `document_id`)
6. `Knowledge -> Resync Knowledge`
7. `Queue -> Queue Health` / `Queue Stats`

## Ongoing maintenance checklist (for future features)

When you add a backend route, update Postman by:

1. Add/update endpoint request in matching folder.
2. Add needed variables if endpoint uses path params.
3. Add auth header when route is protected.
4. Update this file with:
   - date
   - added/changed requests
   - required new variables

## Current known scope

Collection now reflects implemented domains:
- Health
- Assistants
- Phone Numbers
- SIP Configs
- Calls
- Campaigns
- Tools
- Knowledge
- Authentication
- Queue
- Analytics
