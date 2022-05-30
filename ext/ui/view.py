<<<<<<< HEAD
import time
=======
from __future__ import annotations
>>>>>>> 8c577249f0768eea1c8950b4d31d3a5912a83068

import discord
from discord import ui
from discord.ext import commands, tasks
from more_itertools import sliced


class Rocks(discord.ui.View):
    def __init__(self, *, cog, embed_gen, stars, embed):
        self.cog = cog
        self.embed_gen = embed_gen
        self.pages = [
            (embed, stars),
        ]
        self.page = 0
        super().__init__()
        for child in self.children:
            if child.custom_id == "stars_count":
                child.label = "⭐" * stars if stars else "o"

    @discord.ui.button(label="-", custom_id="stars_count")
    async def stars_hud(self, interaction, button):
        pass

    @discord.ui.button(label="<", custom_id="prev", disabled=True)
    async def prev_rock(self, interaction, button):
        print(f"{self.page}  {self.pages}")
        if self.page == 0:
            button.disabled = True
            return await interaction.response.edit_message(view=self)
        self.page -= 1
        data = self.pages[self.page * -1]
        self.stars = data[1]
        for child in self.children:
            if child.custom_id == "stars_count":
                child.label = "⭐" * self.stars if self.stars else "o"
            elif child.custom_id == "next":
                if self.page + 1 < len(self.pages):
                    child.Style = discord.ButtonStyle.gray
        return await interaction.response.edit_message(
            embed=data[0], view=self
        )

    @discord.ui.button(
        label=">", custom_id="next", style=discord.ButtonStyle.green
    )
    async def next_rock(self, interaction, button):
        if self.page + 1 == len(self.pages):
            button.Style = discord.ButtonStyle.green
            await self.gen()
        self.page += 1
        print(f"{self.page}  {self.pages}")
        data = self.pages[self.page]
        self.stars = data[1]
        for child in self.children:
            print("====")
            print(child.custom_id)
            if child.custom_id == "stars_count":
                child.label = "⭐" * self.stars if self.stars else "o"
            elif child.custom_id == "prev":
                child.disabled = False
        await interaction.response.edit_message(embed=data[0], view=self)

    async def gen(self):
        self.pages.append(await self.embed_gen(self.cog))


class Piston(discord.ui.View):
    def __init__(self, cog, code, lang, msg):
        self.code = code
        self.lang = lang
        self.cog = cog
        self.timestamp = int(time.time())
        self.isCompiled = False
        self.output = []
        self.msg = msg
        self.page = 0
        super().__init__()
        self.timer.start()
        self.get_code_out.start()
        # asyncio.run(get_code_out())

    @tasks.loop(seconds=1, count=30)
    async def timer(self):
        if self.isCompiled:
            self.timer.cancel()
            return
        await self.msg.edit(
            embed=await self.cog.bot.embed(
                title="compiling **[** {} **]**".format(
                    int(time.time()) - self.timestamp
                )
            )
        )

    @tasks.loop(seconds=1, count=1)
    async def get_code_out(self):
        self.res = await self.cog.session.executeCode(self.lang, self.code)
        self.isCompiled = True
        self.timer.cancel()
        if "message" in self.res:
            return await self.msg.edit(
                embed=await self.cog.bot.embed(
                    title=" ",
                    description="```ansi\n[1;31m{}\n```".format(
                        self.res["message"]
                    ),
                )
            )
        lines = self.res["output"].split("\n")
        output = []
        for line in lines:
            if len(line) > 500:
                output.extend(sliced(line, 500))
            else:
                if len(output) > 0:
                    if len(output[-1].split("\n")) > 15:
                        output.append(line + "\n")
                    else:
                        output[-1] += line + "\n"
                else:
                    output.append(line + "\n")
        self.output = output
        self.ran = self.res["ran"]
        self.isCompiled = True
        for child in self.children:
            if child.custom_id == "info":
                if self.ran:
                    child.style = discord.ButtonStyle.green
                    child.label = f"ran '{self.lang}' code  |  {int(time.time()) - self.timestamp}s"
                else:
                    child.style = discord.ButtonStyle.red
                    child.label = f"failed to run '{self.lang}' code  |  {int(time.time()) - self.timestamp}s"
        await self.msg.edit(
            embed=await self.cog.bot.embed(
                title=" ", description=f"```{self.lang}\n{output[0]}\n```"
            ),
            view=self,
        )

    @discord.ui.button(label="<", custom_id="prev", disabled=True)
    async def _prev(self, interaction, button):
        if self.page == 0:
            button.disabled = True
            return await interaction.response.edit_message(view=self)
        self.page -= 1
        for child in self.children:
            if child.custom_id == "next":
                child.disabled = False
        return await interaction.response.edit_message(
            embed=await self.cog.bot.embed(
                title=" ",
                description=f"```{self.lang}\n{self.output[self.page]}\n```",
            ),
            view=self,
        )

    @discord.ui.button(
        label="...",
        custom_id="info",
        style=discord.ButtonStyle.gray,
        disabled=True,
    )
    async def _info(self, interaction, button):
        pass

    @discord.ui.button(
        label=">", custom_id="next", style=discord.ButtonStyle.green
    )
    async def _next(self, interaction, button):
        if self.page + 1 == len(self.output):
            button.disabled = True
            return await interaction.response.edit_message(view=self)
        self.page += 1
        for child in self.children:
            if child.custom_id == "prev":
                child.disabled = False
        await interaction.response.edit_message(
            embed=await self.cog.bot.embed(
                title=" ",
                description=f"```{self.lang}\n{self.output[self.page]}\n```",
            ),
            view=self,
        )


from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ext.models import CodingBot
    from typing_extensions import Self


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
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        if self.message:
            return await self.message.delete()

    @ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def confirm(
        self,
        interaction: discord.Interaction,
<<<<<<< HEAD
        button: discord.Button
=======
        button: discord.ui.Button[Self],
>>>>>>> 8c577249f0768eea1c8950b4d31d3a5912a83068
    ) -> None:
        self.confirmed = True
        if interaction.message:
            await interaction.message.delete()
        else:
            await interaction.delete_original_message()
        self.stop()

    @ui.button(label='No', style=discord.ButtonStyle.red)
    async def cancel(
        self,
        interaction: discord.Interaction,
<<<<<<< HEAD
        button: discord.Button
=======
        button: discord.ui.Button[Self],
>>>>>>> 8c577249f0768eea1c8950b4d31d3a5912a83068
    ) -> None:
        if interaction.message:
            await interaction.message.delete()
        else:
<<<<<<< HEAD
            interaction.delete_original_message()
        self.stop()
=======
            await interaction.delete_original_message()
        self.stop()
>>>>>>> 8c577249f0768eea1c8950b4d31d3a5912a83068
