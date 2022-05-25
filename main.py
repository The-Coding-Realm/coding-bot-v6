import os
from ext.models import CodingBot


bot = CodingBot()


@bot.before_invoke
async def before_invoke(ctx):
    bot.processing_commands += 1


@bot.after_invoke
async def after_invoke(ctx):
    bot.processing_commands -= 1


TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)