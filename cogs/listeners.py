from __future__ import annotations

import random
import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands
from ext.errors import InsufficientPrivilegeError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ext.models import CodingBot


class ListenerCog(commands.Cog, command_attrs=dict(hidden=True)):

    hidden = True

    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context[CodingBot], error: Exception):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, InsufficientPrivilegeError):
            embed = discord.Embed(
                title='Insufficient Privilege',
                description=error.message,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        else:
            print('Ignoring exception in command {}:'.format(
                ctx.command
                ),
                file=sys.stderr
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        record = await self.bot.conn.select_record(
            'afk',
            table='afk',
            arguments=('afk_time',),
            where=['user_id'],
            values=(message.author.id,)
        )
        if record:
            record = record[0]
            time_spent = datetime.utcnow() - datetime.utcfromtimestamp(record.afk_time)
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
                    name = message.author.display_name.split(' ')[1:]
                    await message.author.edit(nick=" ".join(name))  # type: ignore
                except (discord.HTTPException, discord.Forbidden):
                    pass

                staff_role = message.guild.get_role(795145820210462771)
                if staff_role and staff_role in message.author.roles:  # type: ignore
                    on_pat_staff = message.guild.get_role(726441123966484600)
                    
                    if on_pat_staff:
                        try:
                            await message.author.add_roles(on_pat_staff)
                        except (discord.Forbidden, discord.HTTPException):
                            pass

                emoji = random.choice(('⚪', '🔴', '🟤', '🟣', '🟢', '🟡', '🟠', '🔵'))
                em = discord.Embed(
                    description=f"{emoji} Welcome back, I removed your AFK!",
                    color=discord.Color.dark_gold()
                )
                await message.reply(embed = em)


    @commands.Cog.listener('on_message')
    async def user_mentioned(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if message.mentions:
            for member in message.mentions:
                record = await self.bot.conn.select_record(
                    'afk',
                    table='afk',
                    arguments=('afk_time', 'reason'),
                    where=('user_id',),
                    values=(message.author.id,),
                )
                if record:
                    record = record[0]
                    emoji = random.choice(['⚪', '🔴', '🟤', '🟣', '🟢', '🟡', '🟠', '🔵'])
                    time_ = int(record.afk_time)
                    em = discord.Embed(
                        description = f"{emoji} {member.mention} is AFK: {record.reason} (<t:{time_}:R>)",
                        color = discord.Color.dark_blue()
                    )
                    await message.reply(embed = em)
                    break

async def setup(bot: CodingBot):
    await bot.add_cog(ListenerCog(bot))
