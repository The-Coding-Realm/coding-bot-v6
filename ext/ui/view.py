from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

import discord
from discord import ui
from discord.ext import commands, tasks
import asyncio
from more_itertools import sliced
from ext.consts import TICKET_REPO, OPEN_TICKET_CATEGORY, CLOSED_TICKET_CATEGORY, TICKET_HANDLER_ROLE_ID, TICKET_LOG_CHANNEL
from ext.helpers import get_transcript, upload


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



# ------------------ TICKET VIEWS ---------------------------


class ReasonModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Ticket Reason", timeout=None)

        self.add_item(
            discord.ui.TextInput(
                label="Reason",
                placeholder="Enter Reason",
                style=discord.TextStyle.short,
                default="No reason provided",
                required=True,
            )
        )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        reason = self.children[0].value

        await interaction.response.defer(ephemeral=True)
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=OPEN_TICKET_CATEGORY)
        for ch in category.text_channels:
            if ch.topic == f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!":
                await interaction.followup.send("You already have a ticket in {0}".format(ch.mention), ephemeral=True)
                return

        r1 : discord.Role = interaction.guild.get_role(TICKET_HANDLER_ROLE_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages = True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await category.create_text_channel(
            name=str(interaction.user),
            topic=f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!",
            overwrites=overwrites
        )
        i_msg = await channel.send(
            embed=discord.Embed(
                title="Ticket Created!",
                description="Don't ping a staff member, they will be here soon.",
                color = discord.Color.green()
            ).add_field(name = "📖 Reason", value = reason),
            view = CloseButton()
        )
        await i_msg.pin()
        await interaction.followup.send(
            embed= discord.Embed(
                description = "Created your ticket in {0}".format(channel.mention),
                color = discord.Color.blurple()
            ),
            ephemeral=True
        )

        log_channel = interaction.guild.get_channel(TICKET_LOG_CHANNEL)
        ticket_id = int(time.time())
        embed = discord.Embed(
            title = "Ticket Created",
            color = 0xe5ffb8
        ).add_field(
            name = "🆔 Ticket ID",
            value = str(ticket_id),
            inline = True
        ).add_field(
            name = "📬 Opened By",
            value = f"{interaction.user.mention}",
            inline = True
        ).add_field(
            name = "📪 Closed By",
            value = f"Not closed yet",
            inline = True
        ).add_field(
            name = "📖 Reason",
            value = f"{reason}",
            inline = True
        ).add_field(
            name = "🕑 Opened at",
            value = f"<t:{ticket_id}>",
            inline = True
        ).add_field(
            name = "🕑 Closed at",
            value = f"Not closed yet",
            inline = True
        ).set_author(name = interaction.user.name, icon_url= interaction.user.avatar.url)

        v = ui.View()
        btn = ui.Button(label = "Open", url = i_msg.jump_url)
        v.add_item(btn)

        msg = await log_channel.send(
            content = f"{r1.mention}",
            embed = embed,
            view = v
        )
        await interaction.client.conn.insert_record(
            "tickets",
            table = "tickets",
            columns = ("message_id", "ticket_id", "opened_by", "closed_by", "opened_at", "closed_at", "reason"),
            values = (
                msg.id,
                ticket_id,
                interaction.user.id,
                0,
                ticket_id,
                0,
                reason
            )
        )
        


class CreateButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(style=discord.ButtonStyle.blurple, emoji="🎫",custom_id="ticketopen")
    async def ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ReasonModal())
        


class CloseButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="Close the ticket",style=discord.ButtonStyle.red,custom_id="closeticket",emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)

        await interaction.channel.send("Closing this ticket!", delete_after = 10)


        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id = CLOSED_TICKET_CATEGORY)
        r1 : discord.Role = interaction.guild.get_role(TICKET_HANDLER_ROLE_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        await interaction.channel.edit(category=category, overwrites=overwrites)
        member = interaction.guild.get_member(int(interaction.channel.topic.split(" ")[0]))
        await get_transcript(member=member, channel=interaction.channel)
        await interaction.channel.send(
            embed= discord.Embed(
                description="Ticket Closed!",
                color = discord.Color.red()
            ),
            view = TrashButton()
        )
        data = (await interaction.client.conn.select_record(
            "tickets",
            arguments = ("ticket_id", "message_id", "reason"),
            table = "tickets",
            where = ("opened_by", ),
            values = (member.id, )
        ))[-1]

        ticket_id = data.ticket_id
        message_id = data.message_id
        reason = data.reason

        await interaction.channel.edit(topic = f"{ticket_id} DO NOT CHANGE THE TOPIC")
        file_name = upload(f'storage/tickets/{member.id}.html',member.name, ticket_id)
        link = f"https://tcrtickets.vercel.app/?id={file_name}"

        log_channel = interaction.guild.get_channel(TICKET_LOG_CHANNEL)
        msg = await log_channel.fetch_message(message_id)

        embed = discord.Embed(
            title = "Ticket Closed",
            color = 0xffb8c4
        ).add_field(
            name = "🆔 Ticket ID",
            value = str(ticket_id),
            inline = True
        ).add_field(
            name = "📬 Opened By",
            value = f"{member.mention}",
            inline = True
        ).add_field(
            name = "📪 Closed By",
            value = f"{interaction.user.mention}",
            inline = True
        ).add_field(
            name = "📖 Reason",
            value = f"{reason}",
            inline = True
        ).add_field(
            name = "🕑 Opened at",
            value = f"<t:{ticket_id}>",
            inline = True
        ).add_field(
            name = "🕑 Closed at",
            value = f"<t:{int(time.time())}>",
            inline = True
        ).set_author(name = member.name, icon_url= member.avatar.url)
        v=ui.View()
        btn = ui.Button(url = link, label = "Transcript")
        v.add_item(btn)

        await msg.edit(content = None, embeds = [embed], view = v)
        try:
            await member.send(embed = embed, view = v)
        except: pass #type: ignore


class TrashButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Delete the ticket", style=discord.ButtonStyle.red, emoji="🚮", custom_id="trash")
    async def trash(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await interaction.channel.send("Deleting the ticket in 3 seconds")
        await asyncio.sleep(3)
        ticket_id = int(interaction.channel.topic.split(" ")[0])

        await interaction.channel.delete()
        await interaction.client.conn.delete_record(
            "tickets",
            table = "tickets",
            where = ("ticket_id",),
            values = (ticket_id,)
        )