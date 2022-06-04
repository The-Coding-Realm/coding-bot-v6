from __future__ import annotations

import random
from textwrap import wrap

import discord
from ext.http import Http
from ext.ui.view import *
from discord.ext import commands
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ext.models import CodingBot


class Fun(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot: CodingBot) -> None:
        self.http = Http(bot.session)
        self.bot = bot
    
    @commands.command()
    async def rock(self, ctx: commands.Context[CodingBot], *, query: Optional[str] = None):
        async def get_rock(self):
            rock = await self.http.api["rock"]["random"]()
            name = rock["name"]
            desc = rock["desc"]
            image = rock["image"]
            rating = rock["rating"]
            embed = await self.bot.embed(
                title=f"🪨   {name}",
                url=image or "https://www.youtube.com/watch?v=o-YBDTqX_ZU",
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

        embed = discord.Embed(title=meme_name, description=f"Meme by {meme_poster} from subreddit {meme_sub}")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.set_image(url=meme_url)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="joke")
    async def joke(self, ctx: commands.Context[CodingBot]):
        response = await self.http.api["some-random-api"]["joke"]()
        json = await response.json()

        joke = json['joke']

        embed = discord.Embed(title="He're a joke", description=joke)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

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
        response = await self.http.api["some-random-api"]["bottoken"]()
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

        response = await self.http.api["some-random-api"]["animal"](animal)
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
        response = await self.http.api["some-random-api"]["binary-encode"](string)
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
        response = await self.http.api["some-random-api"]["binary-decode"](binary)
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

        response = await self.http.api["some-random-api"]["lyrics"](query)
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
        
    @commands.hybrid_command(name="reverse")
    async def reverse(self, ctx: commands.Context, *, text: str):
        embed = discord.Embed(title=f"Reversed Text", description=f"{text[::-1]}", color=discord.Color.random())
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot: CodingBot):
    await bot.add_cog(Fun(bot))
    