import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any, List
from functools import wraps
import time
from aiohttp import ClientSession, ClientResponseError

# Constants
BLACKLIST_API_URL = "http://51.195.102.58/api/recent-blacklists"
UNBLACKLIST_API_URL = "http://51.195.102.58/api/recent-unblacklists"
MOJANG_SESSION_SERVER_URL = "https://sessionserver.mojang.com/session/minecraft/profile/"
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # second

# Configure logging
logger = logging.getLogger(__name__)

# Global session for connection pooling
_session = None

def get_session() -> ClientSession:
    """Get or create a global aiohttp session with connection pooling."""
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        _session = aiohttp.ClientSession(timeout=timeout, raise_for_status=True)
    return _session

async def close_session():
    """Close the global aiohttp session."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None

def retry_on_failure(func):
    """Decorator to retry a function on failure with exponential backoff."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
        logger.error(f"All {MAX_RETRIES} attempts failed for {func.__name__}")
        if last_error:
            raise last_error
        raise Exception("Unknown error occurred")
    return wrapper

@retry_on_failure
async def fetch_json(url: str, session: Optional[ClientSession] = None) -> Any:
    """Fetch JSON from a URL with error handling and retries."""
    session = session or get_session()
    try:
        async with session.get(url) as response:
            if response.status == 404:
                return []
            return await response.json()
    except ClientResponseError as e:
        if e.status == 404:
            return []
        logger.error(f"HTTP error {e.status} fetching {url}: {e}")
        raise
    except asyncio.TimeoutError:
        logger.error(f"Timeout while fetching {url}")
        raise
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        raise

@retry_on_failure
async def get_recent_blacklists() -> List[Dict]:
    """Get recent blacklists with retry logic.
    
    Returns:
        List[Dict]: List of blacklist entries with offender_uuid and offender_discord_id
    """
    session = get_session()
    try:
        # Get recent blacklists with all fields
        return await fetch_json(BLACKLIST_API_URL, session) or []
    except Exception as e:
        logger.error(f"Failed to fetch blacklists: {e}")
        return []

@retry_on_failure
async def get_recent_unblacklists() -> List[Dict]:
    """Get recent unblacklists with retry logic.
    
    Returns:
        List[Dict]: List of unblacklist entries with offender_uuid and offender_discord_id
    """
    session = get_session()
    try:
        params = {
            'fields': 'offender_uuid,offender_discord_id',
            'limit': 50
        }
        return await fetch_json(f"{UNBLACKLIST_API_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}", session) or []
    except Exception as e:
        logger.error(f"Failed to fetch unblacklists: {e}")
        return []

@retry_on_failure
async def get_minecraft_username(uuid: str) -> Optional[str]:
    """Get Minecraft username from UUID with retry logic."""
    if not uuid:
        return None
        
    session = get_session()
    url = f"{MOJANG_SESSION_SERVER_URL}{uuid}"
    try:
        data = await fetch_json(url, session)
        return data.get("name") if data else None
    except ClientResponseError as e:
        if e.status == 404:
            logger.debug(f"Minecraft UUID {uuid} not found")
            return None
        logger.error(f"Error fetching Minecraft username for {uuid}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching Minecraft username: {e}")
        return None

import atexit
atexit.register(lambda: asyncio.get_event_loop().run_until_complete(close_session()))