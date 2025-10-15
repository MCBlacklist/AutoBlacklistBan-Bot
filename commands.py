import discord
from discord.ext import commands
from discord import app_commands
from guild_config import load_config, set_log_channel, set_mod_role, get_guild_config
import logging

logger = logging.getLogger(__name__)

class BlacklistCommands(app_commands.Group):
    def __init__(self, tree: app_commands.CommandTree):
        super().__init__(name="blacklist", description="Blacklist management commands")
        self.tree = tree

    @app_commands.command(name="setlogchannel", description="Sets the log channel for this guild only.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def set_log_channel_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                "Only the server owner can use this command.", 
                ephemeral=True
            )
            
        config = load_config()
        set_log_channel(config, interaction.guild_id, channel.id)
        await interaction.response.send_message(f"Log channel set to {channel.mention} for this guild.", ephemeral=True)

    @app_commands.command(name="setmodrole", description="Sets the moderator role for this guild.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def set_mod_role_command(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                "Only the server owner can use this command.", 
                ephemeral=True
            )
            
        config = load_config()
        set_mod_role(config, interaction.guild_id, role.id)
        await interaction.response.send_message(
            f"Moderator role set to {role.mention} for this guild. "
            f"Users with this role can now manage blacklists.",
            ephemeral=True
        )

    @app_commands.command(name="viewsettings", description="Displays the current guild's log channel and moderator role.")
    async def view_settings_command(self, interaction: discord.Interaction):
        config = load_config()
        guild_config = get_guild_config(config, interaction.guild_id)

        log_channel_id = guild_config.get("logChannelId")
        mod_role_id = guild_config.get("moderatorRoleId")

        log_channel_mention = f"<#{log_channel_id}>" if log_channel_id else "Not set"
        mod_role_mention = f"<@&{mod_role_id}>" if mod_role_id else "Not set (only server owner can manage)"

        embed = discord.Embed(
            title="Guild Settings",
            description=f"**Server Owner:** {interaction.guild.owner.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Log Channel", value=log_channel_mention, inline=False)
        embed.add_field(name="Moderator Role", value=mod_role_mention, inline=False)
        
        if interaction.user == interaction.guild.owner:
            embed.set_footer(text="You can change these settings using /blacklist commands")
        else:
            embed.set_footer(text="Only the server owner can change these settings")

        await interaction.response.send_message(embed=embed, ephemeral=True)