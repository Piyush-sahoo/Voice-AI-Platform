# Voice AI Platform (Vobiz)

A production-ready, scalable Voice AI orchestration platform built with LiveKit, OpenAI/Azure, Deepgram, and Next.js.

## 🚀 Features

*   **Real-time Voice Agents**: Low-latency conversational AI using LiveKit Agents.
*   **Outbound Campaigns**: Schedule and blast calls via CSV upload using Celery & Redis.
*   **Inbound Handling**: SIP trunking support for receiving calls.
*   **Call Analytics**: Detailed logs, recording playback (S3 compatible), and cost estimation.
*   **Modern UI**: React/Next.js frontend with shading/dark mode support.
*   **Scalable Architecture**: Dockerized services for API, worker, frontend, and redis.

## 🛠️ Tech Stack

*   **Frontend**: React, Vite, TailwindCSS, Shadcn/UI
*   **Backend**: Python (FastAPI), LiveKit SDK
*   **Database**: MongoDB (Atlas or Local)
*   **Queue**: Redis + Celery
*   **Voice/AI**: LiveKit, Deepgram (STT), OpenAI/Azure (LLM/TTS)
*   **Infrastructure**: Docker Compose

## 📋 Prerequisites

*   Docker & Docker Compose
*   LiveKit Cloud Account (or self-hosted)
*   OpenAI API Key
*   MongoDB URI
*   AWS S3 Credentials (for recording storage/playback)

## ⚡ Quick Start

### 1. Configure Environment
Create a `.env.local` file in `livekit-outbound-calls/` based on `.env.example`.

**Required Variables:**
```env
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=API...
LIVEKIT_API_SECRET=Secret...

# AI
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=... (for analysis)

# Database
MONGODB_URI=mongodb+srv://...

# AWS S3 (Essential for Recordings)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
AWS_BUCKET_NAME=your-bucket
```

### 2. Run with Docker
The entire platform can be launched with a single command:
```bash
docker-compose up -d --build
```

### 3. Access Services
*   **Frontend**: http://localhost:3000
*   **API Docs**: http://localhost:8000/docs

## 📂 Project Structure

```
├── frontend/                 # React UI application
│   ├── Dockerfile           # Nginx build for frontend
│   └── src/                 # Pages, Components, Hooks
├── livekit-outbound-calls/   # Python Backend & Agent
│   ├── agent/               # LiveKit Worker Agent
│   ├── api/                 # FastAPI Endpoints
│   ├── services/            # Business Logic (S3, Calls, SIP)
│   ├── tasks_queue/         # Celery Worker for Campaigns
│   └── Dockerfile           # Unified backend image
└── docker-compose.yml        # Orchestration
```

## 🔒 Security Note
*   **Gitignore**: All `.env` files and `test_*.json` data files are ignored.
*   **Authentication**: Basic JWT implementation available (configurable).
*   **S3**: Recordings are accessed via short-lived presigned URLs.

## 📝 Deployment
For production:
1.  Ensure `LIVEKIT_URL` points to your production LiveKit instance.
2.   Use a robust MongoDB provider (Atlas/AWS DocumentDB).
3.   Set `AUTH_ENABLED=true` in backend config if using built-in auth.
4.   Run behind a reverse proxy (Nginx/Traefik) with SSL.
