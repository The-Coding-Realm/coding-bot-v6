from __future__ import annotations
from io import BytesIO

import os
import traceback

import discord
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
        """
        Load a cog

        Usage:
        ------
        `{prefix}load [cog]`
        """
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
        """
        Unload a cog

        Usage:
        ------
        `{prefix}unload [cog]`

        """
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
        """
        Reload a cog

        Usage:
        ------
        `{prefix}reload [cog]`
        """
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
        """
        Load all cogs

        Usage:
        ------
        `{prefix}loadall`

        """
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
        """
        Unload all cogs

        Usage:
        ------
        `{prefix}unloadall`

        """
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
        """
        Reload all cogs

        Usage:
        ------
        `{prefix}reloadall`
        
        """
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

    @commands.command(name='getusermetric', aliases=['gum'], hidden=True)
    @commands.is_owner()
    async def _getusermetric(self, ctx: commands.Context[CodingBot], member: discord.Member):
        """
        Get user metric

        Usage:
        ------
        `{prefix}getusermetric [member]`
        
        """
        member = member or ctx.author

        record = await self.bot.conn.select_record(
            'thanks',
            table='thanks_info',
            arguments=['thanks_count'],
            where=['guild_id', 'user_id'],
            values=[ctx.guild.id, member.id]
        )
        total_thank_count = record[0].thanks_count if record else 0
        revoked_thank_count = await self.bot.conn.select_record(
            'thanks',
            table='thanks_data',
            arguments=['count(*)'],
            where=['guild_id', 'user_id', 'thank_revoked'],
            values=[ctx.guild.id, member.id, 1]
        )
        revoked_thank_count = revoked_thank_count[0].count
        surviving_thank_count = total_thank_count - revoked_thank_count 

        message_metric = await self.bot.conn.select_record(
            'metrics',
            table='message_metric',
            arguments=['user_id', 'guild_id', 'message_count', 'deleted_message_count', 'offline', 'online', 'dnd', 'idle'],
            where=['user_id', 'guild_id'],
            values=[member.id, ctx.guild.id]
        )
        record = message_metric[0] if message_metric else None
        if record:
            formatted_message = f"""
            **__Message metrics__** For {member.mention}:
            \u3164 • **__Total message count__**:            {record.message_count}
            \u3164 • **__Deleted message count__**:          {record.deleted_message_count} (`{record.deleted_message_count / record.message_count * 100:.2f}%`)
            \u3164 • **__Actual message count__**:           {record.message_count - record.deleted_message_count} (`{(record.message_count - record.deleted_message_count) / record.message_count * 100:.2f}%`)
            \u3164 • **__Offline message count__**:          {record.offline} (`{record.offline / record.message_count * 100:.2f}%`)
            \u3164 • **__Online message count__**:           {record.online} (`{record.online / record.message_count * 100:.2f}%`)
            \u3164 • **__Dnd message count__**:              {record.dnd} (`{record.dnd / record.message_count * 100:.2f}%`)
            \u3164 • **__Idle message count__**:             {record.idle} (`{record.idle / record.message_count * 100:.2f}%`)
            """

        embed = discord.Embed(
            title=f'{member.name}#{member.discriminator} Detailed anaylysis',
            description=
            f'Total thanks this month: {total_thank_count}\n'
            f'Revoked thanks this month: {revoked_thank_count} (`{revoked_thank_count/total_thank_count*100 if total_thank_count > 0 else 0:.2f}%`)\n'
            f'Actual thanks this month: {surviving_thank_count} (`{surviving_thank_count/total_thank_count*100 if total_thank_count > 0 else 0:.2f}%`)'
            f'\n{formatted_message if record else ""}',
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f'Requested by {ctx.author}', )
        await ctx.send(embed=embed)




async def setup(bot: CodingBot):
    await bot.add_cog(Developer(bot))
