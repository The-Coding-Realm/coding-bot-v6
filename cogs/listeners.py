from __future__ import annotations

import re
import sys
import traceback
from datetime import datetime
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from ext.consts import TCR_STAFF_ROLE_ID
from ext.helpers import check_invite
from ext.errors import InsufficientPrivilegeError

if TYPE_CHECKING:
    from ext.models import CodingBot


class ListenerCog(commands.Cog, command_attrs=dict(hidden=True)):

    hidden = True
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot
        


    @commands.Cog.listener("on_message")
    async def afk_user_messaage(self, message: discord.Message):
        """
        Responsible for checking if a message was sent by an AFK user.
        If so, the bot will send a message to the channel informating that they are no longer AFK.
        It will also remove the [AFK] tag from the user's name.

        Parameters
        ----------
        message : discord.Message
            The message that was sent.
        """
        if message.author.bot or not message.guild:
            return
        record = self.bot.afk_cache.get(message.guild.id)
        if record:
            record = record.get(message.author.id)
            if record:
                _, time = record
                if (datetime.utcnow() - datetime.utcfromtimestamp(time)).seconds < 30:
                    return
                await self.bot.conn.delete_record(
                    'afk',
                    table='afk',
                    where=('user_id',),
                    values=(message.author.id,),
                )
                try:
                    if "[AFK]" in message.author.display_name:
                        name = message.author.display_name.split(' ')[1:]
                        # type: ignore 
                        await message.author.edit(nick=" ".join(name))
                except (discord.HTTPException, discord.Forbidden):
                    pass

                staff_role = message.guild.get_role(795145820210462771)
                if staff_role and staff_role in message.author.roles:  # type: ignore
                    on_pat_staff = message.guild.get_role(726441123966484600)
                    try:
                        await message.author.add_roles(on_pat_staff)
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                del self.bot.afk_cache[message.guild.id][message.author.id]
                em = discord.Embed(
                    description=f"{message.author.mention} Welcome back, I removed your AFK!",
                    color=discord.Color.dark_gold(),
                )
                await message.reply(embed=em)

    @commands.Cog.listener("on_message")
    async def user_mentioned(self, message: discord.Message):
        """
        Responsible for checking if an AFK user was mentioned in a message.
        If so, the bot will send a message to the channel informing that the user that was mentioned is AFK.

        Parameters
        ----------
        message : discord.Message
            The message that was sent.
        """
        if message.author.bot or not message.guild:
            return
        if message.mentions:
            for member in message.mentions:
                record = self.bot.afk_cache.get(message.guild.id)
                if record:
                    record = record.get(message.author.id)
                    if record:
                        reason, time_ = record
                        em = discord.Embed(
                            description=f"{member.mention} is AFK: {reason} (<t:{time_}:R>)",
                            color=discord.Color.dark_blue(),
                        )
                        await message.reply(embed=em)

    @commands.Cog.listener()
    async def on_message_edit(
        self, 
        before: discord.Message, 
        after: discord.Message
    ) -> None:
        """
        Responsible for checking if a message was edited.
        If so, the bot will check if message cache of bot has exceeded 200.
        If so, the bot will clear the cache.

        Parameters
        ----------
        message_before : discord.Message
            The message before the edit.
        msg : discord.Message
            The message after the edit.
        """
        if after.author.bot:
            return
        if len(self.bot.message_cache) > 200:
            self.bot.message_cache.clear()
        await self.bot.process_edit(before, after)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """
        Handles errors for commands during command invocation.
        Errors that are not handled by this function are printed to stderr.
        """
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, InsufficientPrivilegeError):
            embed = discord.Embed(
                title="Insufficient Privilege, ",
                description=error.message,
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Command on Cooldown",
                description=f"{ctx.author.mention} Please wait {error.retry_after:.2f} seconds before using this command again.",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed, ephemeral=True)
        else:
            print(
                "Ignoring exception in command {}:".format(ctx.command),
                file=sys.stderr,
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )

    @commands.Cog.listener('on_message')
    async def track_sent_message(self, message: discord.Message):
        """
        Responsible for tracking staff messages.
        """

        if message.author.bot or not message.guild:
            return

        values = [message.author.id, message.guild.id, 1, 1]
        columns = ['user_id', 'guild_id', 'message_count']

        columns.append(status := message.author.status.name)
        
        staff_role = message.guild.get_role(TCR_STAFF_ROLE_ID)
        if staff_role and staff_role in message.author.roles:  # type: ignore
            columns.append('is_staff')
            values.append(1)
        else:
            pass
            
        return await self.bot.conn.insert_record(
            'metrics',
            table='message_metric',
            columns=columns,
            values=values,
            extras=[f'ON CONFLICT (user_id, guild_id) DO UPDATE SET message_count = message_count + 1, {status} = {status} + 1'],
        )

    @commands.Cog.listener('on_message_delete')
    async def track_deleted_message(self, message: discord.Message):
        """
        Responsible for tracking user messages.
        """
        
        if message.author.bot or not message.guild:
            return
        
        values = [message.author.id, message.guild.id]

        columns = ['deleted_message_count = deleted_message_count + 1']

        await self.bot.conn.update_record(
            'metrics',
            table='message_metric',
            to_update=columns,
            where=['user_id', 'guild_id'],
            values=values,
        )

    @commands.Cog.listener('on_message_edit')
    async def invite_in_message(self, _: discord.Message, after: discord.Message):
        """
        Responsible for tracking member joins.
        """
        if after.author.bot or not after.guild:
            return
        perms = after.channel.permissions_for(after.author).manage_guild
        if (await check_invite(self.bot, after.content, after.channel)) and (not perms):
            invite_regex = "(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?"
            if re.search(invite_regex, after.content):
                await after.delete()
                return await after.channel.send("Please don't send invite links in this server!")
        
    @commands.Cog.listener('on_message')
    async def invite_in_message(self, message: discord.Message):
        """
        Responsible for tracking member joins.
        """
        if message.author.bot or not message.guild:
            return
        perms = message.channel.permissions_for(message.author).manage_guild
        if (await check_invite(self.bot, message.content, message.channel)) and (not perms):
            invite_regex = "(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?"
            if re.search(invite_regex, message.content): # `check_invite` already checks if there is an invite, why are we checking again?
                await message.delete()
                return await message.channel.send("Please don't send invite links in this server!")

    @commands.Cog.listener('on_message')
    async def repo_mention(self, message: discord.Message):
        if 'discord.py' in message.content and not message.author.bot:
            regex = re.search(r'Rapptz/discord.py(#\d+)?', message.content)
            if regex:
                base_link = "https://github.com/Rapptz/discord.py"
                group = regex.group(0)
                if '#' in group:
                    group = group.split('#')[1]
                    base_link += f"/pull/{group}"
                resp = await self.bot.session.get(base_link)
                if resp.ok:
                    await message.channel.send(base_link)



async def setup(bot: CodingBot):
    await bot.add_cog(ListenerCog(bot))
