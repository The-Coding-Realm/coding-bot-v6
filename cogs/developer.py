from __future__ import annotations

import os
import traceback

import discord
import ext.helpers as helpers
from discord.ext import commands
from typing import TYPE_CHECKING, Dict, List, Mapping

if TYPE_CHECKING:
    from ext.models import CodingBot
    from types import ModuleType


class Developer(commands.Cog, command_attrs=dict(hidden=True)):

    hidden = True
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot
        
    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context[CodingBot]):
        """
        Sync all the slash commands globally

        It is not meant to be used after every restart.

        Usage:
        ------
        `{prefix}sync`
        """
        await self.bot.tree.sync()
        await ctx.send("Finished syncing commands globally")

    @commands.command(name='load', aliases=['l'])
    @commands.is_owner()
    async def _load(self, ctx: commands.Context[CodingBot], cog_: str):
        try:
            await self.bot.load_extension(cog_)
            embed = discord.Embed(
                title=f'Successfully loaded extension: `{cog_}`',
                color=discord.Color.green()
            )
        except Exception as e:
            embed = discord.Embed(
                title=f'Failed to load extension: `{cog_}`',
                color=discord.Color.red()
            )
            embed.description = f'```py\n{traceback.format_exc()}\n```'
            
        await ctx.send(embed=embed)

    @commands.command(name='unload', aliases=['u'])
    @commands.is_owner()
    async def _unload(self, ctx: commands.Context[CodingBot], cog_: str):
        try:
            await self.bot.unload_extension(cog_)
            embed = discord.Embed(
                title=f'Successfully unloaded extension: `{cog_}`',
                color=discord.Color.green()
            )
        except Exception as e:
            embed = discord.Embed(
                title=f'Failed to unload extension: `{cog_}`',
                color=discord.Color.red()
            )
            embed.description = f'```py\n{traceback.format_exc()}\n```'
            
        await ctx.send(embed=embed)

    @commands.command(name='reload', aliases=['r'])
    @commands.is_owner()
    async def _reload(self, ctx: commands.Context[CodingBot], cog_: str):
        try:
            await self.bot.reload_extension(cog_)
            embed = discord.Embed(
                title=f'Successfully reloaded extension: `{cog_}`',
                color=discord.Color.green()
            )
        except Exception as e:
            embed = discord.Embed(
                title=f'Failed to reload extension: `{cog_}`',
                color=discord.Color.red()
            )
            embed.description = f'```py\n{traceback.format_exc()}\n```'
            
        await ctx.send(embed=embed)

    @commands.command(name='loadall', aliases=['la'])
    @commands.is_owner()
    async def _loadall(self, ctx: commands.Context[CodingBot]):
        data = os.listdir('./cogs')
        cogs: Dict[str, List[str]] = {
            'loaded': [],
            'not': []
        }
        for cog in data:
            if not cog.endswith('.py'):
                continue
            if f"cogs.{cog[:-3]}" in self.bot.extensions:
                continue
            try:
                await self.bot.load_extension(f'cogs.{cog[:-3]}')
                cogs['loaded'].append(f'cogs.{cog[:-3]}')
            except discord.DiscordException:
                cogs['not'].append(f'cogs.{cog[:-3]}')
        embed = discord.Embed(title='Load all cogs', description='\n'.join([
            ('\U00002705' if cog_ in cogs['loaded'] else '\U0000274c')
            + cog_ for cog_ in data if cog_.endswith('.py')]))
        await ctx.send(embed=embed)

    @commands.command(name='unloadall', aliases=['ua', 'uall'])
    @commands.is_owner()
    async def _unloadall(self, ctx: commands.Context[CodingBot]):
        cogs: Dict[str, List[str]] = {
            'unloaded': [],
            'not': []
        }
        processing: Mapping[str, ModuleType] = self.bot.extensions.copy()  # type: ignore
        for cog in processing:
            try:
                await self.bot.unload_extension(cog)
                cogs['unloaded'].append(cog)
            except discord.DiscordException:
                cogs['not'].append(cog)
        embed = discord.Embed(title='Unload all cogs', description='\n'.join([
            ('\U00002705' if cog_ in cogs['unloaded'] else '\U0000274c')
            + cog_ for cog_ in processing]))
        await ctx.send(embed=embed)

    @commands.command(name='reloadall', aliases=['ra', 'rall'])
    @commands.is_owner()
    async def _reloadall(self, ctx: commands.Context[CodingBot]):
        cogs: Dict[str, List[str]] = {
            'reloaded': [],
            'not': []
        }
        processing: Mapping[str, ModuleType] = self.bot.extensions.copy()  # type: ignore
        for cog in processing:
            try:
                await self.bot.reload_extension(cog)
                cogs['reloaded'].append(cog)
            except discord.DiscordException:
                cogs['not'].append(cog)
        embed = discord.Embed(title='Reload all cogs', description='\n'.join([
            ('\U00002705' if cog_ in cogs['reloaded'] else '\U0000274c')
            + f' `{cog_}`' for cog_ in processing
        ]))
        await ctx.send(embed=embed)


async def setup(bot: CodingBot):
    await bot.add_cog(Developer(bot))
