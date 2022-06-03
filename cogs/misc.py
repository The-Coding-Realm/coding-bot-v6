from __future__ import annotations

import re
import random
from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands
from ext.http import Http
from ext.ui.view import Piston, Rocks

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
        matches = self.regex["codeblock"].findall(codeblock)
        lang = matches[0][0] or matches[0][1]
        if not matches:
            return await msg.edit(
                await self.bot.embed(
                    title="```ansi\n[1;31mInvalid codeblock\n```"
                )
            )
        if not lang:
            return await msg.edit(
                await self.bot.embed(
                    title="```ansi\n[1;31mno language specified\n```"
                )
            )
        code = matches[0][2]
        msg = await self.bot.reply(ctx, "...")
        await msg.edit(
            view=Piston(
                self,
                code,
                lang,
                msg,
            ),
        )
        
            
async def setup(bot: CodingBot):
    await bot.add_cog(Miscellaneous(bot))
    
