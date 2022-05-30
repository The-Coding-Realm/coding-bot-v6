from __future__ import annotations

import random

import discord
from discord.ext import commands
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ext.models import CodingBot


class Fun(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False

    def __init__(self, bot: CodingBot):
        self.bot = bot

    @commands.hybrid_command(name="meme")
    async def meme(self, ctx: commands.Context[CodingBot]):
        response = await self.bot.session.get("https://meme-api.herokuapp.com/gimme")
        meme_json = await response.json()

        meme_url = meme_json['url']
        meme_name = meme_json['title']
        meme_poster = meme_json['author']
        meme_sub = meme_json['subreddit']

        embed = discord.Embed(
            title=meme_name, description=f"Meme by {meme_poster} from subreddit {meme_sub}")
        embed.set_image(url=meme_url)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="8ball")
    async def eightball(self, ctx: commands.Context[CodingBot], *, question: str):
        responses = ["As I see it, yes.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
                     "Do not count on it.", "It is certain.", "It is decidedly so.", "Most likely.", "My reply is no.", "My sources say no.",
                     "Outlook not so good.", "Outlook good.", "Reply hazy, try again.", "Signs point to yes.", "Very doubtful.", "Without a doubt.",
                     "Yes.", "Yes, definitely.", "You may rely on it."]
        response = random.choice(responses)

        embed = discord.Embed(title="8ball is answering",
                              description=f"{question}\nAnswer : {response}")
        # Support for nitro users
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="token")
    async def token(self, ctx: commands.Context[CodingBot]):
        # If you like, you can use sr_api
        response = await self.bot.session.get("https://some-random-api.ml/bottoken")
        json = await response.json()

        bottoken = json['token']

        embed = discord.Embed(
            title="Ha ha ha, I grabbed your bot token.", description=bottoken)
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="animal")
    async def animal(self, ctx: commands.Context[CodingBot], animal: Optional[str] = None):
        options = ("dog", "cat", "panda", "fox", "red_panda",
                   "koala", "bird", "raccoon", "kangaroo")
        if (not animal) or (animal and animal not in options):
            animal = random.choice(options)

        response = await self.bot.session.get(f"https://some-random-api.ml/animal/{animal}")
        if response.status in range(200, 300):
            json = await response.json()

            image = json["image"]
            fact = json["fact"]

            embed = discord.Embed(title="Here's the animal image you asked.")
            embed.set_image(url=image)
            embed.set_footer(text=fact)
        else:
            embed = discord.Embed(
                title="ERROR!",  description=f"Received a bad status code of {response.status}")

        await ctx.send(embed=embed)

    # DO YOUR COMMANDS HERE I HAVE NOT ENOUGH CREATIVITY TO THINK ABOUT THEM KEKW


async def setup(bot: CodingBot):
    await bot.add_cog(Fun(bot))
