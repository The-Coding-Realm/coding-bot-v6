from __future__ import annotations
import asyncio
from datetime import datetime

import re
from typing import TYPE_CHECKING, Optional

import discord
import button_paginator as pg
from discord.ext import commands
from ext.helpers import grouper, ordinal_suffix_of
from ext.http import Http
from ext.ui.view import Piston

if TYPE_CHECKING:
    from ext.models import CodingBot



class Miscellaneous(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot
        self.http = Http(bot.session)
        self.bot = bot
        self.regex = {
            "codeblock": re.compile(r"(\w*)\s*(?:```)(\w*)?([\s\S]*)(?:```$)")
        }

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

        if not reason:
            reason = "AFK"
        member = ctx.author
        staff_role = ctx.guild.get_role(795145820210462771)
        on_pat_staff = member.guild.get_role(726441123966484600) # "on_patrol_staff" role

        if staff_role in member.roles:
            try:
                await member.remove_roles(on_pat_staff)  # type: ignore
            except (discord.Forbidden, discord.HTTPException):
                pass
        record = await self.bot.conn.select_record(
                'afk',
                table='afk',
                arguments=('afk_time', 'reason'),
                where=('user_id',),
                values=(member.id,),
            )
        if not record:
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
            ),
        )

    @commands.hybrid_group(name="thanks", invoke_without_command=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def thanks(self, ctx: commands.Context[CodingBot], member: discord.Member, *, reason: Optional[str] = None):
        """
        Thanks someone.

        Usage:
        ------
        `{prefix}thanks {user} {reason}`: *will thank user*
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
        await self.bot.conn.insert_record(
            'thanks',
            table='thanks_data',
            columns=(
                'is_staff', 'user_id', 'giver_id', 'guild_id', 
                'message_id', 'channel_id', 'reason'
            ),
            values=(member_is_staff, member.id, ctx.author.id, ctx.guild.id, 
                ctx.message.id, ctx.channel.id, reason or "No reason given"
            )
        )
        await ctx.reply(f"{ctx.author.mention} you thanked {member.mention}!", ephemeral=True)

    @thanks.command(name="leaderboard")
    async def thanks_leaderboard(self, ctx: commands.Context[CodingBot]):
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
            await self.bot.reply(ctx, embed=embeds[0])
        else:
            paginator = pg.Paginator(self.bot, embeds, ctx)
            paginator.add_button("back", emoji="◀️")
            paginator.add_button("goto", style=discord.ButtonStyle.primary)
            paginator.add_button("next", emoji="▶️")
            await paginator.start()

    @commands.hybrid_group(invoke_without_command=True)
    async def trainee(self, ctx: commands.Context[CodingBot]):
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
        await self.bot.reply(embed=embed)

            
async def setup(bot: CodingBot):
    await bot.add_cog(Miscellaneous(bot))
    
