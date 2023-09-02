import typing
from ext.consts import MODMAIL_CHANNEL_ID, MODMAIL_ROLE_ID, MODMAIL_CLOSED, MODMAIL_OPEN
from discord.ext import commands
import discord
from ext.ui.view import YesNoView

def none_if_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None

    return wrapper

class ModMail(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = [] # [{user: discord.Member, thread: discord.Thread}]
        self.channel: typing.Optional[discord.ForumChannel] = None

    @none_if_error
    def get_thread(self, user) -> discord.Thread | None:
        return [i['thread'] for i in self.sessions if i['user'] == user][0]

    @none_if_error
    def get_user(self, thread) -> discord.Member | discord.User | None:
        return [i['user'] for i in self.sessions if i['thread'] == thread][0]

    async def send_webhook_message(
            self, 
            message: discord.Message, 
            thread: discord.Thread
            ):
        webhook = (await thread.parent.webhooks())[0]
        await webhook.send(
            username=message.author.name,
            content=message.content,
            avatar_url=message.author.display_avatar.url,
            files=message.attachments,
            allowed_mentions=discord.AllowedMentions(
                users=False, everyone=False, roles=False
            ),
            thread=thread,
        )
        await message.add_reaction("✅")

    async def close_thread(self, thread: discord.Thread):
        await thread.add_tags(thread.parent.get_tag(MODMAIL_CLOSED))
        await thread.remove_tags(thread.parent.get_tag(MODMAIL_OPEN))
        await thread.edit(locked=True, archived=True)
        self.sessions.remove({'user': self.get_user(thread), 'thread': thread})

    @commands.hybrid_command()
    async def close(self, ctx: commands.Context):
        if not ctx.guild and (thread := self.get_thread(ctx.author)):
            await thread.send("This ticket has been closed by the user.")
            await self.close_thread(thread)
            await ctx.send("Your modmail ticket has successfully closed!")

        elif member := self.get_user(ctx.channel):
            view = YesNoView(
                yes_message="Your modmail ticket has successfully closed!",
                no_message="Aborted.",
            )
            await member.send(content="Do you want to close the ticket?", view=view)
            await view.wait()
            if view.yes:
                await self.close_thread(ctx.channel)
            else:
                await ctx.channel.send("Member refused to close the ticket.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.channel:  
            self.channel: discord.ForumChannel = self.bot.get_channel(MODMAIL_CHANNEL_ID)

        if message.author.bot or message.content.startswith(self.bot.command_prefix[0]):
            return

        if not message.guild:
            if not (thread := self.get_thread(message.author)):
                view = YesNoView(
                    yes_message="Your modmail ticket has been successfully created!",
                    no_message="Aborted.",
                )
                await message.author.send(
                    "Do you want to create a modmail ticket?", view=view
                )
                await view.wait()
                if view.yes:
                    thread, _ = await self.channel.create_thread(
                        name=f"Mods vs @{message.author.name}", 
                        content="New ModMail ticket created by "\
                            f"{message.author.mention}, <@&{MODMAIL_ROLE_ID}>",
                        files=message.attachments,
                        applied_tags=[self.channel.get_tag(MODMAIL_OPEN)],
                    )
                    await self.send_webhook_message(message, thread)

                    self.sessions.append({'user': message.author, 'thread': thread})
            else:
                await self.send_webhook_message(message, thread)

        elif member := self.get_user(message.channel):
            await member.send(
                f"⚒️ @{message.author.name}: " + message.content, 
                files=message.attachments
                )


async def setup(bot):
    await bot.add_cog(ModMail(bot))
