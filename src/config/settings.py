"""
Configuration management for the AI Chatbot Meetings application.
"""
import os
import pytz
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import re
# Load environment variables
load_dotenv()


# must be ones from https://platform.openai.com/docs/models that support "Function calling"
# for example, chatgpt-4o-latest does not support function calling
OPENAI_MODELS_AVAILABLE = ["gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1", "o4-mini", "o3"]
# BEST VALUE: https://platform.openai.com/docs/models/gpt-4.1-mini
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_OPENAI_MAX_TOKENS = 1024
DEFAULT_OPENAI_TEMPERATURE = 0.0

DEFAULT_CALCOM_BASE_URL = "https://api.cal.com/v2"
DEFAULT_CALCOM_USERNAME = "chadn"
DEFAULT_CALCOM_EVENT_TYPE_ID = 2520314
DEFAULT_CALCOM_API_VERSION_SLOTS = "2024-09-04"
DEFAULT_CALCOM_API_VERSION_BOOKINGS = "2024-08-13"
DEFAULT_CALCOM_LANGUAGE = "en"
DEFAULT_TIMEZONE = "America/Los_Angeles"

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DEBUG_MODE = False

@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str
    model_name: str = DEFAULT_OPENAI_MODEL
    max_tokens: int = DEFAULT_OPENAI_MAX_TOKENS
    temperature: float = DEFAULT_OPENAI_TEMPERATURE
    
    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Create OpenAI config from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        
        model_name = os.getenv("OPENAI_MODEL_NAME", DEFAULT_OPENAI_MODEL)
        if model_name not in OPENAI_MODELS_AVAILABLE:
            raise ValueError(f"OPENAI_MODEL_NAME must be one of {OPENAI_MODELS_AVAILABLE}, got: {model_name}")
        
        return cls(
            api_key=api_key,
            model_name=model_name,
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", str(DEFAULT_OPENAI_MAX_TOKENS))),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", str(DEFAULT_OPENAI_TEMPERATURE)))
        )

@dataclass
class CalComConfig:
    """Cal.com API configuration."""
    api_key: str
    base_url: str = DEFAULT_CALCOM_BASE_URL
    username: str = DEFAULT_CALCOM_USERNAME
    event_type_id: int = DEFAULT_CALCOM_EVENT_TYPE_ID
    timezone: str = DEFAULT_TIMEZONE
    cal_api_version_slots: str = DEFAULT_CALCOM_API_VERSION_SLOTS
    cal_api_version_bookings: str = DEFAULT_CALCOM_API_VERSION_BOOKINGS
    default_language: str = DEFAULT_CALCOM_LANGUAGE
    
    @classmethod
    def from_env(cls) -> "CalComConfig":
        """Create Cal.com config from environment variables."""
        api_key = os.getenv("CALCOM_API_KEY", "")
        
        # Details in https://github.com/calcom/cal.com/blob/main/packages/lib/slugify.ts
        username = os.getenv("CALCOM_USERNAME", DEFAULT_CALCOM_USERNAME)
        # Validate username follows Cal.com requirements
        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            raise ValueError(f"CALCOM_USERNAME must contain only letters, numbers, periods, underscores, and hyphens. Got: {username}")
        
        timezone = os.getenv("DEFAULT_TIMEZONE", DEFAULT_TIMEZONE)
        # Validate timezone is a valid IANA timezone
        try:
            pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"DEFAULT_TIMEZONE must be a valid IANA timezone. Got: {timezone}")

        return cls(
            api_key=api_key,
            username=username,
            base_url=os.getenv("CALCOM_BASE_URL", DEFAULT_CALCOM_BASE_URL),
            event_type_id=int(os.getenv("CALCOM_BOOKING_EVENT_TYPE_ID", str(DEFAULT_CALCOM_EVENT_TYPE_ID))),
            timezone=timezone,
            default_language=os.getenv("CALCOM_LANGUAGE", DEFAULT_CALCOM_LANGUAGE),
            cal_api_version_slots=DEFAULT_CALCOM_API_VERSION_SLOTS,
            cal_api_version_bookings=DEFAULT_CALCOM_API_VERSION_BOOKINGS,
        )

@dataclass
class AppConfig:
    """Main application configuration."""
    openai: OpenAIConfig
    calcom: CalComConfig
    log_level: str = DEFAULT_LOG_LEVEL
    debug_mode: bool = DEFAULT_DEBUG_MODE
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create app config from environment variables."""
        return cls(
            openai=OpenAIConfig.from_env(),
            calcom=CalComConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            debug_mode=os.getenv("DEBUG_MODE", str(DEFAULT_DEBUG_MODE)).lower() == "true"
        )

# Global configuration instance
_config: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config

def reload_config() -> AppConfig:
    """Reload configuration from environment variables."""
    global _config
    _config = AppConfig.from_env()
    return _config
