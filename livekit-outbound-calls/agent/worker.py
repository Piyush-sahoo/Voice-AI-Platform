"""
LiveKit Voice Agent Worker.
Handles SIP calls with OpenAI Realtime API for voice interactions.
"""
import logging
import os
import json
import sys
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
from config import config


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
        from services.analysis_service import AnalysisService
        from database.connection import connect_to_database
        
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
        from services.webhook_service import WebhookService
        from database.models import CallRecord
        
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


async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the agent."""
    logger.info(f"Connecting to room: {ctx.room.name}")
    
    # Parse metadata
    phone_number = None
    call_id = None
    assistant_id = None
    sip_trunk_id = config.OUTBOUND_TRUNK_ID
    custom_instructions = None
    first_message = None
    voice_id = config.OPENAI_REALTIME_VOICE
    temperature = 0.8
    webhook_url = None
    
    try:
        if ctx.job.metadata:
            data = json.loads(ctx.job.metadata)
            phone_number = data.get("phone_number")
            call_id = data.get("call_id")
            assistant_id = data.get("assistant_id")
            sip_trunk_id = data.get("sip_trunk_id", config.OUTBOUND_TRUNK_ID)
            custom_instructions = data.get("instructions")
            first_message = data.get("first_message")
            voice_id = data.get("voice_id", config.OPENAI_REALTIME_VOICE)
            temperature = data.get("temperature", 0.8)
            webhook_url = data.get("webhook_url")
    except Exception:
        logger.warning("No valid JSON metadata found.")

    # Use room name as call_id if not provided
    if not call_id:
        call_id = ctx.room.name

    logger.info(f"Using OpenAI Realtime: voice={voice_id}, temp={temperature}")
    if assistant_id:
        logger.info(f"Using assistant: {assistant_id}")

    # Initialize session with assistant config
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice=voice_id,
            temperature=temperature,
        ),
    )

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    # Shutdown callback
    async def on_shutdown():
        """Handle cleanup when call ends."""
        try:
            current_date = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            
            # Save transcript locally
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            transcript_data = session.history.to_dict()
            transcript_file = os.path.join(logs_dir, f"transcript_{call_id}_{current_date}.json")
            with open(transcript_file, 'w') as f:
                json.dump(transcript_data, f, indent=2)
            logger.info(f"Transcript saved to {transcript_file}")
            
            # Update database
            await update_call_in_db(call_id, {
                "status": "completed",
                "ended_at": datetime.now(timezone.utc),
                "transcript": transcript_data,
                "transcript_url": transcript_file,
            })
            
            # Send webhook
            await send_webhook(call_id, "completed")
            
            # Run post-call analysis
            await run_post_call_analysis(call_id)
            
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
        ),
    )

    if phone_number:
        logger.info(f"Initiating outbound SIP call to {phone_number}...")
        try:
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=sip_trunk_id,
                    sip_call_to=phone_number,
                    participant_identity=f"sip_{phone_number}",
                    wait_until_answered=True,
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
            agent_name="outbound-caller", 
        )
    )


if __name__ == "__main__":
    run_agent()
