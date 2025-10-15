import discord
def create_blacklist_embed(blacklist_data, username):
    embed = discord.Embed(
        title="🚫 New Blacklist Detected",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    
    # Add all fields from the blacklist data
    embed.add_field(name="Minecraft UUID", value=f"`{blacklist_data['offender_uuid']}`", inline=False)
    embed.add_field(name="Minecraft Username", value=username or "Unknown", inline=False)
    embed.add_field(name="Discord User", value=f"<@{blacklist_data['offender_discord_id']}>", inline=False)
    embed.add_field(name="Offense Type", value=blacklist_data.get('offense_type', 'N/A'), inline=True)
    embed.add_field(name="Ban Date", value=blacklist_data['ban_date'], inline=True)
    
    # Format ban duration if it exists
    if 'ban_duration' in blacklist_data and blacklist_data['ban_duration']:
        duration = int(blacklist_data['ban_duration'])
        if duration > 0:
            days = duration // 86400  # Convert seconds to days
            embed.add_field(name="Ban Duration", value=f"{days} days" if days > 1 else "Permanent", inline=True)
    
    return embed

def create_unblacklist_embed(event_data, username):
    embed = discord.Embed(
        title="✅ Unblacklist Detected",
        color=discord.Color.green()
    )
    embed.add_field(name="Offender UUID → username", value=f"{username} ({event_data['uuid']})", inline=False)
    embed.add_field(name="Offender ID → <@discord_id>", value=f"<@{event_data['discord_id']}>", inline=False)
    embed.add_field(name="Offense", value=event_data['offense'], inline=False)
    embed.add_field(name="Unban Date", value=event_data['unban_date'], inline=True)
    return embed

class BlacklistButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Accept & Ban", style=discord.ButtonStyle.green, custom_id="accept_ban")
    async def accept_ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red, custom_id="reject_blacklist")
    async def reject_blacklist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

class UnblacklistButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Accept & Unban", style=discord.ButtonStyle.green, custom_id="accept_unban")
    async def accept_unban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red, custom_id="reject_unblacklist")
    async def reject_unblacklist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


