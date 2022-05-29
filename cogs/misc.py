import random
import time

import discord
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="afk", aliases = ["afk-set", "set-afk"], help = "Sets your afk")
    @commands.has_role(795145820210462771) # "staff" role
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def afk(self, ctx: commands.Context, *, reason: str = None):
        if not reason:
            reason = "AFK"
        member = ctx.author
        on_pat_staff = member.guild.get_role(726441123966484600) # "on_patrol_staff" role
        try:
            await member.remove_roles(on_pat_staff)
        except:
            pass
        async with self.bot.conn.cursor('afk') as cursor:
            await cursor.execute("""SELECT reason FROM afk WHERE user_id=?""", (member.id,))
            if not cursor:
                await cursor.execute("INSERT INTO afk VALUES (?, ?, ?, ?)", (member.id, member.display_name, reason, int(time.time())))
                try:
                    await member.edit(nick=f"[AFK] {member.display_name}")
                except:
                    pass
                emoji=random.choice(['⚪','🔴','🟤','🟣','🟢','🟡','🟠','🔵'])
                em=discord.Embed(
                    description=f"{emoji} I set your AFK: {reason}",
                    color=discord.Color.blue()
                )
                await ctx.reply(embed=em)
            else:
                em=discord.Embed(
                    description=" You are already AFK",
                    color=discord.Color.brand_red()
                )
                await ctx.reply(embed=em,ephemeral=True)
        await self.bot.con.afk('afk').commit()

async def setup(bot):
    await bot.add_cog(Misc(bot))