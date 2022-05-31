from __future__ import annotations

import inspect
import os
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from ext.models import CodingBot

class General(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="source", aliases=["github", "code"])
    @commands.cooldown(1, 1, commands.BucketType.channel)
    async def _source(
        self, 
        ctx: commands.Context[CodingBot], 
        *, 
        command: str = None
    ) -> None:
        """
        Displays my full source code or for a specific command.
        To display the source code of a subcommand you can separate it by
        periods or spaces.

        Usage:
        ------
        `{prefix}source` *will send link to my source code*
        `{prefix}source [command]` *will send link to the source code of the command*
        `{prefix}source [command] [subcommand]` *will send link to the source code of the subcommand*
        """
        github = '<:githubwhite:981333869502554134>' # <:githubwhite:804344724621230091>
        embed = discord.Embed(title=f'{github} GitHub (Click Here) {github}')
        source_url = 'https://github.com/The-Coding-Realm/coding-bot-v6'
        branch = 'master'
        if command is None:
            embed.url = source_url
            return await ctx.send(embed=embed)

        if command == 'help':
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
            help_command = self.bot.get_command('help')
            if help_command:
                embed.description = help_command.help.format(prefix=ctx.prefix)
        else:
            obj = self.bot.get_command(command.replace('.', ' '))
            if obj is None:
                embed = discord.Embed(title="Error 404", description=f"Command `{command}` not found.")
                return await ctx.send(embed=embed)

            if obj.help:
                embed.description = obj.help.format(prefix=ctx.prefix)

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename
            
        

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith('discord'):
            # not a built-in command
            location = os.path.relpath(filename).replace('\\', '/')
        else:
            location = module.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'
            branch = 'master'

        final_url = (f'{source_url}/blob/{branch}/{location}#L{firstlineno}-L'
                     f'{firstlineno + len(lines) - 1}')
        embed.url = final_url
        await ctx.send(embed=embed)

async def setup(bot: CodingBot) -> None:
    await bot.add_cog(General(bot))