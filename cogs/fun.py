from __future__ import annotations

import random
from textwrap import wrap

import discord
from discord.ext import commands
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ext.models import CodingBot


class Fun(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="meme")
    async def meme(self, ctx: commands.Context[CodingBot]):
        response = await self.bot.session.get("https://meme-api.herokuapp.com/gimme")
        meme_json = await response.json()

        meme_url = meme_json['url']
        meme_name = meme_json['title']
        meme_poster = meme_json['author']
        meme_sub = meme_json['subreddit']

        embed = discord.Embed(title = meme_name, description=f"Meme by {meme_poster} from subreddit {meme_sub}")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_image(url=meme_url)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="8ball")
    async def eightball(self, ctx: commands.Context[CodingBot], *, question: str):
        responses = ["As I see it, yes.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
                    "Do not count on it.", "It is certain.", "It is decidedly so.", "Most likely.", "My reply is no.", "My sources say no.",
                    "Outlook not so good.", "Outlook good.", "Reply hazy, try again.", "Signs point to yes.", "Very doubtful.", "Without a doubt.",
                    "Yes.", "Yes, definitely.", "You may rely on it."]
        response = random.choice(responses)
        
        embed = discord.Embed(title="8ball is answering", description=f"{question}\nAnswer : {response}")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url) # Support for nitro users
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="token")
    async def token(self, ctx: commands.Context[CodingBot]):
        # If you like, you can use sr_api
        response = await self.bot.session.get("https://some-random-api.ml/bottoken")
        json = await response.json()

        bottoken = json['token']

        embed = discord.Embed(title="Ha ha ha, I grabbed your bot token.", description=bottoken)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="animal")
    async def animal(self, ctx: commands.Context[CodingBot], animal: Optional[str] = None):
        options = ("dog", "cat", "panda", "fox", "red_panda", "koala", "bird", "raccoon", "kangaroo")
        if (not animal) or (animal and animal not in options):
            animal = random.choice(options)

        response = await self.bot.session.get(f"https://some-random-api.ml/animal/{animal}")
        if response.status in range(200,300):
            json = await response.json()

            image = json["image"]
            fact = json["fact"]

            embed = discord.Embed(title="Here's the animal image you asked.")
            embed.set_image(url=image)
            embed.set_footer(text=fact)
        else:
            embed = discord.Embed(title="ERROR!",  description=f"Received a bad status code of {response.status}")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.hybrid_group(invoke_without_command=True)
    async def binary(self, ctx: commands.Context):
        embed = discord.Embed(title="Binary command", description="Available methods: ```encode```, ```decode```")

        await ctx.send(embed=embed)

    @binary.command(name="encode")
    async def binary_encode(self, ctx, *, string: str):
        response = await self.bot.session.get(f"https://some-random-api.ml/binary?encode={string}")
        if response.status in range(200,300):
            json = await response.json()

            binary_string = json['binary']

            embed = discord.Embed(title="Encoded to binary", description=binary_string)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        else:
            embed = discord.Embed(title="ERROR!",  description=f"Received a bad status code of {response.status}")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @binary.command(name="decode")
    async def binary_decode(self, ctx, binary: str):
        response = await self.bot.session.get(f"https://some-random-api.ml/binary?decode={binary}")
        if response.status in range(200,300):
            json = await response.json()

            string = json['text']

            embed = discord.Embed(title="Encoded to binary", description=string)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        else:
            embed = discord.Embed(title="ERROR!",  description=f"Received a bad status code of {response.status}")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="lyrics")
    async def lyrics(self, ctx, *, query: str = None):
        if not query:
            embed = discord.Embed(title = "No search argument!", description=f"You must provide a search argument or I couldn't find the lyrics")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        response = await self.bot.session.get(f"https://some-random-api.ml/lyrics?title={query}")
        if response.status in range(200, 300):
            json = await response.json()
            
            lyrics = json['lyrics']
            artist = json['author']
            title = json['title']
            thumbnail = json['thumbnail']['genius']

            for chunk in wrap(lyrics, 4096, replace_whitespace = False):
                embed = discord.Embed(title = f"{artist} - {title}", description = chunk)
                embed.set_thumbnail(url=thumbnail)
                embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        else:
            embed = discord.Embed(title="ERROR!",  description=f"Received a bad status code of {response.status}")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot: CodingBot):
    await bot.add_cog(Fun(bot))
    