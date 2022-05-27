import datetime

import discord
from discord.ext import commands

import humanize

class Moderation(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot):
        self.bot = bot

    async def log(self,
                  *,
                  action,
                  moderator,
                  member,
                  undo,
                  reason,
                  duration,
                  **kwargs
    ) -> None:
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

        description = (f'**{icon} {action_string.title()} {member.name}**#'
                       f'{member.discriminator} *(ID: {member.id})* \n**'
                       f':page_facing_up: Reason:** {reason}') + (' \n**:clock2: Duration:** '
                                                                  f'{humanize.precisedelta(duration)}') if duration else ''
                                                                  
        embed = discord.Embed(description=description, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
        embed.set_author(name=f'{moderator} (ID: {moderator.id}', icon_url=moderator.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)

        logs = self.bot.get_channel(816512034228666419)
        await logs.send(embed=embed)        

    def check_member_permission(self, ctx, member):
        if ctx.author.top_role.position <= member.top_role.position and ctx.author != ctx.guild.owner:
            return f"You can't {ctx.command.name} this member. They have a higher or equal role than you."
        elif member == ctx.author:
            return f"You can't {ctx.command.name} yourself."
        elif member == ctx.guild.owner:
            return f"You can't {ctx.command.name} the server owner."

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        check_made = self.check_member_permission(ctx, member)
        try:
            await member.send('You have been :hammer: **Banned** :hammer: from '
                               f'**{ctx.guild.name}**. \nReason: {reason}')
        except discord.Forbidden:
            pass
        else:
            if check_made:
                return await ctx.send(check_made)
            await member.kick(reason=reason)
            await ctx.send(f'Banned {member.mention}')
            await self.log(action='ban', moderator=ctx.author, member=member, undo=False, reason=reason, duration=None)

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        check_made = self.check_member_permission(ctx, member)
        try:
            await member.send('You have been :hammer: **Banned** :hammer: from '
                               f'**{ctx.guild.name}**. \nReason: {reason}')
        except discord.Forbidden:
            pass
        else:
            if check_made:
                return await ctx.send(check_made)
            await member.ban(reason=reason, delete_message_days=7)
            await ctx.send(f'Banned {member.mention}')
            await self.log(action='ban', moderator=ctx.author, member=member, undo=False, reason=reason, duration=None)

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

    @commands.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Contxt, amount: int = 1):
        await ctx.channel.purge(limit=amount+1)

async def setup(bot):
    await bot.add_cog(Moderation(bot))