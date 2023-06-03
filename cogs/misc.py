from __future__ import annotations

import string

import random
import re
import string
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

import button_paginator as pg
import discord
from discord.ext import commands
from ext.helpers import Spotify, grouper, ordinal_suffix_of, find_anime_source
from ext.http import Http
from ext.ui.view import Piston

if TYPE_CHECKING:
    from ext.models import CodingBot



class Miscellaneous(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot
        self.http = Http(bot.session)
        self.regex = {
            "codeblock": re.compile(r"(\w*)\s*(?:```)(\w*)?([\s\S]*)(?:```$)")
        }

    async def cog_check(self, ctx: commands.Context[CodingBot]) -> bool:
        if ctx.guild:
            return True
        await ctx.send("Please use commands in the server instead of dms")
        return False

    @commands.hybrid_command(name='retry', aliases=['re'], help="Re-execute a command by replying to a message")
    async def retry(self, ctx: commands.Context[CodingBot]):
        """
        Reinvoke a command, running it again. This does NOT bypass any permissions checks | Code from v4
        """
        try:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except discord.errors.NotFound:
            return await ctx.send('I couldn\'t find that message')
        if message.author == ctx.author:
            await ctx.message.add_reaction('\U00002705')
            context = await self.bot.get_context(message)
            await self.bot.invoke(context)
        else:
            await ctx.send(embed='That isn\'t your message')
    
    @commands.hybrid_command(name="afk", aliases = ["afk-set", "set-afk"], help = "Sets your afk")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def afk(self, ctx: commands.Context[CodingBot], *, reason: Optional[str] = None):
        """
        Set your afk status.

        Usage:
        ------
        `{prefix}afk`: *will set your afk status to nothing*
        `{prefix}afk [reason]`: *will set your afk status to [reason]*
        """
        assert isinstance(ctx.author, discord.Member)
        assert ctx.guild is not None

        reason = reason or "AFK"
        member = ctx.author
        staff_role = ctx.guild.get_role(795145820210462771)
        on_pat_staff = member.guild.get_role(726441123966484600) # "on_patrol_staff" role

        if staff_role in member.roles:
            try:
                await member.remove_roles(on_pat_staff)  # type: ignore
            except (discord.Forbidden, discord.HTTPException):
                pass
        if ctx.guild.id not in self.bot.afk_cache:
            self.bot.afk_cache[ctx.guild.id] = {}
        if member.id not in self.bot.afk_cache.get(ctx.guild.id):
            await self.bot.conn.insert_record(
                'afk',
                table='afk',
                values=(member.id, reason, int(ctx.message.created_at.timestamp())),
                columns=['user_id', 'reason', 'afk_time']
            )
            try:
                await member.edit(nick=f"[AFK] {member.display_name}")
            except:
                pass
            try:
                self.bot.afk_cache[ctx.guild.id][member.id] = (reason, int(ctx.message.created_at.timestamp()))
            except KeyError:
                self.bot.afk_cache[ctx.guild.id] = {member.id: (reason, int(ctx.message.created_at.timestamp()))}
            embed = discord.Embed(
                description=f"{ctx.author.mention} I set your AFK: {reason}",
                color=discord.Color.blue()
            )
            await ctx.reply(embed=embed)
        else:
            embed = discord.Embed(
                description=" You are already AFK",
                color=discord.Color.brand_red()
            )
            await ctx.reply(embed=embed, ephemeral=True)


    @commands.command()
    async def run(self, ctx, *, codeblock: str):
        """
        Runs code in a codeblock.
        The codeblock must be surrounded by ``` and the language must be specified.
        Example: ```py\nprint('hello world')\n```

        Usage:
        ------
        `{prefix}run [codeblock]`: *will run the code in the [codeblock]*
        """
        msg = await self.bot.reply(ctx, "...")
        matches = self.regex["codeblock"].findall(codeblock)
        lang = matches[0][0] or matches[0][1]
        if not matches:
            return await msg.edit(
                embed=await self.bot.embed(
                    title="```ansi\nInvalid codeblock\n```"
                )
            )
        if not lang:
            return await msg.edit(
                embed=await self.bot.embed(
                    title="```ansi\nno language specified\n```"
                )
            )
        code = matches[0][2]
        await msg.edit(
            view=Piston(
                self,
                code,
                lang,
                msg,
                ctx.author,
            ),
        )

    @commands.hybrid_group(name="thanks", invoke_without_command=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def thanks(self, ctx: commands.Context[CodingBot], member: discord.Member):
        """
        See how many thanks someone has.

        Usage:
        ------
        `{prefix}thanks {user}`: *will show how many thanks user has*
        """
        record = await self.bot.conn.select_record(
            'thanks',
            table='thanks_info',
            arguments=('thanks_count',),
            where=['guild_id', 'user_id'],
            values=[ctx.guild.id, member.id]
        )
        if not record:
            return await ctx.send(f"{member.display_name} does not have any thanks")
        thanks = record[0]
        await ctx.send(f"{member.display_name} has `{thanks.thanks_count}` thanks")

    @commands.hybrid_group(name="thank", invoke_without_command=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def thank(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: str):
        """
        Thank someone.

        Usage:
        ------
        `{prefix}thank {user} {reason}`: *will thank user*
        """

        if member.id == ctx.author.id:
            return await ctx.reply("You can't thank yourself.", ephemeral=True)

        elif member.id == self.bot.user.id:
            return await ctx.reply("You can't thank me.", ephemeral=True)
        
        await self.bot.conn.insert_record(
            'thanks',
            table='thanks_info',
            values=(member.id, ctx.guild.id, 1),
            columns=['user_id', 'guild_id', 'thanks_count'],
            extras=['ON CONFLICT (user_id) DO UPDATE SET thanks_count = thanks_count + 1']
        )
        staff_role = ctx.guild.get_role(795145820210462771)
        member_is_staff = 1 if staff_role and staff_role in member.roles else 0
        characters = string.ascii_letters + string.digits
        await self.bot.conn.insert_record(
            'thanks',
            table='thanks_data',
            columns=(
                'is_staff', 'user_id', 'giver_id', 'guild_id', 
                'message_id', 'channel_id', 'reason', 'thank_id',
                'date'
            ),
            values=(member_is_staff, member.id, ctx.author.id, ctx.guild.id, 
                ctx.message.id, ctx.channel.id, reason or "No reason given", 
                "". join(random.choice(characters) for _ in range(7)), 
                int(ctx.message.created_at.timestamp())
            )
        )
        await ctx.reply(f"{ctx.author.mention} you thanked {member.mention}!", ephemeral=True)

    @thank.command(name="show")
    @commands.has_any_role(783909939311280129, 797688360806121522)
    async def thank_show(self, ctx: commands.Context[CodingBot], member: discord.Member):
        """
        Show the thanks information of a user.

        Usage:
        ------
        `{prefix}thank show {user}`: *will show the thanks information of user*
        """
        records = await self.bot.conn.select_record(
            'thanks',
            table='thanks_data',
            arguments=(
                'giver_id', 'message_id','channel_id','reason','thank_id',
                'date'
                ),
            where=['user_id'],
            values=[member.id]
        )

        if not records:
            return await ctx.reply(f"{member.mention} does not have any thanks.", ephemeral=True)

        information = tuple(grouper(5, records))

        embeds = []
        for info in information:
            embed = discord.Embed(title=f'Showing {member.display_name}\'s data')
            for data in info:
                giver_id = data.giver_id
                msg_id = data.message_id
                channel_id = data.channel_id
                reason = data.reason
                thank_id = data.thank_id
                timestamp = data.date
                channel = ctx.guild.get_channel(channel_id)
                msg_link = f'https://discord.com/channels/{ctx.guild.id}/{channel.id}/{msg_id}'

                giver = ctx.guild.get_member(giver_id)

                embed.add_field(name=f'Thank: {thank_id}', value=f"Thank giver: {giver.mention}\nDate: <t:{timestamp}:R>\nReason: {reason}\nThank given in: {channel.mention}\nMessage link: [Click here!]({msg_link})", inline=False)

            embeds.append(embed)

        if len(embeds) == 1:
            await self.bot.reply(ctx, embed=embeds[0])
        else:
            paginator = pg.Paginator(self.bot, embeds, ctx)
            paginator.add_button("back", emoji="◀️")
            paginator.add_button("goto", style=discord.ButtonStyle.primary)
            paginator.add_button("next", emoji="▶️")
            await paginator.start()


    @thank.command(name="delete")
    @commands.has_any_role(783909939311280129, 797688360806121522) 
    async def thank_delete(self, ctx: commands.Context[CodingBot], thank_id: str):
        """
        Delete a thank.

        Usage:
        ------
        `{prefix}thank delete [thank_id]`: *will delete the thank with the id [thank_id]*
        
        """
        record = await self.bot.conn.select_record(
            'thanks',
            table='thanks_data',
            arguments=['user_id'],
            where=['thank_id'],
            values=[thank_id]
        )
        if not record:
            return await ctx.send("No thank with that id")

        user_id = record[0].user_id

        await self.bot.conn.delete_record(
            'thanks',
            table='thanks_data',
            where=['thank_id'],
            values=[thank_id]
        )

        await self.bot.conn.insert_record(
            'thanks',
            table='thanks_info',
            values=(user_id, ctx.guild.id, -1),
            columns=['user_id', 'guild_id', 'thanks_count'],
            extras=['ON CONFLICT (user_id) DO UPDATE SET thanks_count = thanks_count - 1']
        )
        await ctx.send(f"Remove thank from <@{user_id}> with id {thank_id}")

    @thank.command(name="leaderboard", aliases=['lb'])
    async def thank_leaderboard(self, ctx: commands.Context[CodingBot]):
        """
        Shows the thanks leaderboard.

        Usage:
        ------
        `{prefix}thanks leaderboard`: *will show the thanks leaderboard*
        """


        records = await self.bot.conn.select_record(
            'thanks',
            table='thanks_info',
            arguments=('user_id', 'thanks_count'),
            where=['guild_id'],
            values=[ctx.guild.id],
            extras=['ORDER BY thanks_count DESC, user_id ASC LIMIT 100'],
        )
        if not records:
            return await ctx.reply("No thanks leaderboard yet.", ephemeral=True)

        information = tuple(grouper(10, records))

        embeds = []
        for info in information:
            user = [ctx.guild.get_member(i.user_id) for i in info]
            embed = discord.Embed(
                title=f"Thank points leaderboard",
                description="\n\n".join(
                    [f"`{i}{ordinal_suffix_of(i)}` is {user.mention} with `{thanks_count.thanks_count}` Thank point(s)" for i, (user, thanks_count) 
                    in enumerate(zip(user, info), 1)
                ]
                ),
                color=discord.Color.blue()
            )
            embeds.append(embed)
        if len(embeds) == 1:
            paginator = pg.Paginator(self.bot, embeds, ctx)
            paginator.add_button("delete", label="Delete", style=discord.ButtonStyle.danger)
            await paginator.start()
        else:
            paginator = pg.Paginator(self.bot, embeds, ctx)
            paginator.add_button("back", emoji="◀️")
            paginator.add_button("goto", style=discord.ButtonStyle.primary)
            paginator.add_button("next", emoji="▶️")
            paginator.add_button("delete", label="Delete", style=discord.ButtonStyle.danger)
            await paginator.start()


    @commands.hybrid_group(invoke_without_command=True)
    async def trainee(self, ctx: commands.Context[CodingBot]):
        """
        Sends the trainee help menu.
        """
        await ctx.send_help('trainee')

    @trainee.command(name="list")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def trainee_list(self, ctx: commands.Context[CodingBot]):
        """
        Lists all the trainees in the server.

        Usage:
        ------
        `{prefix}list trainees`: *will list all the trainees in the server*
        """

        trainee_role = ctx.guild.get_role(729537643951554583)  # type: ignore
        members = trainee_role.members
        
        if not members:
            trainees = "No trainees yet."
        else:
            trainees = "\n".join(
                f"{i}. {member.mention}" for i, member in enumerate(members, 1)
            )
        embed = discord.Embed(
            title=f"Trainees list",
            description=trainees,
            color=discord.Color.blue()
        )
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(aliases=['sp'])
    @commands.cooldown(5, 60.0, type=commands.BucketType.user)
    async def spotify(self, ctx: commands.Context, member: discord.Member = None):
        """
        Shows the spotify status of a member.

        Usage:
        ------
        `{prefix}spotify`: *will show your spotify status*
        `{prefix}spotify [member]`: *will show the spotify status of [member]*
        """
        member = member or ctx.author
        spotify = Spotify(bot=self.bot, member=member)
        embed = await spotify.get_embed()
        if not embed:
            if member == ctx.author:
                return await ctx.reply(f"You are currently not listening to spotify!", mention_author=False)
            return await self.bot.reply(
                ctx,
                f"{member.mention} is not listening to Spotify", 
                mention_author=False,
                allowed_mentions=discord.AllowedMentions(users=False)
            )
        embed, file, view = embed
        await self.bot.send(ctx, embed=embed, file=file, view=view)

    # @commands.command(name='sauce')
    # async def sauce(self, ctx: commands.Context[CodingBot], source: Optional[str] = None):
    #     """
    #     Get the sauce of a source.
    #     Example: {prefix}sauce <source>
    #     """
    #     source = source or ctx.message.attachments[0].url if ctx.message.attachments else None
    #     if not source:
    #         return await ctx.send(
    #             'Please provide image/video url, '
    #             'reply to another message or upload the image/video along with the command. '
    #             f'Please use {ctx.prefix}help saucefor more information.')
        
    #     anime_information = await find_anime_source(self.bot.session, source)

    #     result = anime_information['result']
    #     if not result:
    #         return await ctx.send(
    #             'Could not find any anime source for this image/video.'
    #         )
    #     else:
    #         result = result[0]
            
    #     print(ctx.channel.is_nsfw())
    #     print(result['anilist'].get('isAdult'))

    #     if result['anilist'].get('isAdult') and not ctx.channel.is_nsfw():
    #         await ctx.send(
    #             'This source is marked as adult content and can only be used in NSFW channels. I Will try to DM you instead.'
    #         )
    #         ctx = ctx.author
    
    #     browser = "https://trace.moe/?url={}".format(source)

    #     anilist_id = result['anilist']['id']
    #     mal_id = result['anilist']['idMal']

    #     anilist_url = f'https://anilist.co/anime/{anilist_id}'
    #     anilist_banner = f"https://img.anili.st/media/{anilist_id}"
    #     mal_url = f'https://myanimelist.net/anime/{mal_id}'

    #     native = result['anilist']['title'].get('native')
    #     english = result['anilist']['title'].get('english')
    #     romaji = result['anilist']['title'].get('romaji')

    #     filename = result['filename']
    #     similarity = round(result['similarity'] * 100, 2)

    #     from_timestamp = timedelta(seconds=int(result['from']))
    #     to_timestamp = timedelta(seconds=int(result['to']))
        
    #     embed = discord.Embed(timestamp=discord.utils.utcnow())
    #     embed.add_field(
    #         name="Anime Title", DD
    #         value=f"Native: {native}\nEnglish: {english}\nRomaji: {romaji}", 
    #         inline=False
    #     )
    #     embed.add_field(
    #         name="Scene Details",
    #         value=f"**Filename:** {filename}\n**From:** {from_timestamp}\n**To:** {to_timestamp}\n**Similarity:** {similarity}%",
    #         inline=False
    #     )
    #     embed.add_field(
    #         name="Links",
    #         value="[Open In Browser]({}) | [AniList]({}) | [MyAnimeList]({})".format(
    #             browser, anilist_url, mal_url
    #         ),
    #         inline=False

    #     )
    #     embed.set_image(url=anilist_banner)
    #     try:
    #         await ctx.send(embed=embed)
    #     except (discord.HTTPException, discord.Forbidden):
    #         pass

            
async def setup(bot: CodingBot):
    await bot.add_cog(Miscellaneous(bot))
