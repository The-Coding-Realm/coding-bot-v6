from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands
import datetime

from ext.consts import (
    OFFICIAL_HELPER_ROLE_ID, 
    TCR_GUILD_ID, 
    HELP_BAN_ROLE_ID, 
    READ_HELP_RULES_ROLE_ID
)

if TYPE_CHECKING:
    from ext.models import CodingBot


class Helper(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            return False
        if ctx.guild.id != TCR_GUILD_ID:
            return False

        official_helper_role = ctx.guild.get_role(OFFICIAL_HELPER_ROLE_ID)

        if official_helper_role not in ctx.author.roles:
            return False

        return True

    @commands.hybrid_group(name="helper")
    async def helper(self, ctx: commands.Context[CodingBot]):
        """
        Help commands
        """
        await ctx.send_help(ctx.command)

    @helper.command(name="warn")
    async def help_warn(self, ctx, member: discord.Member, reason):
        await self.bot.conn.insert_record(
            'warnings',
            table='help_warns',
            columns=('guild_id', 'user_id', 'helper_id', 'reason', 'date'),
            values=(ctx.guild.id, member.id, ctx.author.id,
                    reason, ctx.message.created_at.timestamp())
        )
        await ctx.send(f'Help-warned {member.mention}')

    @helper.command(name="warnings")
    async def help_warnings(self, ctx, member: discord.Member):

        embed = discord.Embed(
            title=f"{member} Help warnings List", color=discord.Color.red())
        records = await self.bot.conn.select_record(
            'warnings',
            arguments=('reason', 'helper_id', 'date'),
            table='help_warns',
            where=('guild_id', 'user_id'),
            values=(ctx.guild.id, member.id),
            extras=['ORDER BY date DESC']
        )
        if not records:
            return await ctx.send(f'{member.mention} has no help-warnings.')

        for i, warning in enumerate(records, 1):
            moderator = ctx.guild.get_member(warning.moderator_id)
            if moderator:
                moderator = moderator.mention
            else:
                moderator = 'Unknown'
            embed.add_field(name="`{}.` Reason: {}".format(
                i, warning.reason), value=f"Issued by: {moderator} - <t:{int(warning.date)}:f>", inline=False)

        await ctx.send(embed=embed)

    @helper.command(name="clearwarning")
    async def help_clearwarning(self, ctx, member: discord.Member, index: int = None):
        target = member or ctx.author
        if index is None:
            await self.bot.conn.delete_record(
                'warnings',
                table='help_warns',
                where=('guild_id', 'user_id'),
                values=(ctx.guild.id, target.id)
            )
        else:
            records = await self.bot.conn.select_record(
                'warnings',
                arguments=('date',),
                table='help_warns',
                where=('guild_id', 'user_id'),
                values=(ctx.guild.id, target.id),
                extras=['ORDER BY date DESC']
            )

            if not records:
                return await ctx.send(f'{target.mention} has no warnings.')

            for i, sublist in enumerate(records, 1):
                if index == i:
                    await self.bot.conn.delete_record(
                        'warnings',
                        table='help_warns',
                        where=('guild_id', 'user_id', 'date'),
                        values=(ctx.guild.id, target.id, sublist.date)
                    )
                    break

        await ctx.reply(f'{target.mention}\'s warning was cleared.')

    @helper.command(name="help-ban")
    async def help_ban(self, ctx, member:discord.Member, reason):
        help_ban_role = ctx.guild.get_role(HELP_BAN_ROLE_ID)
        read_help_rules_role = ctx.guild.get_role(READ_HELP_RULES_ROLE_ID)
        if help_ban_role in member.roles:
            return await ctx.send(f'{member.mention} is already help-banned')

        if read_help_rules_role in member.roles:
            member.remove_roles(read_help_rules_role)
        if not help_ban_role in member.roles:
            member.add_roles(help_ban_role)

        await ctx.send(f'help-banned {member.mention} with reason: {reason}')
        try:
            await member.send(f"You have been help-banned with reason: {reason}")
        except discord.Forbidden:
            pass

    @helper.command(name="help-unban")
    async def help_unban(self, ctx, member: discord.Member):
        help_ban_role = ctx.guild.get_role(HELP_BAN_ROLE_ID)
        read_help_rules_role = ctx.guild.get_role(READ_HELP_RULES_ROLE_ID)
        if not help_ban_role in member.roles:
            return await ctx.send(f'{member.mention} is not help-banned')

        if not read_help_rules_role in member.roles:
            member.add_roles(read_help_rules_role)
        if help_ban_role in member.roles:
            member.remove_roles(help_ban_role)

        await ctx.send(f'help-unbanned {member.mention}')
        try:
            await member.send(f"You have been help-unbanned")
        except discord.Forbidden:
            pass

    @commands.hybrid_command(name="help-verify")
    async def help_verify(self, ctx, target: discord.Member):
        read_help_rules_role = ctx.guild.get_role(READ_HELP_RULES_ROLE_ID)
        if read_help_rules_role in target.roles:
            embed = discord.Embed(title="ERROR!", description=f"{target.mention} is already verified")
            embed.set_footer(text=f"Command executed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        else:
            embed = discord.Embed(title="Member verified", description=f"{target.mention} was successfully verified")
            embed.set_footer(text=f"Command executed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await target.add_roles(read_help_rules_role)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Helper(bot))
