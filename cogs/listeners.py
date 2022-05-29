from re import T
import sys
import traceback
import time
import random

import discord
from discord.ext import commands

from ext.errors import InsufficientPrivilegeError

class ListenerCog(commands.Cog, command_attrs=dict(hidden=True)):

    hidden = True
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
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
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        elif message.guild.id == 681882711945641997:
            async with self.bot.conn.cursor('afk') as cur:
                await cur.execute("SELECT member_name FROM afk WHERE user_id=?", (message.author.id,))
                if cur:
                    await cur.execute("SELECT afk_time FROM afk WHERE user_id=?", (message.author.id,))
                    time_spent = int(time.time())-int(cur[0])
                    if time_spent < random.randint(20,30):
                        pass
                    else:
                        await cur.execute("DELETE FROM afk WHERE user_id=?", (message.author.id,))
                        try:
                            await message.author.edit(nick=f"{cur[0]}")
                        except:
                            pass
                        on_pat_staff = message.guild.get_role(726441123966484600)
                        try:
                            await message.author.add_roles(on_pat_staff)
                        except Exception as e:
                            print(e)
                        emoji = random.choice(['⚪', '🔴', '🟤', '🟣', '🟢', '🟡', '🟠', '🔵'])
                        em = discord.Embed(
                            description=f"{emoji} Welcome back, I removed your AFK!",
                            color=discord.Color.dark_gold()
                        )
                        await message.reply(embed = em)
            
                else:
                    if message.mentions:
                        for member in message.mentions:
                            await cur.execute("SELECT reason FROM afk WHERE user_id=?", (member.id,))
                            reason = cur[0]
                            if cur:
                                emoji = random.choice(['⚪', '🔴', '🟤', '🟣', '🟢', '🟡', '🟠', '🔵'])
                                await cur.execute("SELECT afk_time FROM afk WHERE user_id=?", (member.id,))
                                time_ = cur[0]
                                em = discord.Embed(
                                    description = f"{emoji} {member.mention} is AFK: {reason} (<t:{str(time_)}:R>)",
                                    color = discord.Color.dark_blue()
                                )
                                await message.reply(embed = em)
                                break
            await self.bot.conn.afk.commit()

async def setup(bot):
    await bot.add_cog(ListenerCog(bot))