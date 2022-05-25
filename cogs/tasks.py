import random

import discord
from discord.ext import commands, tasks

class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.task.start()

    async def cog_load(self) -> None:
        await self.bot.wait_until_ready()
        self.status_change.start()

    @tasks.loop(minutes=2)
    async def status_change(self):

        statuses = ['over TCR', 'you', 'swas', '@everyone', 'general chat', 'discord', ',help', 'your mom',
                    'bob and shadow argue', 'swas simp for false', 'new members', 'the staff team', 'helpers', 'code',
                    'mass murders', 'karen be an idiot', 'a video', 'watches', 'bob', 'fight club', 'youtube',
                    'https://devbio.me/u/CodingBot', 'potatoes', 'simps', 'people', 'my server', 'humans destroy the world',
                    'AI take over the world', 'female bots 😳', 'dinosaurs', 'https://youtu.be/dQw4w9WgXcQ', 'idiots',
                    'the beginning of WWIII', 'verified bot tags with envy',
                    'Server Boosters (boost to get your name on here)', 'OG members', "dalek rising from the ashes",
                    'spongebob', 'turtles', 'SQUIRREL!!!', 'people get banned', 'por...k chops', 'my poggers discriminator',
                    'tux', 'linux overcome windows', 'bob get a gf', 'a documentary', 'Lexionas74 die inside']
        tcr = self.bot.get_guild(681882711945641997)
        if tcr:
            if tcr.get_role(795145820210462771):
                statuses.append(random.choice(tcr.get_role(795145820210462771).members).name)
            if tcr.get_role(737517726737629214):
                statuses.append(random.choice(tcr.get_role(737517726737629214).members).name + ' (Server Booster)')

        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=random.choice(
                statuses) + ' | ' + self.bot.default_prefixes[0] + 'help'))