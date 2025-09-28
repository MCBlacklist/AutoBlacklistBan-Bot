import os
import asyncio
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from guild_config import load_config, save_config, get_guild_config
from api import get_recent_blacklists, get_recent_unblacklists, get_minecraft_username
from embeds import create_blacklist_embed, create_unblacklist_embed, BlacklistButtons, UnblacklistButtons
from commands import setup_commands
from handlers import handle_button_interaction

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEFAULT_STAFF = int(os.getenv("DEFAULT_STAFF"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()
    print("synced slash commands.")
    scheduler.start()
    print("scheduler started.")
    poll_apis.start()

@bot.event
async def on_guild_join(guild):
    print(f"Joined guild: {guild.name} (ID: {guild.id})")
    # Config for all srvrs
    config = load_config()
    get_guild_config(config, guild.id)
    save_config(config)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] in ["accept_ban", "reject_blacklist", "accept_unban", "reject_unblacklist"]:
            await handle_button_interaction(interaction, interaction.data["custom_id"], DEFAULT_STAFF)
    await bot.process_commands(interaction)

@tasks.loop(minutes=1)
async def poll_apis():
    print("Requesting API")
    config = load_config()

    blacklists = await get_recent_blacklists()
    unblacklists = await get_recent_unblacklists()

    for guild_id, guild_data in config.items():
        guild = bot.get_guild(int(guild_id))
        if not guild:
            print(f"Guild {guild_id} not found, skipping.")
            continue

        log_channel_id = guild_data.get("logChannelId")
        if not log_channel_id:
            print(f"No log channel configured for guild {guild.name}, skipping.")
            continue

        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            print(f"Log channel {log_channel_id} not found in guild {guild.name}, skipping.")
            continue

        new_blacklist_ids = []
        for bl in blacklists:
            if bl["id"] not in guild_data["lastSeenBlacklistIds"]:
                new_blacklist_ids.append(bl["id"])
                username = await get_minecraft_username(bl["uuid"])
                embed = create_blacklist_embed(bl, username or bl["uuid"])
                await log_channel.send(embed=embed, view=BlacklistButtons())
                print(f"Posted new blacklist to {guild.name}")
        if new_blacklist_ids:
            guild_data["lastSeenBlacklistIds"].extend(new_blacklist_ids)
            save_config(config)

        new_unblacklist_ids = []
        for unbl in unblacklists:
            if unbl["id"] not in guild_data["lastSeenUnblacklistIds"]:
                new_unblacklist_ids.append(unbl["id"])
                username = await get_minecraft_username(unbl["uuid"])
                embed = create_unblacklist_embed(unbl, username or unbl["uuid"])
                await log_channel.send(embed=embed, view=UnblacklistButtons())
                print(f"Posted new unblacklist to {guild.name}")
        if new_unblacklist_ids:
            guild_data["lastSeenUnblacklistIds"].extend(new_unblacklist_ids)
            save_config(config)

async def main():
    await setup_commands(bot.tree, DEFAULT_STAFF)
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
# Made by RedstoneLayer with love!