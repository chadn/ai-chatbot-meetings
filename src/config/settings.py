"""
Configuration management for the AI Chatbot Meetings application.
"""
import os
import pytz
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import ast
import logging
import requests

# Load environment variables
load_dotenv()

# must be ones from https://platform.openai.com/docs/models that support "Function calling"
# for example, chatgpt-4o-latest does not support function calling
DEFAULT_OPENAI_MODELS_AVAILABLE = ["gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1", "o4-mini", "o3"]
# BEST VALUE: https://platform.openai.com/docs/models/gpt-4.1-mini
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_OPENAI_MAX_TOKENS = 1024
DEFAULT_OPENAI_TEMPERATURE = 0.0

DEFAULT_CALCOM_BASE_URL = "https://api.cal.com/v2"
DEFAULT_CALCOM_API_VERSION_SLOTS = "2024-09-04"
DEFAULT_CALCOM_API_VERSION_BOOKINGS = "2024-08-13"
DEFAULT_CALCOM_API_VERSION_EVENT_TYPES = "2024-06-14"
DEFAULT_CALCOM_LANGUAGE = "en"
DEFAULT_TIMEZONE = "America/Los_Angeles"

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DEBUG_MODE = False

@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str
    model_name: str = DEFAULT_OPENAI_MODEL
    models_available: list[str] = field(default_factory=lambda: DEFAULT_OPENAI_MODELS_AVAILABLE)
    max_tokens: int = DEFAULT_OPENAI_MAX_TOKENS
    temperature: float = DEFAULT_OPENAI_TEMPERATURE
    
    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Create OpenAI config from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        models_available = get_openai_models_available(api_key)
        return cls(
            api_key=api_key,
            models_available=models_available,
            model_name=validated_model_name(models_available),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", str(DEFAULT_OPENAI_MAX_TOKENS))),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", str(DEFAULT_OPENAI_TEMPERATURE)))
        )

@dataclass
class CalComConfig:
    """Cal.com API configuration."""
    api_key: str
    base_url: str = DEFAULT_CALCOM_BASE_URL
    timezone: str = DEFAULT_TIMEZONE
    cal_api_version_slots: str = DEFAULT_CALCOM_API_VERSION_SLOTS
    cal_api_version_bookings: str = DEFAULT_CALCOM_API_VERSION_BOOKINGS
    cal_api_version_event_types: str = DEFAULT_CALCOM_API_VERSION_EVENT_TYPES
    default_language: str = DEFAULT_CALCOM_LANGUAGE
    
    @classmethod
    def from_env(cls) -> "CalComConfig":
        """Create Cal.com config from environment variables."""
        api_key = os.getenv("CALCOM_API_KEY", "")
        timezone = os.getenv("DEFAULT_TIMEZONE", DEFAULT_TIMEZONE)
        # Validate timezone is a valid IANA timezone
        try:
            pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"DEFAULT_TIMEZONE must be a valid IANA timezone. Got: {timezone}")

        return cls(
            api_key=api_key,
            base_url=os.getenv("CALCOM_BASE_URL", DEFAULT_CALCOM_BASE_URL),
            timezone=timezone,
            default_language=os.getenv("CALCOM_LANGUAGE", DEFAULT_CALCOM_LANGUAGE),
            # TODO: is the next few lines needed? seemsredundant?
            cal_api_version_slots=DEFAULT_CALCOM_API_VERSION_SLOTS,
            cal_api_version_bookings=DEFAULT_CALCOM_API_VERSION_BOOKINGS,
            cal_api_version_event_types=DEFAULT_CALCOM_API_VERSION_EVENT_TYPES
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

def parse_models_env(var: str) -> list:
    # Accepts comma-separated or Python list string
    if not var:
        return []
    try:
        # Try to parse as Python list
        return ast.literal_eval(var)
    except Exception:
        # Fallback: split by comma
        return [m.strip() for m in var.split(",") if m.strip()]

def get_openai_models_available(openai_api_key: str) -> list:
    """Get the list of models available."""
    desired_models_available=parse_models_env(os.getenv("OPENAI_MODELS_AVAILABLE")) or DEFAULT_OPENAI_MODELS_AVAILABLE
    valid_models = get_all_valid_openai_models(openai_api_key)
    if len(valid_models) == 0:
        logging.warn(f"Could not validate OpenAI models, returning: {desired_models_available}")
        return desired_models_available
    models_available = []
    for model in desired_models_available:
        if model in valid_models:
            models_available.append(model)
        else:
            logging.warn(f"Model {model} is not valid. Skipping.")
    return models_available

def get_all_valid_openai_models(openai_api_key: str) -> list[str]:
    url = "https://api.openai.com/v1/models"
    headers = {
        "Authorization": f"Bearer {openai_api_key}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        valid_models = []
        for model in data["data"]:
            if model["owned_by"] == "system" and model["object"] == "model":
                    valid_models.append(model["id"])
        return valid_models
    except Exception as e:
        logging.warn(f"Error getting all OpenAI models: {e}")
        return []

def validated_model_name(models_available: list[str]) -> str:
    model_name = os.getenv("OPENAI_MODEL_NAME", DEFAULT_OPENAI_MODEL)
    if model_name not in models_available:
        if model_name != DEFAULT_OPENAI_MODEL:
            logging.warning(f"OPENAI_MODEL_NAME={model_name} must be one of current list of available models: {models_available}. Falling back to DEFAULT_OPENAI_MODEL={DEFAULT_OPENAI_MODEL}.")
            model_name = DEFAULT_OPENAI_MODEL
        else:
            logging.warning(f"OPENAI_MODEL_NAME={model_name} must be one of current list of available models: {models_available}. Falling back to first one in available list, {models_available[0]}.")
            model_name = models_available[0]
    return model_name
