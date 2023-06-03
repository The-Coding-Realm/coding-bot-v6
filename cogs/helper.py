from __future__ import annotations

import asyncio
import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional

import discord
import humanize
from discord.ext import commands
from ext.consts import (HELP_BAN_ROLE_ID, OFFICIAL_HELPER_ROLE_ID,
                        READ_HELP_RULES_ROLE_ID, TCR_GUILD_ID)
from ext.ui.view import ConfirmButton

if TYPE_CHECKING:
    from ext.models import CodingBot


class Helper(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context[CodingBot]) -> bool:
        """
        Restricts the use of the cog to the official helper role

        Parameters
        ----------
        ctx : commands.Context[CodingBot]
            The context of the command
        
        Returns
        -------
        bool
            Whether the user has the required role
        
        Raises
        ------
        commands.CheckFailure
            If the user doesn't have the required role
        
        """
        if isinstance(ctx.channel, discord.DMChannel):
            return False
        if ctx.guild.id != TCR_GUILD_ID:
            return False

        official_helper_role = ctx.guild.get_role(OFFICIAL_HELPER_ROLE_ID)

        if official_helper_role not in ctx.author.roles:
            return False
        return True

    async def capture_evidence(self, ctx: commands.Context[CodingBot]) -> Optional[discord.Attachment]:
        """
        Captures the evidence for some moderation action taken against a member

        Parameters
        ----------
        ctx : commands.Context[CodingBot]
            The context of the command
        
        Returns
        -------
        Optional[discord.Attachment]
            The evidence that was captured
        
        """
        view = ConfirmButton(ctx)
        view.message = await ctx.author.send(f'Do you want to provide an evidence for your action?', view=view)
        view_touched = not (await view.wait())
        evidence_byts = None
        if view_touched:
            if view.confirmed:
                initial_mess = await ctx.author.send("Please send the evidence in the form of an attachment.")
                try:
                    wait_mess = await self.bot.wait_for(
                        'message', check=lambda m: m.author == ctx.author and m.channel == initial_mess.channel and m.attachments and not m.guild, timeout=60
                    )
                except asyncio.TimeoutError:
                    await initial_mess.delete()
                    await ctx.author.send("You didn't send any evidence in time. Proceeding with the ban without evidence.")
                else:
                    evidence_byts = await wait_mess.attachments[0].read()
        return evidence_byts

    async def log(
        self,
        *,
        action: str,
        undo: bool = False,
        member: discord.Member,
        helper: discord.Member,
        reason: Optional[str] = None,
        duration: Optional[datetime.timedelta] = None,
        **kwargs: Any,
    ) -> None:
        """
        A function that logs all moderation commands executed

        Parameters
        ----------
        action : str
            The action that was performed
        moderator : discord.Member
            The moderator who performed the action
        member : discord.Member
            The member who was affected by the action
        undo : bool
            Whether the action was undone
        reason : Optional[str]
            The reason for the action
        duration : Optional[datetime.timedelta]
            The duration of the action
        """
        definition = {
            'ban': {
                'action': 'banned from help channels',
                'undo_action': 'unbanned from help channels',
                'color': discord.Color.red(),
                'icon': ':hammer:',
                'undo_icon': ':unlock:'
            },
            'mute': {
                'action': 'muted from help channels',
                'undo_action': 'unmuted from help channels',
                'color': discord.Color.light_grey(),
                'icon': ':mute:',
                'undo_icon': ':loud_sound:'},
            'warn': {
                'action': 'warned',
                'undo_action': f"removed warning (`{kwargs.get('warning') or 'removed all warnings'}`)",
                'icon': ':warning:',
                'undo_icon': ':flag_white:',
                'color': discord.Color.yellow()
            }
        }

        action_info = definition.get(
            action, ValueError(f"Invalid action: {action}"))
        if isinstance(action_info, ValueError):
            raise action_info

        undo_action = action_info.get('undo_action')

        if undo and isinstance(undo_action, ValueError):
            raise undo_action

        action_string = action_info['action'] if not undo else action_info['undo_action']
        icon = action_info['icon'] if not undo else action_info['undo_icon']
        color = discord.Color.green() if undo else action_info.get('color')

        embed = discord.Embed(color=color, timestamp=discord.utils.utcnow())

        embed.description = "{} **Action:** {}\n**Reason:** {}\n".format(
            icon, action_string.title(), reason)
        if duration:
            embed.description += "**Duration:** {}\n".format(
                humanize.naturaldelta(duration, minimum_unit='seconds'))
        file = None
        if evidence := kwargs.get('evidence'):
            embed.description += "\n**Evidence provided below:**"
            buffer = BytesIO(evidence)
            buffer.seek(0)
            file = discord.File(buffer, filename=f'evidence_{member.id}.png')
            embed.set_image(url=f"attachment://evidence_{member.id}.png")
        else:
            embed.description += "\n**No evidence was provided.**"
        embed.set_author(
            name=f'{helper} (ID: {helper.id})', icon_url=helper.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        logs = self.bot.get_channel(964165082437263361)  # 816512034228666419
        await logs.send(embed=embed, file=file)  # type: ignore
        

    @commands.hybrid_group(name="helper")
    async def helper(self, ctx: commands.Context[CodingBot]) -> None:
        """
        Help command for helpers to manage the help channels
        """
        await ctx.send_help(ctx.command)

    @helper.command(name="warn")
    async def help_warn(
        self,
        ctx: commands.Context[CodingBot],
        member: discord.Member,
        *,
        reason: str
    ) -> None:
        """
        Warns a member breaking rules in help channels.
        
        Usage:
        {prefix}helper warn <member> <reason>

        Example:
        {prefix}helper warn {member} "Breaking rules"
        """
        if len(reason) > 256:
            return await self.bot.reply(ctx,"The reason must be less than 256 characters.")

        await self.bot.conn.insert_record(
            'warnings',
            table='help_warns',
            columns=('guild_id', 'user_id', 'helper_id', 'reason', 'date'),
            values=(ctx.guild.id, member.id, ctx.author.id,
                    reason, ctx.message.created_at.timestamp())
        )
        await self.bot.reply(ctx,f'Help-warned {member.mention}')
        evidence = await self.capture_evidence(ctx)
        await self.log(
            action='warn', 
            member=member, 
            helper=ctx.author, 
            reason=reason, 
            evidence=evidence
        )
        
        

    @helper.command(name="warnings")
    async def help_warnings(
        self, 
        ctx: commands.Context[CodingBot], 
        member: discord.Member
    ) -> None:
        """
        Shows a list of help warnings for a member.

        Usage:
        {prefix}helper warnings <member>
        
        """
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
            return await self.bot.reply(ctx,f'{member.mention} has no help-warnings.')

        for i, warning in enumerate(records, 1):
            helper = ctx.guild.get_member(warning.helper_id)
            if helper:
                helper = helper.mention
            else:
                helper = 'Unknown'
            embed.add_field(name="`{}.` Reason: {}".format(
                i, warning.reason), value=f"Issued by: {helper} - <t:{int(warning.date)}:f>", inline=False)

        await self.bot.reply(ctx,embed=embed)

    @helper.command(name="clearwarning", aliases = ['chw'])
    async def help_clearwarning(
        self, 
        ctx: commands.Context[CodingBot], 
        member: discord.Member, 
        index: int = None
    ) -> None:
        """
        Clears a help warning from a member.

        Usage:
        {prefix}helper clearwarning <member> [index]
        """
        warn = None

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
                arguments=('date', 'reason'),
                table='help_warns',
                where=('guild_id', 'user_id'),
                values=(ctx.guild.id, target.id),
                extras=['ORDER BY date DESC']
            )

            if not records:
                return await self.bot.reply(ctx,f'{target.mention} has no warnings.')

            for i, sublist in enumerate(records, 1):
                if index == i:
                    warn = sublist.reason
                    await self.bot.conn.delete_record(
                        'warnings',
                        table='help_warns',
                        where=('guild_id', 'user_id', 'date'),
                        values=(ctx.guild.id, target.id, sublist.date)
                    )
                    break

        await self.bot.reply(ctx,f'{target.mention}\'s warning was cleared.')
        await self.log(action='warn', undo=True, member=target, helper=ctx.author, warn=warn)

    @helper.command(name="ban")
    async def help_ban(
        self, 
        ctx: commands.Context[CodingBot], 
        member:discord.Member, 
        *,
        reason: str
    ) -> None:
        """
        Ban someone from help channels

        Usage:
        {prefix}helper ban <member> <reason>
        """
        help_ban_role = ctx.guild.get_role(HELP_BAN_ROLE_ID)
        read_help_rules_role = ctx.guild.get_role(READ_HELP_RULES_ROLE_ID)
        if help_ban_role in member.roles:
            return await self.bot.reply(ctx,f'{member.mention} is already help-banned')

        if read_help_rules_role in member.roles:
            await member.remove_roles(read_help_rules_role)
        if not help_ban_role in member.roles:
            await member.add_roles(help_ban_role)

        await self.bot.reply(ctx,f'help-banned {member.mention} with reason: {reason}')
        try:
            await member.send(f"You have been help-banned with reason: {reason}")
        except discord.Forbidden:
            pass

    @helper.command(name="unban")
    async def help_unban(
        self, 
        ctx: commands.Context[CodingBot], 
        member: discord.Member
    ) -> None:
        """
        Unban someone from help channels

        Usage:
        {prefix}helper unban <member>
        """
        help_ban_role = ctx.guild.get_role(HELP_BAN_ROLE_ID)
        read_help_rules_role = ctx.guild.get_role(READ_HELP_RULES_ROLE_ID)
        if not help_ban_role in member.roles:
            return await self.bot.reply(ctx,f'{member.mention} is not help-banned')

        if not read_help_rules_role in member.roles:
            await member.add_roles(read_help_rules_role)
        if help_ban_role in member.roles:
            await member.remove_roles(help_ban_role)

        await self.bot.reply(ctx,f'help-unbanned {member.mention}')
        try:
            await member.send(f"You have been help-unbanned")
            await self.log(action='ban', undo=True, member=member, helper=ctx.author)
        except discord.Forbidden:
            pass

    @helper.command(name="verify")
    async def help_verify(
        self, 
        ctx: commands.Context[CodingBot], 
        target: discord.Member
    ) -> None:
        """
        Help verify a member

        Usage:
        {prefix}helper verify <member>
        """
        read_help_rules_role = ctx.guild.get_role(READ_HELP_RULES_ROLE_ID)

        if read_help_rules_role in target.roles:
            embed = discord.Embed(title="ERROR!", description=f"{target.mention} is already verified")
            embed.set_footer(text=f"Command executed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        else:
            embed = discord.Embed(title="Member verified", description=f"{target.mention} was successfully verified")
            embed.set_footer(text=f"Command executed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await target.add_roles(read_help_rules_role)

        await self.bot.reply(ctx,embed=embed)

async def setup(bot):
    await bot.add_cog(Helper(bot))
