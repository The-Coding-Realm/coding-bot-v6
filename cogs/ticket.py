import discord
from discord.ext import commands

import asyncio
from discord.ui import Button, button, View, Modal
from ext.consts import TICKET_REPO, OPEN_TICKET_CATEGORY, CLOSED_TICKET_CATEGORY, TICKET_HANDLER_ROLE_ID, TICKET_LOG_CHANNEL

import chat_exporter
from github import Github

import time
import os

# GET TRANSCRIPT
async def get_transcript(member: discord.Member, channel: discord.TextChannel):
    export = await chat_exporter.export(channel=channel)
    file_name=f"{member.id}.html"
    with open(f"storage/tickets/{file_name}", "w", encoding="utf-8") as f:
        f.write(export)

# UPLOAD TO GITHUB
def upload(file_path: str, member_name: str, file_name: str):
    github = Github(os.getenv("GITHUB_TOKEN"))
    repo = github.get_repo(TICKET_REPO)
    repo.create_file(
        path=f"templates/tickets/{file_name}.html",
        message="Ticket Log for {0}".format(member_name),
        branch="main",
        content=open(f"{file_path}","r",encoding="utf-8").read()
    )
    os.remove(file_path)

    return file_name

class ReasonModal(Modal):
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

        v = View()
        btn = Button(label = "Open", url = i_msg.jump_url)
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
        


class CreateButton(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @button(style=discord.ButtonStyle.blurple, emoji="🎫",custom_id="ticketopen")
    async def ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ReasonModal())
        


class CloseButton(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @button(label="Close the ticket",style=discord.ButtonStyle.red,custom_id="closeticket",emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: Button):
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
        await get_transcript(member=member, channel=interaction.channel)
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
        v=View()
        btn = Button(url = link, label = "Transcript")
        v.add_item(btn)

        await msg.edit(content = None, embeds = [embed], view = v)
        try:
            await member.send(embed = embed, view = v)
        except: pass #type: ignore


class TrashButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Delete the ticket", style=discord.ButtonStyle.red, emoji="🚮", custom_id="trash")
    async def trash(self, interaction: discord.Interaction, button: Button):
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
    @commands.has_role(795136568805294097)
    async def ticket(self, ctx):
        await ctx.send(
            embed = discord.Embed(
                description="🎫 **Click on the button below to create a ticket**\nIf you need any help regarding punishments, roles, or you just have a general question, feel free to create a ticket and a staff member will get to you shortly!\nOpening a ticket without a valid reason will get you warned/blacklisted.\n\n__**Do not open support tickets for Coding Help. Doing so will get you warned.**__",
                color = 0x8b6ffc
            ),
            view = CreateButton()
        )

async def setup(bot):
    await bot.add_cog(TicketCog(bot))