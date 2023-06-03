from __future__ import annotations

import asyncio
import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import discord
import humanize
from discord.ext import commands
from ext.errors import InsufficientPrivilegeError
from ext.models import CodingBot, TimeConverter
from ext.ui.view import ConfirmButton
from ext.consts import TCR_MEMBER_ROLE_ID

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
        # self.guild = consts.TCR_GUILD_ID
        # categories = self.guild.by_category()
        # for _category in categories:
        #     if _category[0].id == consts.TICKET_CATEGORY_ID: # need to make a category for tickets and add it here
        #         self.category = _category[0]
        #         break

    def check_member_permission(self, ctx: commands.Context[CodingBot], member: Union[discord.User, discord.Member], priv_level: int = 1):
        if isinstance(member, discord.User):
            return False

        assert ctx.guild is not None
        assert ctx.command is not None

        if member == ctx.author:
            return f"You can't {ctx.command.name} yourself."
        elif member == ctx.guild.owner:
            return f"You can't {ctx.command.name} the server owner."
        elif ctx.author.top_role.position <= member.top_role.position and ctx.author != ctx.guild.owner:
            return f"You can't {ctx.command.name} this member. They have a higher or equal role than you."
        elif ctx.guild.me.top_role.position <= member.top_role.position and priv_level:
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
        """
        Kicks a member from the server

        Usage:
        {prefix}kick <member> [reason]

        Example:
        {prefix}kick {user} Because I don't like them
        """
        assert ctx.guild is not None
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await self.bot.reply(ctx, check_made)
        try:
            await member.send('You have been :boot: **Kicked** :boot: from '
                              f'**{ctx.guild.name}**. \nReason: {reason}')
        except discord.Forbidden:
            pass
        else:
            await member.kick(reason=reason)
            await self.bot.reply(ctx,f'Kicked {member.mention}')
            evidence = await self.capture_evidence(ctx)
            await self.log(action='kick', moderator=ctx.author, member=member, reason=reason, evidence=evidence)  # type: ignore

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: Optional[str] = None):
        """
        Bans a member from the server

        Usage:
        {prefix}ban {user} spamming
        """
        assert ctx.guild is not None
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await self.bot.reply(ctx, check_made)
        else:
            try:
                await member.send('You have been :hammer: **Banned** :hammer: from '
                                  f'**{ctx.guild.name}**. \nReason: {reason}')
            except (discord.Forbidden, discord.HTTPException):
                pass
            await ctx.guild.ban(member, reason=reason, delete_message_days=7)
            await self.bot.reply(ctx,f'Banned {member.mention}')
            evidence = await self.capture_evidence(ctx)
            await self.log(action='ban', moderator=ctx.author, member=member, undo=False, reason=reason, duration=None, evidence=evidence)  # type: ignore

    @commands.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context[CodingBot], user: discord.User, *, reason: Optional[str] = None):
        """
        Unbans a member from the server

        Usage:
        {prefix}unban <user> [reason]

        Example:
        {prefix}unban {user} I am feeling generous
        """
        assert ctx.guild is not None
        try:
            await ctx.guild.unban(user)
        except discord.NotFound:
            return await self.bot.reply(ctx,f'{user.mention} is not banned from this server.')
        else:
            await self.bot.reply(ctx,f'Unbanned {user.mention}')
            await self.log(action='ban', moderator=ctx.author, member=user, undo=True, reason=reason, duration=None)  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="mute", aliases=['timeout'])
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context[CodingBot], member: discord.Member, duration: TimeConverter, *, reason: Optional[str] = None):
        """
        Timeouts a member from the server

        Usage:
        {prefix}mute <member> <duration> [reason]
        """
        assert ctx.guild is not None
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await self.bot.reply(ctx,check_made)

        try:
            await member.send('You have been :mute: **Muted** :hammer: from '
                              f'**{ctx.guild.name}**. \nReason: {reason}')
        except discord.Forbidden:
            pass
        else:
            until: datetime.datetime = discord.utils.utcnow() + duration  # type: ignore
            await member.timeout(until)
            await self.bot.reply(ctx,f'Muted {member.mention}')
            evidence = await self.capture_evidence(ctx)
            await self.log(action='mute', moderator=ctx.author, member=member, undo=False, reason=reason, duration=duration, evidence=evidence)  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: Optional[str] = None):
        """
        Unmutes/removes timeout of a member from the server

        Usage:
        {prefix}unmute <member> [reason]

        Example:
        {prefix}unmute {user} I am feeling generous
        """
        check_made = self.check_member_permission(ctx, member)
        if check_made:
            return await self.bot.reply(ctx, check_made)
        try:
            await member.timeout(None)
        except (discord.Forbidden, discord.HTTPException):
            return await self.bot.reply(ctx,f'{member.mention} is not muted.')
        else:
            await self.bot.reply(ctx,f'Unmuted {member.mention}')
            await self.log(action='mute', moderator=ctx.author, member=member, undo=True, reason=reason)  # type: ignore

    @trainee_check()
    @commands.hybrid_command()
    async def massban(self, ctx: commands.Context[CodingBot], users: commands.Greedy[Union[discord.Member, discord.User]]):
        """
        Mass bans multiple users from the server

        Usage:
        {prefix}massban <user1> <user2> <user3> ...

        Example:
        {prefix}massban @user1 @user2 @user3
        """
        if not users:
            return await self.bot.reply(ctx,'Please provide at least one user to ban.')
        users = set(users)  # type: ignore
        if len(users) > 100:
            return await self.bot.reply(ctx,'Please provide less than 100 users to ban.')
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
        await self.bot.reply(ctx,embed=embed)

    @trainee_check()
    @commands.hybrid_command()
    async def warn(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: Optional[str] = None):
        """
        Warns a member from the server

        Usage:
        {prefix}warn <member> [reason]

        Example:
        {prefix}warn {user} broke rules
        """
        check = self.check_member_permission(ctx, member, priv_level=0)
        if check:
            return await self.bot.reply(ctx, check)
        assert ctx.guild is not None
        if not reason:
            return await self.bot.reply(ctx,"Please provide a reason for the warning.")
        await self.bot.conn.insert_record(
            'warnings',
            table='warnings',
            columns=('guild_id', 'user_id', 'moderator_id', 'reason', 'date'),
            values=(ctx.guild.id, member.id, ctx.author.id,
                    reason, ctx.message.created_at.timestamp())
        )
        await self.bot.reply(ctx,f'Warned {member.mention}')
        evidence = await self.capture_evidence(ctx)
        await self.log(action='warn', moderator=ctx.author, member=member, reason=reason, evidence=evidence)  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context[CodingBot], amount: int = 1):
        """
        Purges a number of messages from the current channel

        Usage:
        {prefix}purge [amount]

        Example:
        {prefix}purge 10
        """
        purged_amt = len(await ctx.channel.purge(limit=amount + 1))  # type: ignore
        await self.bot.reply(ctx,f'Purged {purged_amt} messages in {ctx.channel.mention}')  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="warnings")
    async def warnings(self, ctx: commands.Context[CodingBot], member: discord.Member):
        """
        Lists all warnings of a member

        Usage:
        {prefix}warnings <member>

        Example:
        {prefix}warnings {user}
        """
        assert ctx.guild is not None
        embed = discord.Embed(
            title=f"{member} Warnings List", color=discord.Color.red())
        records = await self.bot.conn.select_record(
            'warnings',
            arguments=('reason', 'moderator_id', 'date'),
            table='warnings',
            where=('guild_id', 'user_id'),
            values=(ctx.guild.id, member.id),  # type: ignore
            extras=['ORDER BY date DESC']
        )
        if not records:
            return await self.bot.reply(ctx,f'{member.mention} has no warnings.')

        for i, warning in enumerate(records, 1):
            moderator = ctx.guild.get_member(warning.moderator_id)
            if moderator:
                moderator = moderator.mention
            else:
                moderator = 'Unknown'
            embed.add_field(name="`{}.` Reason: {}".format(
                i, warning.reason), value=f"Issued by: {moderator} - <t:{int(warning.date)}:f>", inline=False)

        await self.bot.reply(ctx,embed=embed)

    @trainee_check()
    @commands.hybrid_command(name="clearwarning")
    @commands.has_permissions(manage_messages=True)
    async def clearwarning(
        self, 
        ctx: commands.Context[CodingBot], 
        member: Optional[discord.Member] = None, 
        index: Optional[int] = None
    ) -> None:
        """
        Clears a certain warning of a member.
        If no index is provided, it will clear all warnings of a member.

        Usage:
        {prefix}clearwarning [member] [index]

        Example:
        {prefix}clearwarning {user} 1
        {prefix}clearwarning {user}
        """
        assert ctx.guild is not None
        target: discord.Member = member or ctx.author  # type: ignore
        if index is None:
            await self.bot.conn.delete_record(
                'warnings',
                table='warnings',
                where=('guild_id', 'user_id'),
                values=(ctx.guild.id, target.id)
            )
        else:
            records = await self.bot.conn.select_record(
                'warnings',
                arguments=('date',),
                table='warnings',
                where=('guild_id', 'user_id'),
                values=(ctx.guild.id, target.id),
                extras=['ORDER BY date DESC']
            )

            if not records:
                return await self.bot.reply(ctx,f'{target.mention} has no warnings.')

            for i, sublist in enumerate(records, 1):
                if index == i:
                    await self.bot.conn.delete_record(
                        'warnings',
                        table='warnings',
                        where=('guild_id', 'user_id', 'date'),
                        values=(ctx.guild.id, target.id, sublist.date)
                    )
                    break

        await ctx.reply(f'{target.mention}\'s warning was cleared.', allowed_mentions=discord.AllowedMentions(users=False))
        await self.log(action='warn', moderator=ctx.author, member=target, undo=True)  # type: ignore

    @trainee_check()
    @commands.hybrid_command(name="verify")
    @commands.has_permissions(manage_roles=True)
    async def verify_member(self, ctx: commands.Context[CodingBot], target: discord.Member):
        """
        Verifies a member in the server

        Usage:
        {prefix}verify <member>

        Example:
        {prefix}verify {user}
        """
        member = ctx.guild.get_role(744403871262179430)
        if member in target.roles:
            embed = discord.Embed(title="ERROR!", description=f"{target.mention} is already verified")
            embed.set_footer(text=f"Command executed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        else:
            embed = discord.Embed(title="Member verified", description=f"{target.mention} was successfully verified")
            embed.set_footer(text=f"Command executed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await target.add_roles(member)
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="whois")
    async def whois(
        self, 
        ctx: commands.Context[CodingBot], 
        member: Optional[discord.Member] = None
    ) -> None:

        """
        Give information about a member

        Usage:
        {prefix}whois [member]

        Example:
        {prefix}whois {user}
        """
        target: discord.Member = member or ctx.author  # type: ignore
        embed = discord.Embed(title=f"Showing user info : {member}", color=discord.Color.random())
        embed.set_thumbnail(url=target.display_avatar.url)
        # Support for nitro users
        created_at_string = target.created_at.strftime('%d %B, %Y')
        created_ago = humanize.precisedelta((discord.utils.utcnow() - target.created_at).total_seconds(), minimum_unit="minutes", format="%i")
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Discord User ID", value=target.id, inline=False)
        embed.add_field(name="Account Created at",
                        value=f"{created_at_string} ({created_ago} ago)", inline=False)
        embed.add_field(name="Discord Joined at",
                        value=target.joined_at, inline=False)

        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="delete")
    @commands.has_permissions(manage_messages=True)
    async def delete(
        self, 
        ctx: commands.Context[CodingBot],
        channel: Optional[discord.TextChannel] = None,
        message: int = None
    ) -> None:
        """
        Deletes a message
        Either the message ID can be provided or user can reply to the message.

        Usage:
        {prefix}delete [channel] [message]

        Example:
        {prefix}delete #general 123456789
        {prefix}delete 123456789
        """
        if not message and not ctx.message.reference:
            return await ctx.send("Please specify a message to delete.")
        elif not message and ctx.message.reference:
            message = ctx.message.reference.resolved
            await message.delete()
        else:
            channel = channel or ctx.channel
            try:
                message = await channel.fetch_message(message)
                await message.delete()
            except discord.Forbidden:
                return await ctx.send("Something went wrong.")
            except discord.HTTPException:
                return await ctx.send("Message not found.")
        await self.bot.reply(ctx, f"{message.content} ||({message.id} was deleted by {ctx.author})||")

    @commands.hybrid_command(name="slowmode")
    @commands.has_permissions(manage_messages=True)
    async def slowmode(
        self, 
        ctx: commands.Context[CodingBot], 
        seconds: int, 
        channel: Optional[discord.TextChannel] = None
    ) -> None:
        """
        Sets the slowmode of a channel

        Usage:
        {prefix}slowmode <seconds> [channel]

        Example:
        {prefix}slowmode 10 #general
        """
        channel = channel or ctx.channel
        try:
            await channel.edit(slowmode_delay=seconds)
        except discord.HTTPException:
            await ctx.send("You passed in an integer that is too big.")
        await self.bot.reply(ctx, f"Slowmode set to {seconds} seconds")
        
    # Suggestion #1001 - Lockdown command
    @commands.hybrid_command(name="lockdown")
    @commands.has_permissions(administrator=True)
    async def lockdown(
        self,
        ctx: commands.Context[CodingBot],
    ) -> None:
        """
        Lock down the server, requires administrator permissions
        ONLY USE IT WHEN RAID HAPPENS
        
        Usage:
        {prefix}lockdown
        """
        member_role = ctx.guild.get_role(TCR_MEMBER_ROLE_ID)
        for channel in ctx.guild.channels:
            await channel.set_permissions(member_role, send_messages=False)
        await self.bot.reply(ctx, "Locked down the server")
    

    #//////////////////////////////////////////////////////////////////////////////////
    # support
    #//////////////////////////////////////////////////////////////////////////////////

    async def send_as_webhook(
        self,
        author: discord.Member,
        channel: discord.TextChannel,
        content: str = None,
        files: list[discord.File] = None,
    ):
        # webhook = discord.Webhook.from_url(
        #     config.webhook("support"),
        #     adapter=discord.AsyncWebhookAdapter(self.bot.session),
        # )
        webhook = await channel.create_webhook(name=author.name)
        await webhook.send(
            content=content,
            username=author.name,
            avatar_url=author.avatar.url,
            files=files,
        )
        await webhook.delete()

    # @commands.Cog.listener()
    # async def on_dm(self, msg):
    #     channel = discord.utils.get(
    #         self.guild.channels,
    #         name=f"🎫{msg.author.name}{msg.author.discriminator}",
    #     ) or (
    #         await self.guild.create_text_channel(
    #             f"🎫{msg.author.name}{msg.author.discriminator}",
    #             category=self.category,
    #             topic=str(msg.author.id),
    #         )
    #     )
    #     files = []
    #     for attachment in msg.attachments:
    #         files.append(
    #             await attachment.to_file(
    #                 use_cached=True, spoiler=attachment.is_spoiler()
    #             )
    #         )
    #     await self.send_as_webhook(msg.author, channel, msg.content, files)
    #     # await channel.send(msg.content, files=files)

    # @commands.Cog.listener()
    # async def on_message(self, msg):
    #     if msg.author.bot:
    #         return
    #     if msg.guild is None:
    #         return
    #     if msg.channel.category != self.category:
    #         return
    #     ids = [int(i) for i in msg.channel.topic.split()]
    #     for _id in ids:
    #         user = self.guild.get_member(_id)
    #         files = []
    #         for attachment in msg.attachments:
    #             files.append(
    #                 await attachment.to_file(
    #                     use_cached=True, spoiler=attachment.is_spoiler()
    #                 )
    #             )
    #         await user.send(msg.content or None, files=files)

    # TODO: command to add members to a ticket

    @commands.hybrid_group(name="welcomer")
    @commands.has_permissions(manage_messages=True)
    async def welcomer(
        self,
        ctx: commands.Context[CodingBot]
    ) -> None:
        """
        Welcomer commands

        Commands:
        """
        await ctx.send_help('welcomer')

    @welcomer.command(name="enable")
    async def welcomer_enable(self, ctx: commands.Context[CodingBot], help = "Enable welcomer") -> None:
        if not self.bot.welcomer_enabled:
            self.bot.welcomer_enabled = True
            await self.bot.reply(ctx, "Welcomer is now enabled.")
        else:
            await self.bot.reply(ctx, "Welcomer is already enabled.")

    @welcomer.command(name="disable", help = "Disable welcomer")
    async def welcomer_disable(self, ctx: commands.Context[CodingBot]) -> None:
        if self.bot.welcomer_enabled:
            self.bot.welcomer_enabled = False
            await self.bot.reply(ctx, "Welcomer is now disabled.")
        else:
            await self.bot.reply(ctx, "Welcomer is already disabled.")

    @welcomer.command(name="redirect", help = "Set welcomer channel")
    async def welcomer_redirect(
        self,
        ctx: commands.Context[CodingBot],
        channel: Optional[discord.TextChannel]
    ) -> None:

        channel = channel or ctx.channel

        if not self.bot.welcomer_enabled:
            return await self.bot.reply(ctx, "Welcomer is not enabled.")
        
        if self.bot.welcomer_channel_id == channel.id:
            return await self.bot.reply(ctx, "Welcomer is already set to this channel.")
        self.bot.welcomer_channel_id = channel.id
        await self.bot.reply(ctx, f"Welcomer will now redirect to {channel.mention}")


    @commands.hybrid_group(name="raid-mode")
    @commands.has_permissions(manage_messages=True)
    async def raid_mode(self, ctx: commands.Context[CodingBot]) -> None:
        """
        Raid mode commands

        Commands:
        {prefix}raid-mode enable *start raid mode*
        {prefix}raid-mode disable *stop raid mode*
        """
        await ctx.send_help('raid-mode')

    @raid_mode.command(name="enable")
    async def raid_mode_enable(self, ctx: commands.Context[CodingBot]) -> None:
        """
        Enable raid mode

        This will ban all members that have joined during the raid.
        """
        if not self.bot.raid_mode_enabled:
            if self.bot.raid_checker.possible_raid:
                self.bot.raid_mode_enabled = True
                await self.bot.reply(ctx, "Raid mode is now enabled.")
                for member in self.bot.raid_checker.cache:
                    if self.bot.raid_checker.check(member):
                        await member.ban(reason="Raid mode enabled and met raid criteria.")
            else:
                await self.bot.reply(ctx, "There is no raid that has been detected yet.")
        else:
            await self.bot.reply(ctx, "Raid mode is already enabled.")

    @raid_mode.command(name="disable")
    async def raid_mode_disable(self, ctx: commands.Context[CodingBot]) -> None:
        if self.bot.raid_mode_enabled:
            self.bot.raid_mode_enabled = False
            await self.bot.reply(ctx, "Raid mode is now disabled.")
        else:
            await self.bot.reply(ctx, "Raid mode is already disabled.")


async def setup(bot: CodingBot):
    await bot.add_cog(Moderation(bot))
