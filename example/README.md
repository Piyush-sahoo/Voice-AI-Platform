# LiveKit Voice Agent - Vobiz Integration

AI Voice Agent for handling inbound and outbound calls using LiveKit with Vobiz SIP trunking.

## Quick Start

### 1. Install Dependencies
```bash
cd LiveKit
uv sync
```

### 2. Configure Environment
Copy `.env.local.example` to `.env.local` and fill in:
```env
# LiveKit Credentials
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI API Key
OPENAI_API_KEY=your-openai-key

# Deepgram API Key (for STT)
DEEPGRAM_API_KEY=your-deepgram-key

# Vobiz SIP Configuration
VOBIZ_SIP_DOMAIN=your-trunk-id.sip.vobiz.ai
VOBIZ_USERNAME=your-username
VOBIZ_PASSWORD=your-password
VOBIZ_OUTBOUND_NUMBER=+91xxxxxxxxxx
VOBIZ_INBOUND_NUMBER=+91xxxxxxxxxx
```

### 3. Setup LiveKit Inbound Trunk
```bash
uv run python setup_inbound.py
```
This creates the LiveKit inbound trunk and dispatch rule.

### 4. Configure Vobiz Trunk
In Vobiz Dashboard → SIP Trunks → Your Trunk:
- Set **Primary URI** to your LiveKit SIP endpoint (e.g., `sip:48bltwoad8r.sip.livekit.cloud`)
- Link your phone number

### 5. Run the Agent
```bash
# Development mode (auto-reload on changes)
uv run python agent_inbound.py dev

# Production mode
uv run python agent_inbound.py start
```

---

## File Reference

### Core Agent Files
| File | Description |
|------|-------------|
| `agent_inbound.py` | Main inbound call handler - answers incoming calls |
| `agent_outbound_caller.py` | Outbound call agent |
| `agent.py` | Base agent implementation |
| `agent_openai.py` | OpenAI-based agent variant |

### Setup Scripts
| File | Description |
|------|-------------|
| `setup_inbound.py` | Creates LiveKit inbound trunk and dispatch rule |
| `setup_inbound_trunk.py` | Standalone inbound trunk setup |
| `setup_dispatch_rule.py` | Standalone dispatch rule setup |
| `setup_outbound_trunk.py` | Creates LiveKit outbound trunk |

### Utility Scripts
| File | Description |
|------|-------------|
| `configure_inbound.py` | Alternative inbound configuration |
| `dispatch_outbound_call.py` | Dispatch an outbound call |
| `make_outbound_call.py` | Make a test outbound call |
| `update_vobiz_inbound.py` | Update Vobiz trunk settings |

### Configuration
| File | Description |
|------|-------------|
| `.env.local` | Environment variables (credentials, API keys) |

---

## Inbound Call Flow

```
1. Caller dials your Vobiz number (+912271264190)
2. Vobiz receives the call
3. Vobiz forwards to LiveKit SIP endpoint (Primary URI)
4. LiveKit inbound trunk matches the call
5. Dispatch rule creates a room and dispatches agent
6. Agent answers and greets the caller
7. Conversation happens!
```

---

## Troubleshooting

### 408 Request Timeout
- Verify Vobiz **Primary URI** matches your LiveKit SIP endpoint
- Check agent is running and registered
- Verify inbound trunk number matches Vobiz linked number

### Agent Not Registering
- Check `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` in `.env.local`
- Ensure network connectivity to LiveKit Cloud

### No Audio
- Verify `DEEPGRAM_API_KEY` and `OPENAI_API_KEY` are valid
- Check agent logs for STT/TTS errors

---

## Current Configuration

**Vobiz Trunk**: `5aad89b3.sip.vobiz.ai`  
**Primary URI**: `sip:48bltwoad8r.sip.livekit.cloud`  
**Inbound Number**: `+912271264190`  
**Agent Name**: `voice-assistant`
