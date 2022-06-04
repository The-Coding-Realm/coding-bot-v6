from __future__ import annotations

import sys
import traceback
from datetime import datetime
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from ext.errors import InsufficientPrivilegeError

if TYPE_CHECKING:
    from ext.models import CodingBot


class ListenerCog(commands.Cog, command_attrs=dict(hidden=True)):

    hidden = True
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, 
        ctx: commands.Context[CodingBot], 
        error: Exception
    ) -> None:
        """
        Handles errors for commands during command invocation.
        Errors that are not handled by this function are printed to stderr.

        Parameters
        ----------
        ctx : commands.Context[CodingBot]
            The context for the command.
        error : Exception
            The exception that was raised.
        """
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, InsufficientPrivilegeError):
            embed = discord.Embed(
                title="Insufficient Privilege",
                description=error.message,
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed)
        else:
            print(
                "Ignoring exception in command {}:".format(ctx.command),
                file=sys.stderr,
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )

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
        record = await self.bot.conn.select_record(
            "afk",
            table="afk",
            arguments=["afk_time"],
            where=["user_id"],
            values=[message.author.id],
        )
        if record:
            record = record[0]
            time_spent = datetime.utcnow() - datetime.utcfromtimestamp(
                record.afk_time
            )
            if time_spent.total_seconds() < 30:
                pass
            else:
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
                em = discord.Embed(
                    description=f"{message.author.mentioned_in} Welcome back, I removed your AFK!",
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
                record = await self.bot.conn.select_record(
                    "afk",
                    table="afk",
                    arguments=["afk_time", "reason"],
                    where=["user_id"],
                    values=[message.author.id],
                )
                if record:
                    record = record[0]
                    time_ = int(record.afk_time)
                    em = discord.Embed(
                        description=f"{member.mention} is AFK: {record.reason} (<t:{time_}:R>)",
                        color=discord.Color.dark_blue(),
                    )
                    await message.reply(embed=em)
                    break

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


async def setup(bot: CodingBot):
    await bot.add_cog(ListenerCog(bot))
