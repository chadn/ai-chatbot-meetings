from datetime import datetime
from dateutil import parser
import pytz
import logging

# Get logger for this module
logger = logging.getLogger(__name__)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def dbg_important(msg: str, plain_str: str = '') -> None:
    """Log important debug information."""
    full_msg = color_msg(bcolors.OKCYAN, msg, plain_str)
    logger.info(full_msg)

def success(msg: str, plain_str: str = '') -> None:
    """Log success information."""
    full_msg = f"{msg}{': ' + plain_str if plain_str else ''}"
    logger.info(full_msg)

def warn(msg: str, plain_str: str = '') -> None:
    """Log warning information."""
    full_msg = f"{msg}{': ' + plain_str if plain_str else ''}"
    logger.warning(full_msg)

def error(msg: str, plain_str: str = '') -> None:
    """Log error information."""
    full_msg = f"{msg}{': ' + plain_str if plain_str else ''}"
    logger.error(full_msg)

def color_msg(color: str, msg: str, plain_str: str = '') -> None:
    """Legacy function - use logging functions instead."""
    # TODO: replace with https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    plain_str = f": {plain_str}" if plain_str else ''
    return f"{color}{msg}{bcolors.ENDC}{plain_str}"


def convert_to_timezone(dt_str: str, timezone: str) -> datetime:
    """Convert ISO datetime string to the given timezone"""
    # Handle 'Z' UTC timezone indicator
    dt_str = dt_str.replace('Z', '+00:00')
    # Parse the datetime string
    dt = datetime.fromisoformat(dt_str)
    
    # If it's timezone naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    
    # Convert to user timezone if available
    if timezone:
        try:
            user_tz = pytz.timezone(timezone)
            dt = dt.astimezone(user_tz)
        except (pytz.exceptions.UnknownTimeZoneError, AttributeError):
            # If timezone is invalid, keep as is
            pass

    print(f"Converted {dt_str} to user timezone {timezone}: {dt.isoformat()}")
    return dt


def convert_local_to_utc(time_str: str, timezone: str) -> str:
    """
    Convert a local time string to UTC format with Z suffix.

    Args:
        time_str: Time string in ISO format (e.g., "2025-05-28T14:30:00")
        timezone: IANA timezone name (e.g., "America/Los_Angeles")

    Returns:
        UTC time string with Z suffix (e.g., "2025-05-28T21:30:00Z")
    """
    time_str = time_str.strip()

    if time_str.endswith('Z'):
        return time_str

    try:
        local_dt = parser.isoparse(time_str)

        if local_dt.tzinfo is None and timezone:
            user_tz = pytz.timezone(timezone)
            local_dt = user_tz.localize(local_dt)

        utc_dt = local_dt.astimezone(pytz.UTC)
        utc_time_str = utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"Converted local time {local_dt.isoformat()} to UTC: {utc_time_str}")
        return utc_time_str

    except Exception as e:
        print(f"Time conversion error: {e}. Returning original string.")
        return time_str

