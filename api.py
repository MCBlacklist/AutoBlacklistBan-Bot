import aiohttp
import asyncio

BLACKLIST_API_URL = "http://REDACTED/api/recent-blacklists"
UNBLACKLIST_API_URL = "http://REDACTED/api/recent-unblacklists"
MOJANG_SESSION_SERVER_URL = "https://sessionserver.mojang.com/session/minecraft/profile/"

async def fetch_json(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 404:
                # Return empty list for 404 instead of raising an error
                return []
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return []

async def get_recent_blacklists():
    async with aiohttp.ClientSession() as session:
        return await fetch_json(session, BLACKLIST_API_URL)

async def get_recent_unblacklists():
    async with aiohttp.ClientSession() as session:
        return await fetch_json(session, UNBLACKLIST_API_URL)

async def get_minecraft_username(uuid):
    async with aiohttp.ClientSession() as session:
        url = f"{MOJANG_SESSION_SERVER_URL}{uuid}"
        try:
            data = await fetch_json(session, url)
            return data.get("name")
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return None # UUID not found
            raise # Re-raise other errors



