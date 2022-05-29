import discord
from discord.ext import commands

"""
Luz's Commit - Ban word (Line ... to ...)
Feel free to make the better changes to this ban word censorship
Because I hardcode this thing lol
"""

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bannedwords = [] # Place all of em here

    @commands.Cog.listener()
    async def on_message(self, message):
        for word in self.bannedwords:
            if word in message.content.lower():
                await message.delete()

    @commands.hybrid_command(name="banword")
    async def banword(self, ctx: commands.Context, *, word: str):
        self.bannedwords.append(word)
        await ctx.send(f"Successfully added {word} to the banned word list")

    @commands.hybrid_command(name="unbanword")
    async def unbanword(self, ctx: commands.Context, *, word: str):
        self.bannedwords.remove(word)
        await ctx.send(f"Successfully removed {word} to the banned word list")

    # TO DO : Make a command that will show banned word list

async def setup(bot):
    await bot.add_cog(Automod(bot))
    