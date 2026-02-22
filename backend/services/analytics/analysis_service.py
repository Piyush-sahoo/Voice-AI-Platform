"""
Post-call analysis service using Google Gemini.
"""
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google import genai

from shared.database.models import CallRecord, CallAnalysis
from shared.database.connection import get_database
from shared.settings import config

logger = logging.getLogger("analysis_service")


class AnalysisService:
    """Service for post-call analysis using Gemini."""
    
    ANALYSIS_PROMPT = """Analyze the following call transcript and provide a structured analysis.

TRANSCRIPT:
{transcript}

CALL CONTEXT:
- Phone Number: {phone_number}
- Duration: {duration} seconds
- Custom Instructions: {instructions}

Analyze this call and respond in JSON format:
{{
    "success": true/false,
    "sentiment": "positive/neutral/negative",
    "summary": "2-3 sentence summary of the conversation",
    "key_topics": ["topic1", "topic2"],
    "action_items": ["action1", "action2"]
}}

Respond ONLY with the JSON, no other text."""

    @staticmethod
    async def analyze_call(call_id: str) -> Optional[CallAnalysis]:
        """
        Analyze a completed call using Gemini.
        """
        if not config.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not configured, skipping analysis")
            return None
        
        db = get_database()
        
        doc = await db.calls.find_one({"call_id": call_id})
        if not doc:
            logger.error(f"Call not found: {call_id}")
            return None
        
        call = CallRecord.from_dict(doc)
        
        if not call.transcript:
            logger.warning(f"No transcript available for call {call_id}")
            return None
        
        try:
            # Create Gemini client (new SDK)
            client = genai.Client(api_key=config.GOOGLE_API_KEY)

            transcript_text = AnalysisService._format_transcript(call.transcript)
            
            prompt = AnalysisService.ANALYSIS_PROMPT.format(
                transcript=transcript_text,
                phone_number=call.phone_number,
                duration=call.duration_seconds,
                instructions=call.instructions or "No specific instructions",
            )
            
            logger.info(f"Analyzing call {call_id} with Gemini...")
            
            response = await client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
            )
            
            analysis_data = AnalysisService._parse_response(response.text)
            
            if analysis_data:
                analysis = CallAnalysis(
                    success=analysis_data.get("success", False),
                    sentiment=analysis_data.get("sentiment", "neutral"),
                    summary=analysis_data.get("summary", ""),
                    key_topics=analysis_data.get("key_topics", []),
                    action_items=analysis_data.get("action_items", []),
                    analyzed_at=datetime.now(timezone.utc),
                )
                
                await db.calls.update_one(
                    {"call_id": call_id},
                    {"$set": {"analysis": analysis.model_dump()}},
                )
                
                logger.info(f"Analysis complete for call {call_id}: success={analysis.success}")
                return analysis
            else:
                logger.error(f"Failed to parse Gemini response for call {call_id}")
                return None
                
        except Exception as e:
            logger.error(f"Analysis failed for call {call_id}: {e}")
            return None
    
    @staticmethod
    def _format_transcript(transcript: List[Dict[str, Any]]) -> str:
        lines = []
        for item in transcript:
            role = item.get("role", "unknown")
            content = item.get("content", "")
            
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = " ".join(text_parts)
            
            if content:
                speaker = "Agent" if role == "assistant" else "Customer"
                lines.append(f"{speaker}: {content}")
        
        return "\n".join(lines) if lines else "No conversation content available"
    
    @staticmethod
    def _parse_response(response_text: str) -> Optional[Dict[str, Any]]:
        try:
            text = response_text.strip()
            
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            return json.loads(text.strip())
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response_text}")
            return None