import discord
def create_blacklist_embed(event_data, username):
    embed = discord.Embed(
        title="🚫 New Blacklist Detected",
        color=discord.Color.red()
    )
    embed.add_field(name="Offender UUID → username", value=f"{username} ({event_data['uuid']})", inline=False)
    embed.add_field(name="Offender ID → <@discord_id>", value=f"<@{event_data['discord_id']}>", inline=False)
    embed.add_field(name="Offense", value=event_data['offense'], inline=False)
    embed.add_field(name="Ban Date", value=event_data['ban_date'], inline=True)
    embed.add_field(name="Ban Duration", value=event_data['ban_duration'], inline=True)
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


