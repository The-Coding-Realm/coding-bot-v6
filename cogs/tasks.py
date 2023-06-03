from __future__ import annotations

import datetime
import random

import discord
from discord.ext import commands, tasks
from typing import TYPE_CHECKING
from ext.consts import TCR_GUILD_ID

if TYPE_CHECKING:
    from ext.models import CodingBot


class TaskCog(commands.Cog, command_attrs=dict(hidden=True)):
    
    hidden = True
    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.status_change.start()
        self.remove_inactive_warns.start()

    @tasks.loop(minutes=2)
    async def status_change(self):

        statuses = ['over TCR', 'you', 'swas', '@everyone', 'general chat', 'discord', ',help', 'your mom',
                    'bob and shadow argue', 'swas simp for false', 'new members', 'the staff team', 'helpers', 'code',
                    'mass murders', 'karen be an idiot', 'a video', 'watches', 'bob', 'fight club', 'youtube',
                    'potatoes', 'simps', 'people', 'my server', 'humans destroy the world',
                    'AI take over the world', 'female bots 😳', 'dinosaurs', 'https://youtu.be/o-YBDTqX_ZU', 'idiots',
                    'the beginning of WWIII', 'verified bot tags with envy', 'Server Boosters (boost to get your name on here)',
                    'OG members', "dalek rising from the ashes", 'spongebob', 'turtles', 'SQUIRREL!!!', 'people get banned',
                    'por...k chops', 'my poggers discriminator', 'tux', 'linux overcome windows', 'bob get a gf', 'a documentary']
        tcr = self.bot.get_guild(681882711945641997)
        if tcr:
            if tcr.get_role(795145820210462771):
                statuses.append(random.choice(
                    tcr.get_role(795145820210462771).members).name)  # type: ignore
            if tcr.get_role(737517726737629214):
                statuses.append(random.choice(tcr.get_role(
                    737517726737629214).members).name + ' (Server Booster)')  # type: ignore

        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=random.choice(
                statuses) + ' | ' + self.bot.default_prefixes[0] + 'help'))

    @status_change.before_loop
    async def before_status_change(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info('Started task loop for Status Change')

    @tasks.loop(hours=24)
    async def remove_inactive_warns(self):
        await self.bot.wait_until_ready()

        records = await self.bot.conn.select_record(
            'warnings',
            arguments=('date','user_id'),
            table='warnings',
            where=('guild_id',),
            values=(TCR_GUILD_ID,)
        )
        now = datetime.datetime.utcnow().timestamp()
        if records:
            for record in records:
                if record.date + (60*60*24*31) < now:
                    await self.bot.conn.delete_record(
                        'warnings',
                        table='warnings',
                        where=('guild_id', 'user_id', 'date'),
                        values=(TCR_GUILD_ID, record.user_id, record.date)
                    )

    @remove_inactive_warns.before_loop
    async def before_remove_inactive_warns(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info('Started task loop for Remove Inactive Warns')

async def setup(bot: CodingBot):
    await bot.add_cog(TaskCog(bot))
