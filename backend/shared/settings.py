"""
Configuration and environment variables loader.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")


class Config:
    """Application configuration from environment variables."""
    
    # LiveKit
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_REALTIME_VOICE = os.getenv("OPENAI_REALTIME_VOICE", "alloy")
    
    # Google/Gemini (for post-call analysis and Gemini Live)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Additional Voice AI Providers (optional)
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
    
    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "vobiz_calls")
    
    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    
    # Vobiz SIP (default, can be overridden by SIP configs)
    OUTBOUND_TRUNK_ID = os.getenv("OUTBOUND_TRUNK_ID", "ST_EobjZFLK23yB")
    
    # Server
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required = [
            ("LIVEKIT_URL", cls.LIVEKIT_URL),
            ("LIVEKIT_API_KEY", cls.LIVEKIT_API_KEY),
            ("LIVEKIT_API_SECRET", cls.LIVEKIT_API_SECRET),
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("MONGODB_URI", cls.MONGODB_URI),
        ]
        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return True


# Create singleton instance
config = Config()
