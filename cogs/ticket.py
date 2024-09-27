import discord
from discord.ext import commands

from ext.ui.view import CreateButton, CloseButton, TrashButton

class TicketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener(name = "on_ready")
    async def before_ready(self):
        self.bot.add_view(CreateButton())
        self.bot.add_view(CloseButton())
        self.bot.add_view(TrashButton())
        await self.bot.change_presence(activity=discord.Activity(type = discord.ActivityType.listening, name = "Doghouse Game's Heart 😳"))
        print(f"Logged in as: {self.bot.user.name}")
    
    @commands.command(name="ticket")
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx):
        await ctx.send(
            embed = discord.Embed(
                description="🎫 **Click  on the button below to create a ticket**\nIf you need any help regarding punishments, roles, or you just have a general question, feel free to create a ticket and a staff member will get to you shortly!\nOpening a ticket without a valid reason will get you warned/blacklisted.\n\n__**Do not open support tickets for Coding Help. Doing so will get you warned.**__",
                color = 0x8b6ffc
            ),
            view = CreateButton()
        )

async def setup(bot):
    await bot.add_cog(TicketCog(bot))