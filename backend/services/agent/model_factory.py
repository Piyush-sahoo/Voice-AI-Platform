"""
Model factory for dynamically creating STT, LLM, and TTS instances.
Supports multiple providers for user-selectable voice AI configuration.
"""
import logging
import os
from typing import Any, Optional
from contextlib import contextmanager
from openai.types.beta.realtime.session import TurnDetection

logger = logging.getLogger("model-factory")

# Check which plugins are available
AVAILABLE_PLUGINS = {
    "openai": True,  # Always available (core)
    "deepgram": False,
    "elevenlabs": False,
    "anthropic": False,
    "cartesia": False,
    "google": False,
    "groq": False,
    "assemblyai": False,
}

# Try importing plugins to check availability
try:
    from livekit.plugins import deepgram
    AVAILABLE_PLUGINS["deepgram"] = True
except ImportError:
    pass

try:
    from livekit.plugins import elevenlabs
    AVAILABLE_PLUGINS["elevenlabs"] = True
except ImportError:
    pass

try:
    from livekit.plugins import anthropic
    AVAILABLE_PLUGINS["anthropic"] = True
except ImportError:
    pass

try:
    from livekit.plugins import cartesia
    AVAILABLE_PLUGINS["cartesia"] = True
except ImportError:
    pass

try:
    from livekit.plugins import google
    AVAILABLE_PLUGINS["google"] = True
except ImportError:
    pass


@contextmanager
def _scoped_env(env_updates: dict):
    """
    Temporarily apply environment variables for client construction only.
    This avoids process-global credential bleed across tenants.
    """
    old_values = {k: os.environ.get(k) for k in env_updates.keys()}
    try:
        for k, v in env_updates.items():
            if v:
                os.environ[k] = v
        yield
    finally:
        for k, old in old_values.items():
            if old is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = old


def _provider_env(api_keys: Optional[dict]) -> dict:
    if not api_keys:
        return {}
    return {
        "OPENAI_API_KEY": api_keys.get("openai"),
        "DEEPGRAM_API_KEY": api_keys.get("deepgram"),
        "GOOGLE_API_KEY": api_keys.get("google"),
        "ELEVENLABS_API_KEY": api_keys.get("elevenlabs"),
        "CARTESIA_API_KEY": api_keys.get("cartesia"),
        "ANTHROPIC_API_KEY": api_keys.get("anthropic"),
        "ASSEMBLYAI_API_KEY": api_keys.get("assemblyai"),
    }


def get_stt(voice_config: dict, api_keys: Optional[dict] = None) -> Any:
    """
    Create STT instance based on provider configuration.
    
    Supported providers: deepgram, openai, assemblyai
    """
    from livekit.plugins import openai
    
    provider = voice_config.get("stt_provider", "deepgram")
    model = voice_config.get("stt_model", "nova-2")
    language = voice_config.get("stt_language", "en")
    
    logger.info(f"Creating STT: provider={provider}, model={model}, language={language}")
    
    if provider == "openai":
        with _scoped_env(_provider_env(api_keys)):
            return openai.STT(model=model, language=language)
    
    elif provider == "deepgram" and AVAILABLE_PLUGINS["deepgram"]:
        from livekit.plugins import deepgram
        with _scoped_env(_provider_env(api_keys)):
            return deepgram.STT(model=model, language=language)
    
    elif provider == "assemblyai":
        # AssemblyAI requires API key
        logger.warning("AssemblyAI not yet fully implemented, falling back to OpenAI")
        return openai.STT(model="whisper-1", language=language)
    
    else:
        logger.warning(f"STT provider '{provider}' not available, falling back to OpenAI")
        return openai.STT(model="whisper-1", language=language)


def get_llm(voice_config: dict, api_keys: Optional[dict] = None) -> Any:
    """
    Create LLM instance based on provider configuration.
    
    Supported providers: openai, anthropic, google, groq
    """
    from livekit.plugins import openai
    
    provider = voice_config.get("llm_provider", "openai")
    model = voice_config.get("llm_model", "gpt-4o-mini")
    
    logger.info(f"Creating LLM: provider={provider}, model={model}")
    
    if provider == "openai":
        with _scoped_env(_provider_env(api_keys)):
            return openai.LLM(model=model)
    
    elif provider == "anthropic" and AVAILABLE_PLUGINS["anthropic"]:
        from livekit.plugins import anthropic
        with _scoped_env(_provider_env(api_keys)):
            return anthropic.LLM(model=model)
    
    elif provider == "google" and AVAILABLE_PLUGINS["google"]:
        from livekit.plugins import google
        with _scoped_env(_provider_env(api_keys)):
            return google.LLM(model=model)
    
    elif provider == "groq" and AVAILABLE_PLUGINS["groq"]:
        # Groq requires special handling
        logger.warning("Groq not yet fully implemented, falling back to OpenAI")
        return openai.LLM(model="gpt-4o-mini")
    
    else:
        logger.warning(f"LLM provider '{provider}' not available, falling back to OpenAI")
        return openai.LLM(model="gpt-4o-mini")


def get_tts(voice_config: dict, api_keys: Optional[dict] = None) -> Any:
    """
    Create TTS instance based on provider configuration.
    
    Supported providers: elevenlabs, openai, cartesia, deepgram
    """
    from livekit.plugins import openai
    
    provider = voice_config.get("tts_provider", "openai")
    model = voice_config.get("tts_model", "tts-1")
    voice_id = voice_config.get("voice_id", "alloy")
    
    logger.info(f"Creating TTS: provider={provider}, model={model}, voice={voice_id}")
    
    if provider == "openai":
        with _scoped_env(_provider_env(api_keys)):
            return openai.TTS(model=model, voice=voice_id)
    
    elif provider == "elevenlabs" and AVAILABLE_PLUGINS["elevenlabs"]:
        from livekit.plugins import elevenlabs
        with _scoped_env(_provider_env(api_keys)):
            return elevenlabs.TTS(model_id=model, voice=voice_id)
    
    elif provider == "cartesia" and AVAILABLE_PLUGINS["cartesia"]:
        from livekit.plugins import cartesia
        with _scoped_env(_provider_env(api_keys)):
            return cartesia.TTS(model=model, voice=voice_id)
    
    elif provider == "deepgram" and AVAILABLE_PLUGINS["deepgram"]:
        from livekit.plugins import deepgram
        with _scoped_env(_provider_env(api_keys)):
            return deepgram.TTS(model=model)
    
    else:
        logger.warning(f"TTS provider '{provider}' not available, falling back to OpenAI")
        return openai.TTS(model="tts-1", voice="alloy")


def get_realtime_model(voice_config: dict, api_keys: Optional[dict] = None) -> Any:
    """
    Create Realtime (speech-to-speech) model instance.
    
    Supported providers: openai, google
    """
    from livekit.plugins import openai
    
    provider = voice_config.get("realtime_provider", "openai")
    model = voice_config.get("realtime_model", "gpt-4o-realtime-preview")
    voice_id = voice_config.get("voice_id", "alloy")
    temperature = voice_config.get("temperature", 0.8)
    
    logger.info(f"Creating Realtime: provider={provider}, model={model}, voice={voice_id}")
    
    if provider == "openai":
        with _scoped_env(_provider_env(api_keys)):
            return openai.realtime.RealtimeModel(
                model=model,
                voice=voice_id,
                temperature=temperature,
                modalities=["text", "audio"],
                input_audio_transcription={"model": "whisper-1"},
                turn_detection=TurnDetection(
                    type="server_vad",
                    threshold=0.5,
                    prefix_padding_ms=300,
                    silence_duration_ms=500,
                    create_response=True,
                    interrupt_response=True,
                ),
            )
    
    elif provider == "google" and AVAILABLE_PLUGINS["google"]:
        from livekit.plugins import google
        with _scoped_env(_provider_env(api_keys)):
            return google.RealtimeModel(
                model=model,
                voice=voice_id,
            )
    
    else:
        logger.warning(f"Realtime provider '{provider}' not available, falling back to OpenAI")
        return openai.realtime.RealtimeModel(
            voice=voice_id,
            temperature=temperature,
        )


def get_available_providers() -> dict:
    """Return dictionary of available providers for frontend."""
    return {
        "stt": ["openai"] + ([p for p in ["deepgram", "assemblyai"] if AVAILABLE_PLUGINS.get(p)]),
        "llm": ["openai"] + ([p for p in ["anthropic", "google", "groq"] if AVAILABLE_PLUGINS.get(p)]),
        "tts": ["openai"] + ([p for p in ["elevenlabs", "cartesia", "deepgram"] if AVAILABLE_PLUGINS.get(p)]),
        "realtime": ["openai"] + ([p for p in ["google"] if AVAILABLE_PLUGINS.get(p)]),
    }
