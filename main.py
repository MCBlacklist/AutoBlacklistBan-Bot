import os
import sys
import asyncio
import logging
from typing import Dict, Any, Set, Optional
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from guild_config import load_config, save_config, get_guild_config, ConfigDict
from api import get_recent_blacklists, get_minecraft_username, close_session
from embeds import create_blacklist_embed, BlacklistButtons
from handlers import handle_button_interaction

# Import commands after bot is defined to avoid circular imports
from commands import BlacklistCommands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    logger.error("No DISCORD_TOKEN environment variable set!")
    sys.exit(1)

CONFIG_UPDATE_BATCH_SIZE = 5  # Number of config updates before saving

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class BlacklistBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.scheduler = AsyncIOScheduler()
        self.pending_config_updates: Dict[str, Dict] = {}
        self.config_update_counter = 0

    async def setup_hook(self) -> None:
        """Setup hook that runs when the bot starts."""
        # Register command group
        self.tree.add_command(BlacklistCommands(self.tree))
        
        # Sync commands with Discord
        await self.tree.sync()
        logger.info("Successfully synced application commands")
        
    async def close(self):
        """Cleanup when the bot is shutting down."""
        # Save any pending config changes
        await self.save_pending_config()
        # Close the HTTP session
        await close_session()
        # Stop the scheduler
        if self.scheduler.running:
            self.scheduler.shutdown()
        await super().close()
    
    async def save_pending_config(self) -> None:
        """Save any pending configuration changes."""
        if self.pending_config_updates:
            logger.info(f"Saving {len(self.pending_config_updates)} pending config updates...")
            config = load_config()
            for guild_id, guild_data in self.pending_config_updates.items():
                if guild_id in config:
                    config[guild_id].update(guild_data)
            save_config(config)
            self.pending_config_updates.clear()
            self.config_update_counter = 0

    def queue_config_update(self, guild_id: int, updates: Dict[str, Any]) -> None:
        """Queue configuration updates to be saved in batches."""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.pending_config_updates:
            self.pending_config_updates[guild_id_str] = {}
        self.pending_config_updates[guild_id_str].update(updates)
        self.config_update_counter += 1
        
        # Save if we've reached the batch size
        if self.config_update_counter >= CONFIG_UPDATE_BATCH_SIZE:
            asyncio.create_task(self.save_pending_config())

# Initialize bot instance
bot = BlacklistBot()

@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    bot.scheduler.start()
    logger.info("Scheduler started.")
    poll_apis.start()
    logger.info("API polling started.")

@bot.event
async def on_guild_join(guild: discord.Guild):
    """Event triggered when the bot joins a new guild."""
    logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
    config = load_config()
    get_guild_config(config, guild.id)
    save_config(config)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Handle all interactions, including button clicks and application commands."""
    try:
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id")
            if custom_id in ["accept_ban", "reject_blacklist", "accept_unban", "reject_unblacklist"]:
                await handle_button_interaction(interaction, custom_id)
    except Exception as e:
        logger.error(f"Error handling interaction: {e}", exc_info=True)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while processing your request.", 
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

@tasks.loop(minutes=1.0)
async def poll_apis():
    """Poll the blacklist and unblacklist APIs and process new entries."""
    try:
        config = load_config()
        
        # Get recent blacklists
        blacklists = await get_recent_blacklists()
        
        # Log new blacklists if any
        if blacklists:
            logger.info(f"Received {len(blacklists)} new blacklist(s) from API")
            for blacklist in blacklists:
                logger.info(
                    f"Blacklist - UUID: {blacklist.get('offender_uuid', 'N/A')}, "
                    f"Discord ID: {blacklist.get('offender_discord_id', 'N/A')}, "
                    f"Offense: {blacklist.get('offense_type', 'N/A')}"
                )
        
        # Process each guild
        tasks = []
        for guild_id, guild_data in config.items():
            tasks.append(process_guild_updates(guild_id, guild_data, blacklists, []))
        
        # Run guild updates concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors from guild updates
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in guild update: {result}", exc_info=result)
        
        # Save any pending config updates
        await bot.save_pending_config()
        
        logger.debug("Finished processing API updates")
        
    except Exception as e:
        logger.error(f"Error in poll_apis: {e}", exc_info=True)

async def process_guild_updates(
    guild_id: str, 
    guild_data: ConfigDict, 
    blacklists: list,
    _unused: list = None  # Keep for backward compatibility
) -> None:
    """Process updates for a single guild."""
    try:
        guild = bot.get_guild(int(guild_id))
        if not guild:
            logger.warning(f"Guild {guild_id} not found, skipping.")
            return

        log_channel_id = guild_data.get("logChannelId")
        if not log_channel_id:
            logger.warning(f"No log channel configured for guild {guild.name}, skipping.")
            return

        log_channel = guild.get_channel(int(log_channel_id))
        if not log_channel or not isinstance(log_channel, discord.TextChannel):
            logger.warning(f"Log channel {log_channel_id} not found in guild {guild.name}, skipping.")
            return

        # Process blacklists
        new_blacklist_ids = []
        for bl in blacklists:
            # Check if required fields exist
            if not isinstance(bl, dict) or not all(k in bl for k in ["offender_uuid", "offender_discord_id"]):
                logger.warning("Blacklist item missing required fields (offender_uuid, offender_discord_id)")
                continue

            if bl["offender_uuid"] not in guild_data.get("lastSeenBlacklistIds", []):
                new_blacklist_ids.append(bl["offender_uuid"])
                try:
                    username = await get_minecraft_username(bl["offender_uuid"])
                    embed = create_blacklist_embed(bl, username or "Unknown")
                    await log_channel.send(embed=embed, view=BlacklistButtons())
                    logger.info(f"Posted new blacklist to {guild.name} for {username or bl['offender_uuid']}")
                except Exception as e:
                    logger.error(f"Error processing blacklist: {e}")
        
        # Update config with new blacklist IDs
        if new_blacklist_ids:
            bot.queue_config_update(guild.id, {
                "lastSeenBlacklistIds": guild_data.get("lastSeenBlacklistIds", []) + new_blacklist_ids
            })
            
    except Exception as e:
        logger.error(f"Error processing guild {guild_id}: {e}", exc_info=True)

async def main():
    """Main entry point for the bot."""
    if not DISCORD_TOKEN:
        logger.error("No Discord token provided. Set the DISCORD_TOKEN environment variable.")
        return 1

    try:
        # Initialize the bot
        async with bot:
            # Start the bot
            await bot.start(DISCORD_TOKEN)
    except (discord.LoginFailure, discord.HTTPException) as e:
        logger.error(f"Failed to connect to Discord: {e}")
        return 1
    except discord.PrivilegedIntentsRequired as e:
        logger.error(f"Missing required intents: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
        return 1
    finally:
        if not bot.is_closed():
            await bot.close()
    
    return 0

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
# Made by RedstoneLayer with love!