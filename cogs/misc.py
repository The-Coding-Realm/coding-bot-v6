import random
import time

import discord
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="afk", aliases = ["afk-set", "set-afk"], help = "Sets your afk")

    @commands.cooldown(1, 10, commands.BucketType.member)
    async def afk(self, ctx: commands.Context, *, reason: str = None):
        if not reason:
            reason = "AFK"
        member = ctx.author
        staff_role = ctx.guild.get_role(795145820210462771)
        on_pat_staff = member.guild.get_role(726441123966484600) # "on_patrol_staff" role
        if staff_role in member.roles:
            try:
                await member.remove_roles(on_pat_staff)
            except (discord.Forbidden, discord.HTTPException):
                pass
        record = await self.bot.conn.select_record(
                'afk',
                table='afk',
                arguments=['afk_time', 'reason'],
                where=['user_id'],
                values=[member.id]
            )
        if not record:
            await self.bot.conn.insert_record(
                'afk',
                table='afk',
                values=(member.id, reason, int(ctx.message.created_at.timestamp())),
                columns=['user_id', 'reason', 'afk_time']
            )
            try:
                await member.edit(nick=f"[AFK] {member.display_name}")
            except:
                pass
            emoji = random.choice(['⚪','🔴','🟤','🟣','🟢','🟡','🟠','🔵'])
            embed = discord.Embed(
                description=f"{emoji} I set your AFK: {reason}",
                color=discord.Color.blue()
            )
            await ctx.reply(embed=embed)
        else:
            embed = discord.Embed(
                description=" You are already AFK",
                color=discord.Color.brand_red()
            )
            await ctx.reply(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Misc(bot))