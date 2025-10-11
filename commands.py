import discord
from discord import app_commands
from guild_config import load_config, save_config, set_log_channel, set_mod_role, get_guild_config

class BlacklistCommands(app_commands.Group):
    def __init__(self, tree: app_commands.CommandTree, default_mod_role_id: int):
        super().__init__(name="blacklist", description="Blacklist management commands")
        self.tree = tree
        self.default_mod_role_id = default_mod_role_id

    @app_commands.command(name="setlogchannel", description="Sets the log channel for this guild only.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def set_log_channel_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_config()
        set_log_channel(config, interaction.guild_id, channel.id)
        await interaction.response.send_message(f"Log channel set to {channel.mention} for this guild.", ephemeral=True)

    @app_commands.command(name="setmodrole", description="Sets the moderator role for this guild only.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def set_mod_role_command(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        set_mod_role(config, interaction.guild_id, role.id)
        await interaction.response.send_message(f"Moderator role set to {role.mention} for this guild.", ephemeral=True)

    @app_commands.command(name="viewsettings", description="Displays the current guild's log channel and moderator role.")
    async def view_settings_command(self, interaction: discord.Interaction):
        config = load_config()
        guild_config = get_guild_config(config, interaction.guild_id)

        log_channel_id = guild_config.get("logChannelId")
        mod_role_id = guild_config.get("moderatorRoleId")

        log_channel_mention = f"<#{log_channel_id}>" if log_channel_id else "Not set"
        mod_role_mention = f"<@&{mod_role_id}>" if mod_role_id else f"Not set (default: <@&{self.default_mod_role_id}>)"

        embed = discord.Embed(
            title="Guild Settings",
            color=discord.Color.blue()
        )
        embed.add_field(name="Log Channel", value=log_channel_mention, inline=False)
        embed.add_field(name="Moderator Role", value=mod_role_mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup_commands(tree: app_commands.CommandTree, default_mod_role_id: int):
    tree.add_command(BlacklistCommands(tree, default_mod_role_id))
