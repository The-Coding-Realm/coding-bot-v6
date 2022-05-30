from __future__ import annotations

import asyncio
import datetime
from io import BytesIO
from typing import Any, Dict, Optional, Union

import discord
import humanize
from discord.ext import commands
from ext.errors import InsufficientPrivilegeError
from ext.models import CodingBot, TimeConverter
from ext.ui.view import ConfirmButton
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ext.models import CodingBot



def trainee_check():
    def wrapper(ctx: commands.Context[CodingBot]):
        trainee_role = ctx.guild.get_role(729537643951554583)  # type: ignore
        if trainee_role:
            if ctx.author.top_role.position >= trainee_role.position:  # type: ignore
                return True
        raise InsufficientPrivilegeError(
            "{}, you don't have the permission to use this command.".format(ctx.author.mention))
    return commands.check(wrapper)


class Moderation(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot: CodingBot):
        self.bot = bot

    def check_member_permission(self, ctx: commands.Context[CodingBot], member: Union[discord.User, discord.Member]):
        if isinstance(member, discord.User):
            return False
        assert ctx.guild is not None
        assert ctx.command is not None

        if ctx.author.top_role.position <= member.top_role.position and ctx.author != ctx.guild.owner:
            return f"You can't {ctx.command.name} this member. They have a higher or equal role than you."
        elif member == ctx.author:
            return f"You can't {ctx.command.name} yourself."
        elif member == ctx.guild.owner:
            return f"You can't {ctx.command.name} the server owner."
        elif ctx.guild.me.top_role.position <= member.top_role.position:
            return f"I can't {ctx.command.name} this member. They have a higher or equal role than me."

        return False

    async def capture_evidence(self, ctx: commands.Context[CodingBot]) -> Optional[discord.Attachment]:
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

    async def log(self,
                  *,
                  action: str,
                  undo: bool = False,
                  member: discord.Member,
                  moderator: discord.Member,
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
        definition: Dict[str, Any] = {
            'ban': {
                'action': 'banned',
                'undo_action': 'unbanned',
                'color': discord.Color.red(),
                'icon': ':hammer:',
                'undo_icon': ':unlock:'
            },
            'kick': {
                'action': 'kicked',
                'undo_action': ValueError("Cannot un-kick"),
                'color': discord.Color.orange(),
                'icon': ':boot:',
                'undo_icon': ':boot:'
            },
            'mute': {
                'action': 'muted',
                'undo_action': 'unmuted',
                'color': discord.Color.light_grey(),
                'icon': ':mute:',
                'undo_icon': ':loud_sound:'},
            'warn': {
                'action': 'warned',
                'undo_action': f"removed warning ({kwargs.get('warn')}) from" if kwargs.get('warn') else "removed all warnings from",
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
            name=f'{moderator} (ID: {moderator.id})', icon_url=moderator.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        logs = self.bot.get_channel(964165082437263361)  # 816512034228666419
        await logs.send(embed=embed, file=file)  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: Optional[str] = None):
        assert ctx.guild is not None
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await ctx.send(check_made)
        try:
            await member.send('You have been :boot: **Kicked** :boot: from '
                              f'**{ctx.guild.name}**. \nReason: {reason}')
        except discord.Forbidden:
            pass
        else:
            await member.kick(reason=reason)
            await ctx.send(f'Kicked {member.mention}')
            evidence = await self.capture_evidence(ctx)
            await self.log(action='kick', moderator=ctx.author, member=member, reason=reason, evidence=evidence)  # type: ignore

#    @trainee_check()
    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: Optional[str] = None):
        assert ctx.guild is not None
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await ctx.send(check_made)
        else:
            try:
                await member.send('You have been :hammer: **Banned** :hammer: from '
                                  f'**{ctx.guild.name}**. \nReason: {reason}')
            except (discord.Forbidden, discord.HTTPException):
                pass
            await ctx.guild.ban(member, reason=reason, delete_message_days=7)
            await ctx.send(f'Banned {member.mention}')
            evidence = await self.capture_evidence(ctx)
            await self.log(action='ban', moderator=ctx.author, member=member, undo=False, reason=reason, duration=None, evidence=evidence)  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context[CodingBot], user: discord.User, *, reason: Optional[str] = None):
        assert ctx.guild is not None
        try:
            await ctx.guild.unban(user)
        except discord.NotFound:
            return await ctx.send(f'{user.mention} is not banned from this server.')
        else:
            await ctx.send(f'Unbanned {user.mention}')
            await self.log(action='ban', moderator=ctx.author, member=user, undo=True, reason=reason, duration=None)  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="mute", aliases=['timeout'])
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context[CodingBot], member: discord.Member, duration: TimeConverter, *, reason: Optional[str] = None):
        assert ctx.guild is not None
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await ctx.send(check_made)

        try:
            await member.send('You have been :mute: **Muted** :hammer: from '
                              f'**{ctx.guild.name}**. \nReason: {reason}')
        except discord.Forbidden:
            pass
        else:
            until: datetime.datetime = discord.utils.utcnow() + duration  # type: ignore
            await member.timeout(until)
            await ctx.send(f'Muted {member.mention}')
            evidence = await self.capture_evidence(ctx)
            await self.log(action='mute', moderator=ctx.author, member=member, undo=False, reason=reason, duration=duration, evidence=evidence)  # type: ignore

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: Optional[str] = None):
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await ctx.send(check_made)
        try:
            await member.timeout(None)
        except (discord.Forbidden, discord.HTTPException):
            return await ctx.send(f'{member.mention} is not muted.')
        else:
            await ctx.send(f'Unmuted {member.mention}')
            await self.log(action='mute', moderator=ctx.author, member=member, undo=True, reason=reason)  # type: ignore

    @commands.hybrid_command()
    async def massban(self, ctx: commands.Context[CodingBot], users: commands.Greedy[Union[discord.Member, discord.User]]):
        if not users:
            return await ctx.send('Please provide at least one user to ban.')
        users = set(users)  # type: ignore
        if len(users) > 100:
            return await ctx.send('Please provide less than 100 users to ban.')
        counter_dict: Dict[str, Any] = {
            'banned': [],
            'not_banned': []
        }
        for user in users:
            check_made = self.check_member_permission(ctx, user)
            if check_made:
                counter_dict['not_banned'].append(user)
                continue
            await ctx.guild.ban(user)  # type: ignore
            counter_dict['banned'].append(user)
        embed = discord.Embed(color=discord.Color.red())
        description = "Following members were banned:\n{}".format(
            ', '.join(f'{user.mention}' for user in counter_dict['banned']))
        if counter_dict['not_banned']:
            embed.color = discord.Color.yellow()
            description += f"\n\nFollowing members were not banned:\n{', '.join(f'{user.mention}' for user in counter_dict['not_banned'])}"
        embed.description = description
        await ctx.send(embed=embed)

    @trainee_check()
    @commands.hybrid_command()
    async def warn(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: Optional[str] = None):
        assert ctx.guild is not None
        if not reason:
            return await ctx.send("Please provide a reason for the warning.")
        await self.bot.conn.insert_record(
            'warnings',
            table='warnings',
            columns=('guild_id', 'user_id', 'moderator_id', 'reason', 'date'),
            values=(ctx.guild.id, member.id, ctx.author.id,
                    reason, ctx.message.created_at.timestamp())
        )
        await ctx.send(f'Warned {member.mention}')
        evidence = await self.capture_evidence(ctx)
        await self.log(action='warn', moderator=ctx.author, member=member, reason=reason, evidence=evidence)  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context[CodingBot], amount: int = 1):
        purged_amt = len(await ctx.channel.purge(limit=amount + 1))  # type: ignore
        await ctx.send(f'Purged {purged_amt} messages in {ctx.channel.mention}')  # type: ignore

    @trainee_check()
    @commands.command(name="warnings")
    async def warnings(self, ctx: commands.Context[CodingBot], member: discord.Member):
        assert ctx.guild is not None
        embed = discord.Embed(
            title=f"{member} Warnings List", color=discord.Color.red())
        records = await self.bot.conn.select_record('warnings',
                                                    arguments=(
                                                        'reason', 'moderator_id', 'date'),
                                                    table='warnings',
                                                    where=(
                                                        'guild_id', 'user_id'),
                                                    values=(
                                                        ctx.guild.id, member.id),  # type: ignore
                                                    extras=[
                                                        'ORDER BY date DESC']
                                                    )
        if not records:
            return await ctx.send(f'{member.mention} has no warnings.')

        for i, warning in enumerate(records, 1):
            moderator = ctx.guild.get_member(warning.moderator_id)
            if moderator:
                moderator = moderator.mention
            else:
                moderator = 'Unknown'
            embed.add_field(name="`{}.` Reason: {}".format(
                i, warning.reason), value=f"Issued by: {moderator} - <t:{int(warning.date)}:f>", inline=False)

        await ctx.send(embed=embed)

    @trainee_check()
    @commands.hybrid_command(name="clearwarning")
    @commands.has_permissions(manage_messages=True)
    async def clearwarning(self, ctx: commands.Context[CodingBot], member: Optional[discord.Member] = None, index: Optional[int] = None):
        assert ctx.guild is not None
        target: discord.Member = member or ctx.author  # type: ignore
        if index is None:
            await self.bot.conn.delete_record('warnings',
                                              table='warnings',
                                              where=('guild_id', 'user_id'),
                                              values=(ctx.guild.id, target.id)
                                              )
        else:
            records = await self.bot.conn.select_record('warnings',
                                                        arguments=('date',),
                                                        table='warnings',
                                                        where=(
                                                            'guild_id', 'user_id'),
                                                        values=(
                                                            ctx.guild.id, target.id),
                                                        extras=[
                                                            'ORDER BY date DESC']
                                                        )

            if not records:
                return await ctx.send(f'{target.mention} has no warnings.')

            for i, sublist in enumerate(records, 1):
                if index == i:
                    await self.bot.conn.delete_record('warnings',
                                                      table='warnings',
                                                      where=(
                                                          'guild_id', 'user_id', 'date'),
                                                      values=(
                                                          ctx.guild.id, target.id, sublist.date)
                                                      )
                    break

        await ctx.reply(f'{target.mention}\'s warning was cleared.', allowed_mentions=discord.AllowedMentions(users=False))
        await self.log(action='warn', moderator=ctx.author, member=target, undo=True)  # type: ignore

    # FEEL FREE TO MOVE THIS TO ANY COGS (IF YOU ADD ONE)

    @commands.hybrid_command(name="whois")
    async def whois(self, ctx: commands.Context[CodingBot], member: Optional[discord.Member] = None):
        target: discord.Member = member or ctx.author  # type: ignore
        embed = discord.Embed(title=f"Showing user info : {member}")
        embed.set_thumbnail(url=target.display_avatar.url)
        # Support for nitro users
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Discord User ID", value=target.id, inline=False)
        embed.add_field(name="Account Created at",
                        value=target.created_at, inline=False)
        embed.add_field(name="Discord Joined at",
                        value=target.joined_at, inline=False)

        await ctx.send(embed=embed)


async def setup(bot: CodingBot):
    await bot.add_cog(Moderation(bot))
