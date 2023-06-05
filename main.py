from __future__ import annotations

import os

from discord.ext import commands

from ext.models import CodingBot

if not os.path.exists("./database"):
    os.mkdir("./database")

bot = CodingBot()


@bot.before_invoke
async def before_invoke(ctx: commands.Context[CodingBot]):
    bot.processing_commands += 1


@bot.after_invoke
async def after_invoke(ctx: commands.Context[CodingBot]):
    bot.processing_commands -= 1


@bot.check
async def check_processing_commands(ctx: commands.Context[CodingBot]):
    await bot.wait_until_ready()
    return True


TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
