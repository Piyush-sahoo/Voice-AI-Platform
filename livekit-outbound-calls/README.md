# LiveKit Voice AI Platform

A production-ready **outbound calling platform** powered by LiveKit and OpenAI Realtime API. Build, manage, and scale AI-driven voice agents with full API control.

## 🚀 Features

- **AI Assistants** - Customizable voice agents with configurable prompts, voices, and behaviors
- **Dynamic SIP Trunks** - Auto-create LiveKit SIP trunks from your credentials
- **Batch Campaigns** - Run thousands of calls with concurrency control
- **Custom Tools** - Function calling for live data lookups during calls
- **Post-Call Analysis** - Gemini-powered sentiment and summary analysis
- **Call Analytics** - Dashboard-ready statistics and tracking

## 📋 Prerequisites

- Python 3.11+
- MongoDB database
- LiveKit Cloud account
- OpenAI API key
- Google Gemini API key (for analysis)
- [Vobiz.ai](https://vobiz.ai) SIP credentials (for telephony)

## ⚡ Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/Piyush-sahoo/LiveKit-Platform.git
cd LiveKit-Platform
pip install uv
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local` with your credentials:
- LiveKit URL, API key, and secret
- OpenAI API key
- MongoDB URI
- Google Gemini API key (optional)
- AWS S3 credentials (optional, for recordings)

### 3. Start Services

**Terminal 1 - API Server:**
```bash
uv run python run_server.py
```

**Terminal 2 - Agent Worker:**
```bash
uv run python run_agent.py start
```

API runs at `http://localhost:8000`

---

## 🐳 Docker Deployment

```bash
# Start all services (API, Agent, MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🏗️ Architecture

### Core Components

| Component | Description |
|-----------|-------------|
| **API Server** | FastAPI REST endpoints for all operations |
| **Agent Worker** | LiveKit voice agent with OpenAI Realtime |
| **MongoDB** | Persistent storage for all entities |
| **LiveKit Cloud** | Real-time voice infrastructure |

### Entities

- **Assistants** - AI agent configurations (instructions, voice, first message)
- **Phone Numbers** - Inventory of available caller IDs
- **SIP Configs** - SIP provider credentials with auto trunk creation
- **Calls** - Individual call records with transcripts and analysis
- **Campaigns** - Batch calling with contact lists and progress tracking
- **Tools** - Custom function calling definitions

---

## 📡 API Overview

All endpoints are prefixed with `/api`

| Resource | Endpoints | Description |
|----------|-----------|-------------|
| Assistants | CRUD | Manage AI agent configurations |
| Phone Numbers | CRUD | Manage phone number inventory |
| SIP Configs | CRUD | SIP credentials with auto-trunk |
| Calls | Create, List, Analyze | Outbound calling |
| Campaigns | CRUD + Start/Pause/Cancel | Batch calling |
| Tools | CRUD + Test | Custom function tools |
| Analytics | Stats, Summary | Dashboard data |

See `postman_collection.json` for complete API documentation.

---

## 📁 Project Structure

```
livekit-outbound-calls/
├── agent/
│   └── worker.py         # LiveKit agent with function tools
├── api/
│   ├── main.py           # FastAPI app
│   └── routers/          # API endpoints
├── config/
│   └── settings.py       # Environment configuration
├── database/
│   ├── connection.py     # MongoDB connection
│   └── models/           # Pydantic models
├── services/             # Business logic layer
├── postman_collection.json
├── run_server.py
└── run_agent.py
```

---

## 🔧 Key Concepts

### Dynamic SIP Trunk Creation

When you create a SIP config with credentials, the platform automatically creates a LiveKit outbound trunk. No manual trunk setup required.

### Campaign Execution

Campaigns support:
- Concurrent call limits
- Start/Pause/Resume/Cancel
- Per-contact status tracking
- Automatic progress updates

### Function Tools

Built-in tools:
- `get_current_time` - Returns current time
- `end_call` - Gracefully ends calls

Custom webhook tools can be defined via the API for CRM lookups, appointment scheduling, etc.

### Post-Call Analysis

After calls complete, trigger Gemini analysis for:
- Success/failure determination
- Sentiment analysis
- Key topics extraction
- Action items

---

## 🧪 Testing

Import `postman_collection.json` into Postman for complete API testing.

---

## 🔒 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| LIVEKIT_URL | ✅ | LiveKit WebSocket URL |
| LIVEKIT_API_KEY | ✅ | LiveKit API key |
| LIVEKIT_API_SECRET | ✅ | LiveKit API secret |
| OPENAI_API_KEY | ✅ | OpenAI API key |
| MONGODB_URI | ✅ | MongoDB connection string |
| GOOGLE_API_KEY | ⬜ | Gemini API (for analysis) |
| AWS_* | ⬜ | S3 for recordings |

---

## 📄 License

MIT License

---

## 🤝 Support

- [Vobiz Documentation](https://docs.vobiz.ai) - Telephony provider
- [LiveKit Documentation](https://docs.livekit.io) - Voice infrastructure
- [OpenAI Realtime API](https://platform.openai.com/docs) - AI models
