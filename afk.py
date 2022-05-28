import random
import aiosqlite
import discord
import time
from discord.ext import commands



class Afk(commands.Cog):
    def __init__(self,bot,db):
        self.bot = bot
        self.db=db
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded afk.py")
        self.db=await aiosqlite.connect("database/afk.db")
        await self.db.execute("""CREATE TABLE IF NOT EXISTS afk(
            memid INTEGER,
            memname TEXT,
            memres TEXT,
            afktime INTEGER
        )""")
    
    @commands.hybrid_command(name="afk",aliases=["afk-set","set-afk"],help="""Sets your afk""")
    @commands.has_role(795145820210462771) # "staff" role
    @commands.cooldown(1,10,commands.BucketType.member)
    async def afk(self,ctx,*,reason:str="AFK"):
        member=ctx.author
        on_pat_staff=member.guild.get_role(726441123966484600)
        try:
            await member.remove_roles(on_pat_staff)
        except Exception as e:
            print(e)
            
        cur=await self.db.execute("SELECT memres FROM afk WHERE memid=?",(member.id,))
        res=await cur.fetchone()
        if not res:
            await self.db.execute("INSERT INTO afk VALUES(?,?,?,?)",(member.id,member.display_name,reason,int(time.time())))
            await self.db.commit()
            try:
                await member.edit(nick=f"[AFK] {member.display_name}")
            except: pass
            emoji=random.choice(['⚪','🔴','🟤','🟣','🟢','🟡','🟠','🔵'])
            em=discord.Embed(
                title=" ",
                description=f"{emoji} I set your AFK: {reason}",
                color=discord.Color.blue()
            )
            await ctx.reply(embed=em)
            await self.db.commit()
        elif res:
            em=discord.Embed(
                title=" ",
                description=" You are already AFK",
                color=discord.Color.brand_red()
            )
            await ctx.reply(embed=em,ephemeral=True)
    
    @commands.Cog.listener()
    async def on_message(self,msg):
        if msg.author.bot:
            return
        if msg.guild is None:
            return
        elif msg.guild.id==681882711945641997:
            cur=await self.db.execute("SELECT memname FROM afk WHERE memid=?",(msg.author.id,))
            name=await cur.fetchone()
            if name:
                cur=await self.db.execute("SELECT afktime FROM afk WHERE memid=?",(msg.author.id,))
                trs=await cur.fetchone()
                tp=int(time.time())-int(trs[0])
                if tp<random.randint(20,30):pass
                else:
                    await self.db.execute("DELETE FROM afk WHERE memid=?",(msg.author.id,))
                    await self.db.commit()
                    try:
                        await msg.author.edit(nick=f"{name[0]}")
                    except: pass
                    on_pat_staff=msg.guild.get_role(726441123966484600)
                    try:
                        await msg.author.add_roles(on_pat_staff)
                    except Exception as e:
                        print(e)
                    emoji=random.choice(['⚪','🔴','🟤','🟣','🟢','🟡','🟠','🔵'])
                    em=discord.Embed(
                        title=" ",
                        description=f"{emoji} I removed your AFK",
                        color=discord.Color.dark_gold()
                    )
                    await msg.reply(embed=em)
            
            else:
                if msg.mentions:
                    for i in msg.mentions:
                        cur=await self.db.execute("SELECT memres FROM afk WHERE memid=?",(i.id,))
                        res=await cur.fetchone()
                        if res:
                            emoji=random.choice(['⚪','🔴','🟤','🟣','🟢','🟡','🟠','🔵'])
                            cur=await self.db.execute("SELECT afktime FROM afk WHERE memid=?",(i.id,))
                            ti=await cur.fetchone()
                            em=discord.Embed(
                                title=" ",
                                description=f"{emoji} {i.mention} is AFK: {res[0]} (<t:{str(ti[0])}:R>)",
                                color=discord.Color.dark_blue()
                            )
                            await msg.reply(embed=em)
                            break
                        else:pass
                        

async def setup(bot):
    db=await aiosqlite.connect("database/afk.db")
    await bot.add_cog(Afk(bot,db))
