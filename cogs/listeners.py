from re import T
import sys
import traceback

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

async def setup(bot):
    await bot.add_cog(ListenerCog(bot))