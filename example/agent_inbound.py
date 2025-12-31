"""
LiveKit AI Voice Agent for Inbound Calls

This agent handles inbound SIP calls from Vobiz using:
- Deepgram for Speech-to-Text (STT)
- OpenAI for Text-to-Speech (TTS) and LLM
- Automatic greeting when caller connects

The agent is automatically spawned when an inbound call arrives,
matched by dispatch rules configured in LiveKit.
"""

import logging
import os
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import openai, deepgram, silero

load_dotenv(".env.local")

logger = logging.getLogger(__name__)


class VoiceAssistant(Agent):
    """AI voice assistant for handling inbound calls."""

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful and friendly voice AI assistant.
            You are speaking with a caller who has dialed in to reach support.
            Be warm, professional, and helpful.
            Ask how you can assist them today."""
        )


async def entrypoint(ctx: agents.JobContext):
    """
    Entrypoint for inbound SIP calls.

    This function is called automatically when:
    1. An inbound call arrives at the Vobiz number
    2. Vobiz routes it to LiveKit SIP endpoint
    3. LiveKit dispatch rule matches and spawns this agent
    """
    logger.info(f"[OK] Starting voice assistant for room: {ctx.room.name}")

    # Get configuration from environment
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not deepgram_api_key:
        raise ValueError("DEEPGRAM_API_KEY not found in .env.local")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in .env.local")

    # Configure the agent session
    session = AgentSession(
        # Speech-to-Text: Deepgram Nova-3 (multilingual support)
        stt=deepgram.STT(
            model="nova-3",
            language="multi"  # Supports multiple languages
        ),

        # Large Language Model: OpenAI GPT-4o-mini
        llm=openai.LLM(
            model="gpt-4o-mini"
        ),

        # Text-to-Speech: OpenAI TTS-1 with Alloy voice
        tts=openai.TTS(
            model="tts-1",
            voice="alloy"  # Natural, balanced voice
        ),

        # Voice Activity Detection: Silero VAD
        vad=silero.VAD.load(),
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
        room_input_options=RoomInputOptions(
            # Don't close session when caller disconnects (allows reconnection)
            close_on_disconnect=False,
        ),
    )

    # Greet the caller when they connect
    # For inbound calls, the SIP participant is already in the room
    try:
        logger.info("[OK] Generating greeting for caller...")
        await session.generate_reply(
            instructions="Greet the caller warmly and professionally. Introduce yourself as a voice AI assistant and ask how you can help them today."
        )
    except RuntimeError as e:
        logger.warning(f"[!] Could not generate greeting (session may be closing): {e}")


if __name__ == "__main__":
    """
    Run the agent in 'start' mode to handle all inbound calls.

    Usage:
        uv run python agent_inbound.py start

    The agent will:
    - Connect to LiveKit cloud
    - Listen for rooms created by dispatch rules
    - Automatically join when an inbound call arrives
    - Greet the caller and start conversation
    """
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Agent name must match the dispatch rule configuration
            agent_name="voice-assistant",
        )
    )
