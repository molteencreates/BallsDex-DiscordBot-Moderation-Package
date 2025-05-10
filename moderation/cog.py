import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings = {}

    # Role hierarchy checker
    def has_higher_role(self, guild: discord.Guild, actor: discord.Member, target: discord.Member) -> bool:
        return actor.top_role > target.top_role and guild.me.top_role > target.top_role

    # Kick
    
    @app_commands.command(name="kick", description="Kick a user from the server.")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("You don't have permission to kick members.", ephemeral=True)

        if not self.has_higher_role(interaction.guild, interaction.user, member):
            return await interaction.response.send_message("You can't kick this member due to role hierarchy.", ephemeral=True)

        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} was kicked. Reason: {reason}")

    # Ban
    
    @app_commands.command(name="ban", description="Ban a user from the server.")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)

        if not self.has_higher_role(interaction.guild, interaction.user, member):
            return await interaction.response.send_message("You can't ban this member due to role hierarchy.", ephemeral=True)

        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} was banned. Reason: {reason}")

    # Unban
    
    @app_commands.command(name="unban", description="Unban a user by tag (e.g. Name#1234).")
    async def unban(self, interaction: discord.Interaction, user_tag: str):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("You don't have permission to unban members.", ephemeral=True)

        name, discrim = user_tag.split("#")
        bans = await interaction.guild.bans()
        for ban in bans:
            if (ban.user.name, ban.user.discriminator) == (name, discrim):
                await interaction.guild.unban(ban.user)
                return await interaction.response.send_message(f"{ban.user.mention} has been unbanned.")
        await interaction.response.send_message("User not found in ban list.")

    # Purge
    
    @app_commands.command(name="purge", description="Purge/Clear messages in the channel.")
    async def clear(self, interaction: discord.Interaction, amount: int = 5):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("You don't have permission to manage messages.", ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)

    # Mute
    
    @app_commands.command(name="mute", description="Mute a user.")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)

        if not self.has_higher_role(interaction.guild, interaction.user, member):
            return await interaction.response.send_message("You can't mute this member due to role hierarchy.", ephemeral=True)

        muted_role = get(interaction.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await interaction.guild.create_role(name="Muted")
            for channel in interaction.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)

        await member.add_roles(muted_role, reason=reason)
        await interaction.response.send_message(f"{member.mention} has been muted. Reason: {reason}")

    # Unmute
    
    @app_commands.command(name="unmute", description="Unmute a user.")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)

        muted_role = get(interaction.guild.roles, name="Muted")
        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role)
            await interaction.response.send_message(f"{member.mention} has been unmuted.")
        else:
            await interaction.response.send_message("User is not muted.")

    # warn
    
    @app_commands.command(name="warn", description="Warn a user.")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("You don't have permission to warn users.", ephemeral=True)

        if not self.has_higher_role(interaction.guild, interaction.user, member):
            return await interaction.response.send_message("You can't warn this member due to role hierarchy.", ephemeral=True)

        uid = member.id
        self.warnings.setdefault(uid, []).append(reason)
        await interaction.response.send_message(f"{member.mention} has been warned. Reason: {reason}")

    # warns list
    
    @app_commands.command(name="warnings", description="List warnings for a user.")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        uid = member.id
        warns = self.warnings.get(uid, [])
        if warns:
            msg = "\n".join(f"{i+1}. {w}" for i, w in enumerate(warns))
            await interaction.response.send_message(f"Warnings for {member.mention}:\n{msg}")
        else:
            await interaction.response.send_message(f"{member.mention} has no warnings.")

    # slowmode
    
    @app_commands.command(name="slowmode", description="Set slowmode in this channel.")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("You don't have permission to set slowmode.", ephemeral=True)

        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"Slowmode set to {seconds} seconds.")

    # lock 
    
    @app_commands.command(name="lock", description="Lock this channel.")
    async def lock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("You don't have permission to lock channels.", ephemeral=True)

        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("Channel locked.")

    # unlock
    
    @app_commands.command(name="unlock", description="Unlock this channel.")
    async def unlock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("You don't have permission to unlock channels.", ephemeral=True)

        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("Channel unlocked.")

    # nickname
    
    @app_commands.command(name="nickname", description="Change a user's nickname.")
    async def nickname(self, interaction: discord.Interaction, member: discord.Member, nickname: str):
        if not interaction.user.guild_permissions.manage_nicknames:
            return await interaction.response.send_message("You don't have permission to change nicknames.", ephemeral=True)

        if not self.has_higher_role(interaction.guild, interaction.user, member):
            return await interaction.response.send_message("You can't change this member's nickname due to role hierarchy.", ephemeral=True)

        await member.edit(nick=nickname)
        await interaction.response.send_message(f"{member.mention}'s nickname changed to: {nickname}")



