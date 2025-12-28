# Quickstart

Get the Voice Agent Platform running in less than 10 minutes using Docker.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- [Git](https://git-scm.com/) installed
- API Keys:
  - [LiveKit](https://livekit.io/) account
  - [OpenAI API Key](https://platform.openai.com/)
  - [Vobiz](https://vobiz.ai/) account for telephony

## 1. Clone the Repository

```bash
git clone https://github.com/Piyush-sahoo/Voice-AI-Platform.git
cd Voice-AI-Platform
```

## 2. Configure Environment

Copy the example environment file and add your credentials:

```bash
cp backend/.env.example backend/.env.local
```

Edit `backend/.env.local` and fill in your keys:

```ini
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# AI Providers
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...

# Database
MONGO_URI=mongodb://mongo:27017/vobiz

# Vobiz Telephony
SIP_DOMAIN=sbc.vobiz.ai
SIP_USERNAME=your_username
SIP_PASSWORD=your_password
```

## 3. Start the Platform

Launch all services with Docker Compose:

```bash
docker-compose up -d --build
```

This starts:
- **Gateway** (http://localhost:8000) - API entry point
- **Frontend** (http://localhost:3000) - Dashboard
- **Config Service** (Port 8002) - Configuration management
- **Analytics Service** (Port 8001) - Call analytics
- **Orchestration Service** (Port 8003) - Campaign management
- **Agent Worker** - Voice AI processing
- **Redis** - Caching and queuing
- **MongoDB** - Database

## 4. Verify Installation

Check if all services are running:

```bash
docker-compose ps
```

You should see all services in "Up" state.

Access the **API Documentation**: http://localhost:8000/docs

## 5. Make Your First Call

Use the included automation script to test the entire workflow:

```bash
python scripts/full_api_automation.py
```

This script will:
1. Create an AI assistant
2. Configure SIP settings
3. Add a phone number
4. Make a test call
5. Retrieve call analytics

## 🎉 Success!

You now have a fully functional Voice Agent Platform running locally!

## Next Steps

- [Create Custom Assistants](./guides/creating-assistants)
- [Configure SIP Trunks](./guides/sip-configuration)
- [Launch Campaigns](./guides/outbound-campaigns)
- [Explore the API](../api)

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs -f gateway

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

### Database connection errors
Make sure MongoDB is running and MONGO_URI is correct in `.env.local`.

### Agent won't connect to LiveKit
Verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` are correct.

Need help? [Open an issue on GitHub](https://github.com/Piyush-sahoo/Voice-AI-Platform/issues)
