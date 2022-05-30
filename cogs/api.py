import re

from discord.ext import commands

from ext.http import Http
from ext.ui.view import Piston, Rocks


class Api(commands.Cog):
    def __init__(self, bot):
        self.session = Http(bot.session)
        self.bot = bot
        self.regex = {
            "codeblock": re.compile(r"(\w*)\s*(?:```)(\w*)?([\s\S]*)(?:```$)")
        }

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
    async def rock(self, ctx, *, query: str = None):
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
                print(f"[DEBUG] {image}")
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
    async def number(self, ctx, number=None):
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


async def setup(bot):
    await bot.add_cog(Api(bot))
