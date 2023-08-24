import typing

from ext.consts import MODMAIL_CHANNEL_ID
from discord.ext import commands
import discord

class YesNoView(discord.ui.View):  # class should be moved to a utils class probably
    def __init__(self, *, yes_message, no_message):
        self.yes = None
        self.yes_message = yes_message
        self.no_message = no_message

    @discord.ui.button(emoji="✅", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction, button):
        await interaction.response.send_message(self.yes_message)
        self.yes = True
        self.stop()

    @discord.ui.button(emoji="🚫", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction, button):
        await interaction.response.send_message(self.no_message)
        self.yes = False
        self.stop()

class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_modmail = {}
        self.opposite_current_modmail = {}
        self.channel: typing.Optional[discord.TextChannel] = None

    @commands.command()
    async def close(self, ctx):
        if not ctx.guild:
            if ctx.author in self.current_modmail:
                thread = self.current_modmail[ctx.author]
                await thread.edit(locked=True)
                self.current_modmail.pop(ctx.author)
                self.opposite_current_modmail.pop(thread)
        elif ctx.channel in self.opposite_current_modmail:
            member = self.opposite_current_modmail[ctx.channel]
            view = YesNoView(yes_message="Your modmail ticket has successfully closed!", no_message="Aborted.")
            await member.send(content="Do you want to close the ticket?", view=view)
            await view.wait()
            if view.yes:
                await ctx.channel.edit(locked=True)
                self.current_modmail.pop(member)
                self.opposite_current_modmail.pop(ctx.channel)
            else:
                await ctx.channel.send("Member refused to close the ticket.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.channel:  # I was unsure if getting the channel in the __init__ is wise
            self.channel = self.bot.get_channel(MODMAIL_CHANNEL_ID)

        if message.author.bot:
            return

        if not message.guild:
            if message.author not in self.current_modmail:
                view = YesNoView(yes_message="Your modmail ticket has been successfully created!", no_message="Aborted.")
                await message.author.send("Do you want to create a modmail ticket?", view=view)
                await view.wait()
                if view.yes:
                    message = await self.channel.send(message.content, files=message.files, allowed_mentions=discord.AllowedMentions(users=False, everyone=False, roles=False))
                    thread = await self.channel.create_thread(name=f"{message.author.name} vs mods", message=message)
                    self.current_modmail[message.author] = thread
                    self.opposite_current_modmail[thread] = message.author
            else:
                webhook = await ctx.channel.create_webhook(name=message.author.name)
                thread = self.current_modmail[message.author]
                await webhook.send(content=message.content, avatar_url=message.author.display_avatar.url, files=message.files, allowed_mentions=discord.AllowedMentions(users=False, everyone=False, roles=False), thread=thread)
        elif message.channel in self.opposite_current_modmail:
            member = self.opposite_current_modmail[self.channel]
            await member.send("⚒️ staff: "+message.content, files=message.files)

async def setup(bot: CodingBot):
    await bot.add_cog(ModMail(bot))
