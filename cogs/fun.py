import discord
from discord.ext import commands

class Fun(commands.Cog, command_attrs=dict(hidden=False)):

    hidden = False
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="meme")
    async def meme(self, ctx: commands.Context):
        response = await self.bot.session.get("https://meme-api.herokuapp.com/gimme")
        meme_json = await response.json()

        meme_url = meme_json['url']
        meme_name = meme_json['title']
        meme_poster = meme_json['author']
        meme_sub = meme_json['subreddit']

        embed = discord.Embed(title = meme_name, description=f"Meme by {meme_poster} from subreddit {meme_sub}")
        embed.set_image(url=meme_url)

        await ctx.send(embed=embed)

    # DO YOUR COMMANDS HERE I HAVE NOT ENOUGH CREATIVITY TO THINK ABOUT THEM KEKW

async def setup(bot):
    await bot.add_cog(Fun(bot))
    