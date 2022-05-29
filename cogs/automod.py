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

async def setup(bot):
    await bot.add_cog(Automod(bot))
    