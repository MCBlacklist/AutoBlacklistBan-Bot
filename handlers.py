import discord
import logging
from discord import app_commands
from guild_config import load_config, save_config, get_guild_config

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_button_interaction(interaction: discord.Interaction, custom_id: str, default_mod_role_id: int):
    config = load_config()
    guild_id = interaction.guild_id
    guild_config = get_guild_config(config, guild_id)

    moderator_role_id = guild_config.get("moderatorRoleId") or default_mod_role_id
    member_roles = [role.id for role in interaction.user.roles]

    if moderator_role_id not in member_roles:
        await interaction.response.send_message(
            "> ❌ You don’t have permission to accept/reject this action in this server.",
            ephemeral=True
        )
        return

    # No nasty fails
    await interaction.response.defer(ephemeral=False)

    original_embed = interaction.message.embeds[0]
    new_embed = discord.Embed.from_dict(original_embed.to_dict())
    moderator_name = interaction.user.display_name
    
    try:
        # Get ID from the embed
        discord_id_field = next(field for field in original_embed.fields if field.name == "Offender ID → <@discord_id>")
        discord_id = int(discord_id_field.value.strip('<@>'))
        
        # Get the member object
        member = await interaction.guild.fetch_member(discord_id)
        
        if custom_id == "accept_ban":
            # Ban the user
            reason = f"Blacklist accepted by {moderator_name}"
            try:
                await member.ban(reason=reason, delete_message_days=7)  # Delete last 7 days of messages
                new_embed.title = "🚫 User Banned"
                new_embed.color = discord.Color.dark_red()
                new_embed.add_field(name="Decision", value=f"Banned by {moderator_name}", inline=False)
                new_embed.add_field(name="Reason", value=reason, inline=False)
                logger.info(f"Banned user {member} (ID: {member.id}) in guild {interaction.guild.name}")
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to ban members.", ephemeral=True)
                return
            except discord.HTTPException as e:
                await interaction.followup.send(f"❌ Failed to ban user: {e}", ephemeral=True)
                return
                
        elif custom_id == "reject_blacklist":
            new_embed.title = "🚫 Blacklist Rejected"
            new_embed.color = discord.Color.dark_grey()
            new_embed.add_field(name="Decision", value=f"Rejected by {moderator_name}", inline=False)
            logger.info(f"Blacklist rejected for user {member} (ID: {member.id}) in guild {interaction.guild.name}")
            
        elif custom_id == "accept_unban":
            # Unban the user
            reason = f"Unblacklist accepted by {moderator_name}"
            try:
                await interaction.guild.unban(member, reason=reason)
                new_embed.title = "✅ User Unbanned"
                new_embed.color = discord.Color.dark_green()
                new_embed.add_field(name="Decision", value=f"Unbanned by {moderator_name}", inline=False)
                new_embed.add_field(name="Reason", value=reason, inline=False)
                logger.info(f"Unbanned user {member} (ID: {member.id}) in guild {interaction.guild.name}")
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to unban members.", ephemeral=True)
                return
            except discord.HTTPException as e:
                await interaction.followup.send(f"❌ Failed to unban user: {e}", ephemeral=True)
                return
                
        elif custom_id == "reject_unblacklist":
            new_embed.title = "✅ Unblacklist Rejected"
            new_embed.color = discord.Color.dark_grey()
            new_embed.add_field(name="Decision", value=f"Rejected by {moderator_name}", inline=False)
            logger.info(f"Unblacklist rejected for user {member} (ID: {member.id}) in guild {interaction.guild.name}")

        await interaction.message.edit(embed=new_embed, view=None)

        action = {
            "accept_ban": "banned the user",
            "reject_blacklist": "rejected the blacklist",
            "accept_unban": "unbanned the user",
            "reject_unblacklist": "rejected the unblacklist"
        }.get(custom_id, "performed an action")
        
        await interaction.followup.send(f"{moderator_name} has {action}.")
        
    except discord.NotFound:
        await interaction.followup.send("❌ User not found in this server.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)
        logger.error(f"Error in handle_button_interaction: {e}")
    except Exception as e:
        await interaction.followup.send("❌ An unexpected error occurred.", ephemeral=True)
        logger.error(f"Unexpected error in handle_button_interaction: {e}", exc_info=True)


