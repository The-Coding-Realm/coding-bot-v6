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
        self.session = Http(bot.session)
        self.bot = bot
        self.regex = {
            "codeblock": re.compile(r"(\w*)\s*(?:```)(\w*)?([\s\S]*)(?:```$)")
        }

    @commands.hybrid_command(name="afk", aliases = ["afk-set", "set-afk"], help = "Sets your afk")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def afk(self, ctx: commands.Context[CodingBot], *, reason: Optional[str] = None):
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

            emoji = random.choice(['⚪','🔴','🟤','🟣','🟢','🟡','🟠','🔵'])
            embed = discord.Embed(
                description=f"{emoji} I set your AFK: {reason}",
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

    @commands.command()
    async def rock(self, ctx: commands.Context[CodingBot], *, query: Optional[str] = None):
        async def get_rock(self):
            rock = await self.session.get_random_rock()
            name = rock["name"]
            desc = rock["desc"]
            image = rock["image"]
            rating = rock["rating"]
            embed = await self.bot.embed(
                title=f"🪨   {name}",
                url=image or "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                description=f"```yaml\n{desc}```",
            )
            if image is not None and image != "none" and image != "":
                embed.set_thumbnail(url=image)
            return (embed, rating)

        rock_info = await get_rock(self)
        return await self.bot.reply(
            ctx,
            embed=rock_info[0],
            view=Rocks(
                cog=self,
                embed_gen=get_rock,
                stars=rock_info[1],
                embed=rock_info[0],
            ),
        )

    @commands.command()
    async def number(self, ctx: commands.Context[CodingBot], number: Optional[int] = None):
        number = await (
            self.session.get_random_number()
            if (number is None)
            else self.session.get_number(number)
        )
        embed = await self.bot.embed(
            title=f"**{number}**",
            description=" ",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        return await self.bot.reply(ctx, embed=embed)

            
async def setup(bot: CodingBot):
    await bot.add_cog(Miscellaneous(bot))
    