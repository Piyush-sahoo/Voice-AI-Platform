"""
LiveKit Voice Agent Worker.
Handles SIP calls with OpenAI Realtime API for voice interactions.
"""
import logging
import os
import json
import sys
import httpx
from datetime import datetime, timezone

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from livekit import agents, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, metrics, MetricsCollectedEvent
from livekit.plugins import openai, noise_cancellation

# Load environment variables
load_dotenv(".env.local")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

from livekit.agents import function_tool, RunContext

# Import config
from shared.settings import config


class OutboundAssistant(Agent):
    """AI agent for outbound calls with dynamic tools."""
    
    def __init__(self, custom_instructions: str = None, tools: list = None) -> None:
        default_instructions = """
        You are a helpful and professional voice assistant calling from Vobiz.
        
        Key behaviors:
        1. Introduce yourself clearly when the user answers.
        2. Be concise and respect the user's time.
        3. If asked, explain you are an AI assistant helping with a test call.
        """
        
        self._custom_tools = tools or []
        
        super().__init__(
            instructions=custom_instructions or default_instructions
        )
    
    @function_tool()
    async def get_current_time(self, context: RunContext) -> str:
        """Get the current date and time."""
        now = datetime.now(timezone.utc)
        return f"The current time is {now.strftime('%I:%M %p')} on {now.strftime('%B %d, %Y')}"
    
    @function_tool()
    async def end_call(self, context: RunContext) -> str:
        """End the current call when the user wants to hang up or says goodbye."""
        return "Ending the call now. Goodbye!"


async def start_recording(ctx: agents.JobContext, phone_number: str = None, call_id: str = None):
    """Start audio recording to S3 bucket."""
    if not all([config.AWS_ACCESS_KEY_ID, config.AWS_SECRET_ACCESS_KEY, config.AWS_BUCKET_NAME]):
        logger.warning("AWS credentials not configured. Skipping recording.")
        return None, None
    
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        phone_suffix = phone_number.replace("+", "") if phone_number else "unknown"
        filepath = f"recordings/{call_id or ctx.room.name}_{phone_suffix}_{timestamp}.ogg"
        
        logger.info(f"Starting audio recording to s3://{config.AWS_BUCKET_NAME}/{filepath}")
        
        egress_req = api.RoomCompositeEgressRequest(
            room_name=ctx.room.name,
            audio_only=True,
            file_outputs=[
                api.EncodedFileOutput(
                    file_type=api.EncodedFileType.OGG,
                    filepath=filepath,
                    s3=api.S3Upload(
                        bucket=config.AWS_BUCKET_NAME,
                        region=config.AWS_REGION,
                        access_key=config.AWS_ACCESS_KEY_ID,
                        secret=config.AWS_SECRET_ACCESS_KEY,
                    ),
                )
            ],
        )
        
        lkapi = api.LiveKitAPI()
        egress_info = await lkapi.egress.start_room_composite_egress(egress_req)
        await lkapi.aclose()
        
        logger.info(f"Recording started! Egress ID: {egress_info.egress_id}")
        return egress_info.egress_id, f"s3://{config.AWS_BUCKET_NAME}/{filepath}"
        
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        return None, None


async def update_call_in_db(call_id: str, updates: dict):
    """Update call record in MongoDB."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        if not config.MONGODB_URI:
            return
        
        client = AsyncIOMotorClient(config.MONGODB_URI)
        db = client[config.MONGODB_DB_NAME]
        await db.calls.update_one({"call_id": call_id}, {"$set": updates})
        client.close()
        
    except Exception as e:
        logger.error(f"Failed to update call in DB: {e}")


async def run_post_call_analysis(call_id: str):
    """Run post-call analysis using Gemini."""
    try:
        from services.analytics.analysis_service import AnalysisService
        from shared.database.connection import connect_to_database
        
        if config.MONGODB_URI:
            await connect_to_database(config.MONGODB_URI, config.MONGODB_DB_NAME)
            analysis = await AnalysisService.analyze_call(call_id)
            if analysis:
                logger.info(f"Analysis complete: success={analysis.success}, sentiment={analysis.sentiment}")
    except Exception as e:
        logger.error(f"Post-call analysis failed: {e}")


async def send_webhook(call_id: str, event: str):
    """Send webhook notification."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from services.analytics.webhook_service import WebhookService
        from shared.database.models import CallRecord
        
        if not config.MONGODB_URI:
            return
        
        client = AsyncIOMotorClient(config.MONGODB_URI)
        db = client[config.MONGODB_DB_NAME]
        doc = await db.calls.find_one({"call_id": call_id})
        client.close()
        
        if doc and doc.get("webhook_url"):
            call = CallRecord.from_dict(doc)
            if event == "answered":
                await WebhookService.send_answered(call)
            elif event == "completed":
                await WebhookService.send_completed(call)
            elif event == "failed":
                await WebhookService.send_failed(call)
                
    except Exception as e:
        logger.error(f"Webhook failed: {e}")


async def get_inbound_assistant_config(room_name: str) -> dict:
    """
    Fetch assistant config for inbound calls.
    Looks up the phone number from the room name and gets the assigned assistant's prompts.
    
    Returns dict with:
      - system_prompt: The assistant's instructions
      - first_message: The greeting to say when answering
      - assistant_id: The assistant ID for tracking
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        if not config.MONGODB_URI:
            logger.warning("No MongoDB URI - using default prompts")
            return {}
        
        client = AsyncIOMotorClient(config.MONGODB_URI)
        db = client[config.MONGODB_DB_NAME]
        
        # Find inbound phone numbers that might match this room
        # The dispatch rule creates rooms with prefix "call-" or "inbound-"
        # We need to find which phone number this call came in on
        
        # Debug: Log all inbound numbers
        all_inbound = await db.phone_numbers.find({"direction": "inbound"}).to_list(10)
        logger.info(f"[INBOUND] All inbound numbers in DB: {len(all_inbound)}")
        for num in all_inbound:
            logger.info(f"[INBOUND]   -> {num.get('number')} | assistant_id={num.get('assistant_id')} | is_active={num.get('is_active')}")
        
        # For now, get the first active inbound number's assistant
        # (In production, you'd extract the called number from SIP headers)
        phone_doc = await db.phone_numbers.find_one({
            "direction": "inbound",
            "is_active": True,
            "assistant_id": {"$exists": True, "$ne": None, "$ne": ""}
        })
        
        if not phone_doc:
            logger.warning("No inbound phone number with assistant found")
            client.close()
            return {}
        
        assistant_id = phone_doc.get("assistant_id")
        inbound_number = phone_doc.get("number", "unknown")
        logger.info(f"[INBOUND] Found phone {inbound_number} -> assistant {assistant_id}")
        
        # Fetch the assistant's configuration
        assistant_doc = await db.assistants.find_one({"assistant_id": assistant_id})
        client.close()
        
        if not assistant_doc:
            logger.warning(f"Assistant {assistant_id} not found in DB")
            return {"assistant_id": assistant_id}
        
        # Extract prompts from assistant
        result = {
            "assistant_id": assistant_id,
            "assistant_name": assistant_doc.get("name", "Assistant"),
            "system_prompt": assistant_doc.get("system_prompt", ""),
            "first_message": assistant_doc.get("first_message", ""),
            "inbound_number": inbound_number,
        }
        
        # Also check voice_config for any custom settings
        voice_config = assistant_doc.get("voice", {})
        if voice_config:
            result["voice_config"] = voice_config
        
        logger.info(f"[INBOUND] Loaded assistant '{result['assistant_name']}' for inbound call")
        logger.info(f"[INBOUND] >>> payload of result = '{result}' for inbound call")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get inbound assistant config: {e}")
        return {}

def update_voice_config(metadata_dict: dict, is_inbound: bool, inbound_config: dict) -> dict:
    # Voice configuration (user-selectable models)
    #DEFAULT
    voice_config = {
        "mode": "realtime",  # realtime or pipeline
        "voice_id": config.OPENAI_REALTIME_VOICE,
        "temperature": 0.8,
        # Realtime mode
        "realtime_provider": "openai",
        "realtime_model": "gpt-4o-realtime-preview",
        # Pipeline mode (STT → LLM → TTS)
        "stt_provider": "deepgram",
        "stt_model": "nova-2",
        "stt_language": "en",
        "llm_provider": "openai",
        "llm_model": "gpt-4o-mini",
        "tts_provider": "openai",
        "tts_model": "tts-1",
    }

    if is_inbound and inbound_config: # inbound
        voice_config.update(inbound_config.get("voice_config", {}))
    else:   # outbound
        if metadata_dict:
            temperature = metadata_dict.get("temperature", 0.8)
            if "voice" in metadata_dict:
                voice_config.update(metadata_dict.get("voice", {}))
            
            voice_config["temperature"] = temperature

    logger.info(f" >>> Updated voice_config in entry point => voice_config = {voice_config}")

    return voice_config


async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the agent."""
    logger.info(f"Connecting to room: {ctx.room.name}")
    
    # Import model factory
    from services.agent.model_factory import get_stt, get_llm, get_tts, get_realtime_model

    # PART-1: METADATA CREATION AND PARSING

    # Parse metadata
    phone_number = None
    call_id = None
    assistant_id = None
    sip_trunk_id = config.OUTBOUND_TRUNK_ID
    custom_instructions = None
    first_message = None
    webhook_url = None

    inbound_config = None
    data = {}

    try:
        if ctx.job.metadata:
            data = json.loads(ctx.job.metadata)
            phone_number = data.get("phone_number")
            call_id = data.get("call_id")
            assistant_id = data.get("assistant_id")
            sip_trunk_id = data.get("sip_trunk_id", config.OUTBOUND_TRUNK_ID)
            custom_instructions = data.get("instructions")
            first_message = data.get("first_message")
            webhook_url = data.get("webhook_url")
            
    except Exception:
        logger.warning("No valid JSON metadata found.")

    # PART-2: DETECTING THE TYPE OF CALL (INBOUND VS OUTBOUND)
    # Use room name as call_id if not provided
    if not call_id:
        call_id = ctx.room.name
    
    # Inbound: room name starts with "inbound-"
    # Outbound: has phone_number in metadata
    if ctx.room.name.startswith("inbound-"):
        is_inbound = True
    elif phone_number:
        is_inbound = False
    else:
        # Fallback for other room names (e.g. "call-") without phone number -> Inbound
        is_inbound = True
    
    if is_inbound:
        logger.info(f"[INBOUND CALL] Room: {ctx.room.name}")
        # Fetch the assistant config for this inbound call
        inbound_config = await get_inbound_assistant_config(ctx.room.name)
        if not inbound_config:
            inbound_config = {}
    else:
        logger.info(f"[OUTBOUND CALL] To: {phone_number} (Room: {ctx.room.name})")

    # PART-3: UPDATING THE VOICE CONFIG FOR BOTH INBOUND AND OUTBOUND
    voice_config = update_voice_config(data, is_inbound, inbound_config)

    # PART-4: CREATE SESSION BASED ON MODE

    mode = voice_config.get("mode", "realtime")
    logger.info(f"Creating agent session: mode={mode}")
    
    if mode == "pipeline":
        # Pipeline mode: STT → LLM → TTS (more flexible)
        logger.info(f"Pipeline: >>> STT={voice_config.get('stt_provider')}, LLM={voice_config.get('llm_provider')}, TTS={voice_config.get('tts_provider')}")
        session = AgentSession(
            stt=get_stt(voice_config),
            llm=get_llm(voice_config),
            tts=get_tts(voice_config),
        )
    else:
        # Realtime mode: Speech-to-Speech (lowest latency)
        logger.info(f"Realtime: >>> provider={voice_config.get('realtime_provider')}, voice={voice_config.get('voice_id')}")
        session = AgentSession(
            llm=get_realtime_model(voice_config),
        )

    if assistant_id:
        logger.info(f"Using assistant: {assistant_id}")

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)
        


    # --- Manual Transcript Handling ---
    # Since RealtimeModel doesn't automatically populate session.history in this version
    # and AgentSession attributes vary, we use a robust local buffer.
    transcript_messages = []
    
    # 1. Capture Transcriptions from Room (Standard LiveKit STT)
    # This works for any invalid transcription events published to the room
    @ctx.room.on("transcription_received")
    def _on_transcription_received(ev):
        # ev is TranscriptionReceivedEvent
        # It contains a list of segments.
        for seg in ev.segments:
            if not seg.final:
                continue # Only capture final segments
            
            # Determine role based on participant
            role = "user"
            # If the participant is the agent itself, it's assistant
            if ev.participant and ev.participant.identity == ctx.agent.identity:
                role = "assistant"
            elif ev.participant is None: # Sometimes null for system/agent
                role = "assistant"
                
            transcript_messages.append({"role": role, "content": seg.text})
            logger.info(f"Transcript ({role}): {seg.text}")


    # Shutdown callback
    async def on_shutdown():
        """Handle cleanup when call ends."""
        try:
            # Get transcript data - try multiple sources
            # Priority: 1) Local buffer (room events), 2) session.conversation_history, 3) session.chat_ctx
            transcript_data = transcript_messages  # Start with our local buffer
            
            # If local buffer is empty, try to get from session
            if not transcript_data:
                # Try conversation_history (newer API)
                try:
                    if hasattr(session, 'conversation_history') and session.conversation_history:
                        logger.info("Using session.conversation_history for transcript")
                        for msg in session.conversation_history:
                            role = getattr(msg, 'role', 'user')
                            content = getattr(msg, 'content', str(msg))
                            if isinstance(content, list):
                                content = ' '.join([str(c) for c in content])
                            transcript_data.append({"role": role, "content": content})
                except Exception as e:
                    logger.debug(f"conversation_history not available: {e}")
            
            # Fallback: try chat_ctx.messages
            if not transcript_data:
                try:
                    if hasattr(session, 'chat_ctx') and hasattr(session.chat_ctx, 'messages'):
                        logger.info("Using session.chat_ctx.messages for transcript")
                        for msg in session.chat_ctx.messages:
                            role = getattr(msg, 'role', 'user')
                            content = getattr(msg, 'content', str(msg))
                            if isinstance(content, list):
                                content = ' '.join([str(c) for c in content])
                            transcript_data.append({"role": role, "content": content})
                except Exception as e:
                    logger.debug(f"chat_ctx.messages not available: {e}")
            
            logger.info(f"Call {call_id} ended. Captured {len(transcript_data)} transcript segments.")
            
            # Update database with transcript (no local file storage for container scalability)
            # CallRecord.transcript expects List[Dict], not {"messages": [...]}
            await update_call_in_db(call_id, {
                "status": "completed",
                "ended_at": datetime.now(timezone.utc),
                "transcript": transcript_data,  # Direct list, not wrapped in dict
            })
            
            # Send webhook
            await send_webhook(call_id, "completed")
            
            # Trigger post-call analysis via Analytics Service (direct call to dedicated service)
            try:
                # Call Analytics Service directly (not via Gateway) for proper microservice separation
                API_URL = "http://analytics:8001"  # Analytics container
                INTERNAL_KEY = os.getenv("INTERNAL_API_KEY", "vobiz_internal_secret_key_123")
                
                start_time = datetime.now()
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{API_URL}/calls/{call_id}/analyze",  # Analytics Service endpoint
                        timeout=2.0,
                        headers={"X-API-Key": INTERNAL_KEY}
                    )
                logger.info(f"Triggered analysis for {call_id} (took {(datetime.now() - start_time).total_seconds()}s)")
            except Exception as exc:
                logger.warning(f"Failed to trigger analysis: {exc}")
            
            # Log usage
            summary = usage_collector.get_summary()
            logger.info(f"Usage Summary: {summary}")
            
        except Exception as e:
            logger.error(f"Shutdown callback failed: {e}")

    ctx.add_shutdown_callback(on_shutdown)

    # Start session
    await session.start(
        room=ctx.room,
        agent=OutboundAssistant(custom_instructions),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
            close_on_disconnect=False,  # Keep session alive for proper cleanup
        ),
    )

    if is_inbound:
        # ========== INBOUND CALL ==========
        # Caller is already in the room - greet them with dynamic prompts
        logger.info("[INBOUND] Caller connected, initialising prompts and starting conversation")
        
        try:
            
            # Get prompts from assistant config, with fallbacks

            inbound_system_prompt = inbound_config.get("system_prompt", "")
            inbound_first_message = inbound_config.get("first_message", "")
            inbound_assistant_id = inbound_config.get("assistant_id", "")
            
            # Use custom instructions if set in metadata, else use assistant's system prompt
            effective_instructions = custom_instructions or inbound_system_prompt or """
                You are a helpful customer service assistant.
                Be polite, professional, and assist the caller with their needs.
            """
            
            # Use first_message from metadata, then from assistant, then default
            effective_greeting = first_message or inbound_first_message or "Hello! Thank you for calling. How can I assist you today?"
            
            logger.info(f"[INBOUND] Using assistant: {inbound_assistant_id or 'default'}")
            logger.info(f"[INBOUND] First message: {effective_greeting[:50]}...")
            
            # Update call status with assistant info
            await update_call_in_db(call_id, {
                "status": "answered",
                "answered_at": datetime.now(timezone.utc),
                "direction": "inbound",
                "assistant_id": inbound_assistant_id,
            })
            
            # Generate greeting for the caller using the assistant's configured prompts
            await session.generate_reply(
                instructions=f"{effective_instructions}\n\nGreet the caller warmly and professionally. Say: {effective_greeting}"
            )
            logger.info("[INBOUND] Greeting sent, conversation started")
            
        except Exception as e:
            logger.error(f"[INBOUND] Error greeting caller: {e}")
    
    elif phone_number:
        logger.info(f"Initiating outbound SIP call to {phone_number}...")
        try:
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=sip_trunk_id,
                    sip_call_to=phone_number,
                    participant_identity=f"sip_{phone_number}",
                    wait_until_answered=False,  # Don't block - let the call connect async
                )
            )
            logger.info("Call answered! Agent is now listening.")
            
            # Update status to answered
            await update_call_in_db(call_id, {
                "status": "answered",
                "answered_at": datetime.now(timezone.utc),
            })
            
            # Send answered webhook
            await send_webhook(call_id, "answered")
            
            # If first_message is set, have agent speak first
            if first_message:
                logger.info(f"Agent speaking first message...")
                await session.generate_reply(instructions=f"Say exactly: {first_message}")
            
            # Start recording
            egress_id, recording_url = await start_recording(ctx, phone_number, call_id)
            if egress_id:
                await update_call_in_db(call_id, {
                    "egress_id": egress_id,
                    "recording_url": recording_url,
                })
            
        except Exception as e:
            logger.error(f"Failed to place outbound call: {e}")
            await update_call_in_db(call_id, {
                "status": "failed",
                "metadata.failure_reason": str(e),
            })
            await send_webhook(call_id, "failed")
            ctx.shutdown()
    else:
        logger.info("No phone number in metadata. Treating as inbound/web call.")
        await session.generate_reply(instructions="Greet the user.")


def run_agent():
    """Run the agent worker."""
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="voice-assistant", 
        )
    )


if __name__ == "__main__":
    run_agent()
