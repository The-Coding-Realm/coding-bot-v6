import asyncio
import datetime
from io import BytesIO
from re import I, purge
from typing import Any, Dict, Optional, Union

import discord
import humanize
from discord.ext import commands
from ext.models import TimeConverter
from ext.ui.view import ConfirmButton

from ext.errors import InsufficientPrivilegeError

def trainee_check():
    def wrapper(ctx: commands.Context):
        trainee_role = ctx.guild.get_role(729537643951554583)
        if trainee_role:
            if ctx.author.top_role.position >= trainee_role.position:
                return True
        raise InsufficientPrivilegeError("{}, you don't have the permission to use this command.".format(ctx.author.mention))
    return commands.check(wrapper)

class Moderation(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def check_member_permission(self, ctx, member):
        if isinstance(member, discord.User):
            return False
        if ctx.author.top_role.position <= member.top_role.position and ctx.author != ctx.guild.owner:
            return f"You can't {ctx.command.name} this member. They have a higher or equal role than you."
        elif member == ctx.author:
            return f"You can't {ctx.command.name} yourself."
        elif member == ctx.guild.owner:
            return f"You can't {ctx.command.name} the server owner."

    async def capture_evidence(self, ctx) -> Optional[discord.Attachment]:
        view = ConfirmButton(ctx)
        view.message = await ctx.author.send(f'Do you want to provide an evidence for your action?', view=view)
        view_touched = not (await view.wait())
        evidence_byts = None
        if view_touched:
            if view.confirmed:
                try:
                    initial_mess = await ctx.author.send("Please send the evidence in the form of an attachment.")
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
                  reason: str = 'No reason was provided',
                  duration: Optional[datetime.timedelta] = None,
                  **kwargs: Dict[str, Any]
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
                     'undo_icon': ':loud_sound:'                    },
            'warn': {
                     'action': 'warned',
                     'undo_action': f"removed warning ({kwargs.get('warn')}) from" if kwargs.get('warn') else "removed all warnings from", 
                     'icon': ':warning:',
                     'undo_icon': ':flag_white:',
                     'color': discord.Color.yellow()
            }
        }
        if action not in definition:
            raise ValueError(f"Invalid action {action}")
        action_info = definition.get(action)
        if undo and isinstance(action_info.get('undo_action'), ValueError):
            raise action_info.get('undo_action')

        action_string = action_info.get('action') if not undo else action_info.get('undo_action')
        icon = action_info.get('icon') if not undo else action_info.get('undo_icon')
        color = discord.Color.green() if undo else action_info.get('color')

        embed = discord.Embed(color=color, timestamp=discord.utils.utcnow())
        embed.description = "{} **Action:** {}\n**Reason:** {}\n".format(icon, action_string.title(), reason)
        if duration:
            embed.description += "**Duration:** {}\n".format(humanize.naturaldelta(duration, minimum_unit='seconds'))
        file = None
        if evidence := kwargs.get('evidence'):
            embed.description += "\n**Evidence provided below:**"
            buffer = BytesIO(evidence)
            buffer.seek(0)
            file = discord.File(buffer, filename=f'evidence_{member.id}.png')
            embed.set_image(url=f"attachment://evidence_{member.id}.png")
        else:
            embed.description += "\n**No evidence was provided.**"
        embed.set_author(name=f'{moderator} (ID: {moderator.id})', icon_url=moderator.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        logs = self.bot.get_channel(816512034228666419) # 816512034228666419
        await logs.send(embed=embed, file=file)        

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
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
            await self.log(action='kick', moderator=ctx.author, member=member, reason=reason, evidence=evidence)

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await ctx.send(check_made)
        evidence = await self.get_evidence(ctx)
        try:
            await member.send('You have been :hammer: **Banned** :hammer: from '
                               f'**{ctx.guild.name}**. \nReason: {reason}')
        except discord.Forbidden:
            pass
        else:
            await member.ban(reason=reason, delete_message_days=7)
            await ctx.send(f'Banned {member.mention}')
            await self.log(action='ban', moderator=ctx.author, member=member, undo=False, reason=reason, duration=None, evidence=evidence)

    @commands.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user: discord.User, *, reason: str = None):
        try:
            await ctx.guild.unban(user)
        except discord.NotFound:
            return await ctx.send(f'{user.mention} is not banned from this server.')
        else:
            await ctx.send(f'Unbanned {user.mention}')
            await self.log(action='ban', moderator=ctx.author, member=user, undo=True, reason=reason, duration=None)

    @commands.hybrid_command(name="mute", aliases=['timeout'])
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: TimeConverter, *, reason: str = None):
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await ctx.send(check_made)
        
        try:
            await member.send('You have been :mute: **Muted** :hammer: from '
                               f'**{ctx.guild.name}**. \nReason: {reason}')
        except discord.Forbidden:
            pass
        else:
            until = discord.utils.utcnow() + duration
            await member.timeout(until)
            await ctx.send(f'Muted {member.mention}')
            evidence = await self.capture_evidence(ctx)
            await self.log(action='mute', moderator=ctx.author, member=member, undo=False, reason=reason, duration=duration, evidence=evidence)

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await ctx.send(check_made)
        try:
            await member.timeout(None)
        except (discord.Forbidden, discord.HTTPException):
            return await ctx.send(f'{member.mention} is not muted.')
        else:
            await ctx.send(f'Unmuted {member.mention}')
            await self.log(action='mute', moderator=ctx.author, member=member, undo=True, reason=reason)

    @commands.hybrid_command()
    async def massban(self, ctx: commands.Context, users: commands.Greedy[Union[discord.Member, discord.User]]):
        if not users:
            return await ctx.send('Please provide at least one user to ban.')
        users = set(users)
        if len(users) > 100:
            return await ctx.send('Please provide less than 100 users to ban.')
        counter_dict = {
            'banned': [],
            'not_banned': []
        }
        for user in users:
            check_made = self.check_member_permission(ctx, user)
            if check_made:
                counter_dict['not_banned'].append(user)
                continue
            await ctx.guild.ban(user)
            counter_dict['banned'].append(user)
        embed = discord.Embed(color=discord.Color.red())
        description = "Following members were banned:\n{}".format(', '.join(f'{user.mention}' for user in counter_dict['banned']))
        if counter_dict['not_banned']:
            embed.color = discord.Color.yellow()
            description += f"\n\nFollowing members were not banned:\n{', '.join(f'{user.mention}' for user in counter_dict['not_banned'])}"
        embed.description = description
        await ctx.send(embed=embed)
    
    @trainee_check()
    @commands.hybrid_command()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        if not reason:
            return await ctx.send("Please provide a reason for the warning.")
        async with self.bot.conn.cursor('warnings') as cur:
            await cur.execute('''INSERT INTO warnings 
            (guild_id, user_id, moderator_id, reason, date) VALUES (?, ?, ?, ?, ?)
            ''', (ctx.guild.id, member.id, ctx.author.id, reason, int(ctx.message.created_at.timestamp())))
        await self.bot.conn.warnings.commit()
        await ctx.send(f'Warned {member.mention}')

    @trainee_check()
    @commands.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int = 1):
        purged_amt = len(await ctx.channel.purge(limit=amount+1))
        await ctx.send(f'Purged {purged_amt} messages in {ctx.channel.mention}')


    @trainee_check()
    @commands.command(name="warnings")
    async def warnings(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        async with self.bot.conn.cursor('warnings') as cur:
            await cur.execute('''SELECT moderator_id, reason, date FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY date DESC''', (ctx.guild.id, member.id))
            embed = discord.Embed(title=f"{member} Warnings List", color=discord.Color.red())

            i = 1
            async for warning in cur:
                moderator_id, reason, date = warning
                moderator = ctx.guild.get_member(moderator_id)
                if moderator:
                    moderator = moderator.mention
                else:
                    moderator = 'Unknown'
                
                embed.add_field(name="`{}.` Reason: {}".format(i, reason), value=f"Issued by: {moderator} - <t:{date}:f>", inline=False)
                i += 1
            if not embed.fields:
                return await ctx.send(f'{member.mention} has no warnings.')
            await ctx.send(embed=embed)

    @trainee_check()
    @commands.hybrid_command(name="clearwarning")
    @commands.has_permissions(manage_messages=True)
    async def clearwarning(self, ctx: commands.Context, member: discord.Member = None, index: int = None):
        member = member or ctx.author
        async with self.bot.conn.cursor('warnings') as cur:
            if index is None:
                await cur.execute('''DELETE FROM warnings WHERE guild_id = ? AND user_id = ?''', (ctx.guild.id, member.id))
            else:
                await cur.execute('''SELECT date FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY date DESC''', (ctx.guild.id, member.id))
                i = 0
                async for row in cur:
                    if i == index - 1:
                        await cur.execute('''DELETE FROM warnings WHERE guild_id = ? AND user_id = ? AND date = ?''', (ctx.guild.id, member.id, row[0]))
                        break
                    i += 1
        await self.bot.conn.warnings.commit()
        await ctx.send(f'{member.mention}\'s warning was cleared.')


async def setup(bot):
    await bot.add_cog(Moderation(bot))
