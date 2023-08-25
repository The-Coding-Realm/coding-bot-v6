import typing
import aiohttp
from ext.consts import MODMAIL_CHANNEL_ID, MODMAIL_WEBHOOK_URL
from discord.ext import commands
import discord
from ext.ui.view import YesNoView
import os


class ModMail(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current_modmail = {}
        self.opposite_current_modmail = {}
        self.channel: typing.Optional[discord.TextChannel] = None

    @commands.hybrid_command()
    async def close(self, ctx):
        if not ctx.guild:
            if ctx.author in self.current_modmail:
                thread = self.current_modmail[ctx.author]
                await thread.edit(locked=True)
                self.current_modmail.pop(ctx.author)
                self.opposite_current_modmail.pop(thread)
                await ctx.send("Your modmail ticket has successfully closed!")
        elif ctx.channel in self.opposite_current_modmail:
            member = self.opposite_current_modmail[ctx.channel]
            view = YesNoView(
                yes_message="Your modmail ticket has successfully closed!",
                no_message="Aborted.",
            )
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
        if (
            not self.channel
        ):  # I was unsure if getting the channel in the __init__ is wise
            self.channel = self.bot.get_channel(MODMAIL_CHANNEL_ID)

        if message.author.bot or message.content.startswith(self.bot.command_prefix):
            return

        if not message.guild:
            if message.author not in self.current_modmail:
                view = YesNoView(
                    yes_message="Your modmail ticket has been successfully created!",
                    no_message="Aborted.",
                )
                await message.author.send(
                    "Do you want to create a modmail ticket?", view=view
                )
                await view.wait()
                if view.yes:
                    msg_sent = await self.channel.send(
                        message.content,
                        files=message.attachments,
                        allowed_mentions=discord.AllowedMentions(
                            users=False, everyone=False, roles=False
                        ),
                    )
                    thread = await self.channel.create_thread(
                        name=f"{message.author.name} vs mods", message=msg_sent
                    )
                    self.current_modmail[message.author] = thread
                    self.opposite_current_modmail[thread] = message.author
            else:
                thread = self.current_modmail[message.author]
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(
                        MODMAIL_WEBHOOK_URL, session=session
                    )
                    await webhook.send(
                        content=mesage.content,
                        avatar_url=message.author.display_avatar.url,
                        files=message.attachments,
                        allowed_mentions=discord.AllowedMentions(
                            users=False, everyone=False, roles=False
                        ),
                        thread=thread,
                    )
                    await message.add_reaction("✅")
        elif message.channel in self.opposite_current_modmail:
            member = self.opposite_current_modmail[message.channel]
            await member.send("⚒️ staff: " + message.content, files=message.attachments)


async def setup(bot):
    await bot.add_cog(ModMail(bot))
