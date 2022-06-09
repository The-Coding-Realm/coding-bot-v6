from __future__ import annotations

import random
from textwrap import wrap

import discord
from ext.http import Http
from ext.ui.view import *
from discord.ext import commands
from typing import TYPE_CHECKING, Optional

from ext.helpers import get_rock

if TYPE_CHECKING:
    from ext.models import CodingBot
    
# For this cog's utility
def make_embed(ctx, *, title=Optional[Any], description=Optional[Any], image_url=Optional[Any]):
    embed = discord.Embed(title=title, description=desc, color=discord.Color.random())
    embed.set_image(url=image_url)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    return embed

def error_embed(ctx, *, error_msg=Optional[Any]):
    embed = discord.Embed(title="ERROR!",  description=error_msg)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    return embed


class Fun(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot: CodingBot) -> None:
        self.http = Http(bot.session)
        self.bot = bot
    
    @commands.hybrid_command()
    async def rock(self, ctx: commands.Context[CodingBot], *, query: Optional[str] = None):
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

    @commands.hybrid_command()
    async def number(
        self, 
        ctx: commands.Context[CodingBot], 
        number: Optional[int] = None
    ) -> None:
        """
        Gets a random number.
        Usage:
        ------
        `{prefix}number`: *will get a random number*
        `{prefix}number [number]`: *will get the [number]*
        """
        if number is None:
            number = random.randint(1, 100)
        await self.bot.reply(ctx, f"{number}")
        number = await (
            self.http.api["numbers"]["random"]()
            if (number is None)
            else self.api["numbers"]["number"](number)
        )
        embed = await self.bot.embed(
            title=f"**{number}**",
            description=" ",
            url="https://www.youtube.com/watch?v=o-YBDTqX_ZU",
        )
        return await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="meme")
    async def meme(self, ctx: commands.Context[CodingBot]):
        meme_json = await self.http.api["get"]["meme"]()

        meme_url = meme_json['url']
        meme_name = meme_json['title']
        meme_poster = meme_json['author']
        meme_sub = meme_json['subreddit']
        
        embed = make_embed(title=meme_name, description=f"Meme by {meme_poster} from subreddit {meme_sub}", image_url=meme_url)
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="joke")
    async def joke(self, ctx: commands.Context[CodingBot]):
        response = await self.http.api["some-random-api"]["joke"]()
        joke = response['joke']

        embed = make_embed(title="He're a joke", description=joke)

        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="8ball")
    async def eightball(self, ctx: commands.Context[CodingBot], *, question: str):
        responses = ["As I see it, yes.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
                    "Do not count on it.", "It is certain.", "It is decidedly so.", "Most likely.", "My reply is no.", "My sources say no.",
                    "Outlook not so good.", "Outlook good.", "Reply hazy, try again.", "Signs point to yes.", "Very doubtful.", "Without a doubt.",
                    "Yes.", "Yes, definitely.", "You may rely on it."]
        response = random.choice(responses)
        
        embed = make_embed(title="8ball is answering", description=f"{question}\nAnswer : {response}", )
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="token")
    async def token(self, ctx: commands.Context[CodingBot]):
        response = await self.http.api["some-random-api"]["bottoken"]()
        json = await response.json()

        bottoken = json['token']

        embed = make_embed(title="Ha ha ha, I grabbed your bot token.", description=bottoken)
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="animal")
    async def animal(self, ctx: commands.Context[CodingBot], animal: Optional[str] = None):
        options = ("dog", "cat", "panda", "fox", "red_panda", "koala", "bird", "raccoon", "kangaroo")
        if (not animal) or (animal and animal not in options):
            animal = random.choice(options)

        response = await self.http.api["some-random-api"]["animal"](animal)
        if response.status in range(200,300):
            json = await response.json()

            image = json["image"]
            fact = json["fact"]

            embed = make_embed(title=f"Here's the {animal.capitalize()} you asked.", description=fact, image_url=image)
        else:
            embed = error_embed(error_msg=f"Received a bad status code of {response.status}")
        
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_group(invoke_without_command=True)
    async def binary(self, ctx: commands.Context[CodingBot]):
        embed = make_embed(title="Binary command", description="Available methods: `encode`, `decode`")
        await self.bot.reply(ctx, embed=embed)

    @binary.command(name="encode")
    async def binary_encode(self, ctx: commands.Context[CodingBot], *, string: str):
        binary_string = " ".join((map(lambda x: f"{ord(x):08b}", string)))

        embed = make_embed(title="Encoded to Binary", description=binary_string)

        await self.bot.reply(ctx, embed=embed)

    @binary.command(name="decode")
    async def binary_decode(self, ctx: commands.Context[CodingBot], binary: str):
        if (len(binary) - binary.count(" ")) % 8 != 0:
            return await self.bot.reply(ctx, "The binary is an invalid length.")
        binary = binary.replace(" ", "")
        string = "".join(chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8))
        embed = make_embed(title="Decoded from Binary", description=string)
            
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="lyrics")
    async def lyrics(self, ctx: commands.Context[CodingBot], *, query: str = None):
        if not query:
            embed = discord.Embed(title = "Hey! I'm confused", description=f"You must provide a search argument or I couldn't find the lyrics")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        response = await self.http.api["some-random-api"]["lyrics"](query)
        if response.status in range(200, 300):
            json = await response.json()
            
            lyrics = json['lyrics']
            artist = json['author']
            title = json['title']
            thumbnail = json['thumbnail']['genius']

            for chunk in wrap(lyrics, 4096, replace_whitespace = False):
                embed = discord.Embed(title = f"{artist} - {title}", description = chunk, color=discord.Color.random())
                embed.set_thumbnail(url=thumbnail)
                embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        else:
            embed = discord.Embed(title="ERROR!",  description=f"Received a bad status code of {response.status}")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await self.bot.reply(ctx, embed=embed)
        
    @commands.hybrid_command(name="reverse")
    async def reverse(self, ctx: commands.Context[CodingBot], *, text: str):
        embed = make_embed(title="Reversed Text", description=f"{text[::-1]}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="owofy")
    async def owofy(self, ctx: commands.Context[CodingBot], *, text: str):
        embed = make_embed(title=f"Owofied Text", description=text.replace("o", "OwO"))
        await self.bot.reply(ctx, embed=embed)

    # Filters command
    @commands.hybrid_group(invoke_without_command=True)
    async def filter(self, ctx: commands.Context[CodingBot]):
        embed = make_embed(title="Filter command", description="Available methods: `invert`, `greyscale`, `colour [hex]`")
        await self.bot.reply(ctx, embed=embed)

    @filter.command(name="invert")
    async def filter_invert(self, ctx: commands.Context[CodingBot], member: discord.Member = None):
        if not member:
            member = ctx.author
        pfp = member.display_avatar.url
        response = await self.http.api["some-random-api"]["filters"]["invert"](pfp)

        embed = make_embed(title="Filter command - Invert", image_url=response)
        await self.bot.reply(ctx, embed=embed)

    @filter.command(name="greyscale")
    async def filter_greyscale(self, ctx: commands.Context[CodingBot], member: discord.Member = None):
        if not member:
            member = ctx.author
        pfp = member.display_avatar.url
        response = await self.http.api["some-random-api"]["filters"]["greyscale"](pfp)

        embed = make_embed(title="Filter command - Greyscale", image_url=response)
        await self.bot.reply(ctx, embed=embed)

    @filter.command(name="colour")
    async def filter_colour(self, ctx: commands.Context[CodingBot], member: discord.Member = None, hex_code: str = None):
        if not member:
            member = ctx.author
        if not hex_code:
            embed = discord.Embed(title="ERROR!",  description="No Hex? Hex colour code is required")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        hex_code = hex_code.replace('#', '')
        pfp = member.display_avatar.url
        response = await self.http.api["some-random-api"]["filters"]["greyscale"](pfp, hex_code)

        embed = make_embed(title="Filter command - Colour", image_url=response)
        await self.bot.reply(ctx, embed=embed)

    @filter.command(name="brightness")
    async def filter_brightness(self, ctx: commands.Context[CodingBot], member: discord.Member = None):
        if not member:
            member = ctx.author
        pfp = member.display_avatar.url
        response = await self.http.api["some-random-api"]["filters"]["brightness"](pfp)

        embed = make_embed(title="Filter command - Brightness", image_url=response)
        await self.bot.reply(ctx, embed=embed)

    @filter.command(name="threshold")
    async def filter_threshold(self, ctx: commands.Context[CodingBot], member: discord.Member = None):
        if not member:
            member = ctx.author
        pfp = member.display_avatar.url
        response = await self.http.api["some-random-api"]["filters"]["threshold"](pfp)

        embed = make_embed(title="Filter command - Invert", image_url=threshold)
        await self.bot.reply(ctx, embed=embed)

async def setup(bot: CodingBot):
    await bot.add_cog(Fun(bot))
    