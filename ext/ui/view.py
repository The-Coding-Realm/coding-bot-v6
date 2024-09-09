from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

import discord
from discord import ui
from discord.ext import commands, tasks
from more_itertools import sliced

if TYPE_CHECKING:
    from typing_extensions import Self

    from ext.models import CodingBot


class Piston(discord.ui.View):
    def __init__(
        self,
        cog: commands.Cog,
        code: str,
        language: str,
        message: discord.Message,
        author: discord.Member,
    ) -> None:
        self.code = code
        self.lang = language
        self.cog = cog
        self.timestamp = int(time.time())
        self.is_compiled = False
        self.output = []
        self.msg = message
        self.author = author
        self.page = 0
        super().__init__()
        self.timer.start()
        self.get_code_out.start()
        # asyncio.run(get_code_out())

    @tasks.loop(seconds=1, count=30)
    async def timer(self):
        if self.is_compiled:
            self.timer.cancel()
            return
        await self.msg.edit(
            embed=self.cog.bot.embed(
                title=f"compiling **[** {int(time.time()) - self.timestamp} **]**"
            )
        )

    @tasks.loop(seconds=1, count=1)
    async def get_code_out(self):
        self.res = await self.cog.http.api["piston"]["execute"](self.lang, self.code)
        self.is_compiled = True
        self.timer.cancel()
        if "message" in self.res:
            return await self.msg.edit(
                embed=self.cog.bot.embed(
                    title=" ",
                    description="```ansi\n[1;31m{}\n```".format(self.res["message"]),
                )
            )
        lines = self.res["output"].split("\n")
        output = []
        for line in lines:
            if len(line) > 500:
                output.extend(sliced(line, 500))
            elif output:
                if len(output[-1].split("\n")) > 15:
                    output.append(line + "\n")
                else:
                    output[-1] += line + "\n"
            else:
                output.append(line + "\n")
        self.output = output
        self.ran = self.res["ran"]
        self.is_compiled = True
        for child in self.children:
            if child.custom_id == "info":
                if self.ran:
                    child.style = discord.ButtonStyle.green
                    child.label = (
                        f"ran '{self.lang}' code  |  "
                        f"{int(time.time()) - self.timestamp}s"
                    )
                else:
                    child.style = discord.ButtonStyle.red
                    child.label = (
                        f"failed to run '{self.lang}' code  |  "
                        f"{int(time.time()) - self.timestamp}s"
                    )
        await self.msg.edit(
            embed=self.cog.bot.embed(
                title=" ", description=f"```{self.lang}\n{output[0]}\n```"
            ),
            view=self,
        )

    @ui.button(label="<", custom_id="prev", disabled=True)
    async def _prev(self, interaction: discord.Interaction, button: discord.Button):
        if self.page == 0:
            button.disabled = True
            return await interaction.response.edit_message(view=self)
        self.page -= 1
        for child in self.children:
            if child.custom_id == "next":
                child.disabled = False
        return await interaction.response.edit_message(
            embed=self.cog.bot.embed(
                title=" ",
                description=f"```{self.lang}\n{self.output[self.page]}\n```",
            ),
            view=self,
        )

    @ui.button(
        label="...", custom_id="info", style=discord.ButtonStyle.gray, disabled=True
    )
    async def _info(self, interaction: discord.Interaction, button: discord.Button):
        pass

    @ui.button(label=">", custom_id="next", style=discord.ButtonStyle.green)
    async def _next(self, interaction: discord.Interaction, button: discord.Button):
        if self.page + 1 == len(self.output):
            button.disabled = True
            return await interaction.response.edit_message(view=self)
        self.page += 1
        for child in self.children:
            if child.custom_id == "prev":
                child.disabled = False
        try:
            await interaction.response.edit_message(
                embed=self.cog.bot.embed(
                    title=" ",
                    description=f"```{self.lang}\n{self.output[self.page]}\n```",
                ),
                view=self,
            )
        except IndexError:
            self.page -= 1
        return

    @ui.button(
        label="Delete", custom_id="delete", style=discord.ButtonStyle.danger, row=2
    )
    async def _delete(self, interaction: discord.Interaction, button: discord.Button):
        self.stop()
        await self.msg.delete()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author


class ConfirmButton(ui.View):
    if TYPE_CHECKING:
        message: discord.Message

    def __init__(self, ctx: commands.Context[CodingBot]) -> None:
        super().__init__(timeout=60)
        self.confirmed: Optional[bool] = None
        self.message: Optional[discord.Message] = None
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.ctx.author.id != interaction.user.id:
            await interaction.response.send_message(
                "This is not your button.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.message:
            return await self.message.delete()

    @ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[Self],
    ) -> None:
        self.confirmed = True
        if interaction.message:
            await interaction.message.delete()
        else:
            await interaction.delete_original_message()
        self.stop()

    @ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[Self],
    ) -> None:
        if interaction.message:
            await interaction.message.delete()
        else:
            await interaction.delete_original_message()
        self.stop()


class YesNoView(discord.ui.View):  # class should be moved to a utils class probably
    def __init__(self, *, yes_message, no_message):
        super().__init__()
        self.yes = None
        self.yes_message = yes_message
        self.no_message = no_message

    @discord.ui.button(emoji="✅", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction, button):
        await interaction.response.send_message(self.yes_message)
        self.yes = True
        self.stop()

    @discord.ui.button(emoji="⛔", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction, button):
        await interaction.response.send_message(self.no_message)
        self.yes = False
        self.stop()
