from typing import Optional
import discord
from discord import ui
from discord.ext import commands

class ConfirmButton(ui.View):
    def __init__(self, ctx: commands.Context) -> None:
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
        button: discord.Button
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
        button: discord.Button
    ) -> None:
        if interaction.message:
            await interaction.message.delete()
        else:
            await interaction.delete_original_message()
        self.stop()