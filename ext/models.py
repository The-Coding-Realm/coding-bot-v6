import datetime as dt
from dataclasses import dataclass, field
import os
from typing import Any, Dict

import aiosqlite
import discord
from discord.ext import commands
from DiscordUtils import InviteTracker

from .consts import INTENTS
from .helpers import WelcomeBanner, log_error

@dataclass(slots=True, kw_only=True, repr=True)
class Cache:
    """
    A Cache for storing guild information

    Attributes
    ----------
    guild_id : int
        The ID of the guild
    channel_id : int
        The ID of the channel
    """
    prefixes: list
    commands: set = field(default_factory=set)

class Database:
    """
    Database class for storing opened connections

    Attributes
    ----------
    conn : Dict[str, aiosqlite.Connection]
        A dictionary of connections
    is_closed : bool
        Whether the connections are closed
    """
    def __init__(self):
        self.conn: Dict[str, aiosqlite.Connection] = {}
        self.is_closed: bool = False
        
    def __getattr__(self, __name: str) -> Any:
        if __name in self.conn:
            return self.conn[__name]
        return super().__getattribute__(__name)

    async def __aenter__(self) -> "Database":
        self.conn["config"] = await aiosqlite.connect('./database/config.db')
        await self.init_dbs()
        return self

    async def init_dbs(self):
        PREFIX_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS prefixconf (
                           id BIGINT,
                           prefix TEXT
                        );
                        """
        COMMANDS_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS commandconf (
                            id BIGINT,
                            command TEXT UNIQUE
                        );
                        """
        async with self.cursor('config') as cursor:
            await cursor.execute(PREFIX_CONFIG_SCHEMA)
            await cursor.execute(COMMANDS_CONFIG_SCHEMA)
            await self.config.commit()

    async def __aexit__(self, *args: Any) -> None:
        await self.commit()
        await self.close()

    def cursor(self, conn: str) -> aiosqlite.Cursor:
        if hasattr(self, conn):
            return getattr(self, conn).cursor()
    
    def __repr__(self) -> str:
        return f"<Database: {self.conn}>"

    @property
    def closed(self):
        return self.is_closed
    
    async def commit(self) -> None:
        for conn in self.conn.values():
            await conn.commit()

    async def close(self) -> None:
        self.is_closed = True
        for conn in self.conn.values():
            await conn.close()

class CodingBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=[','],
            intents=INTENTS,
            case_insensitive=True
        )
        self.conn: Database = None
        self.tracker = InviteTracker(self)
        self.default_prefixes = [',']
        self.welcomer = WelcomeBanner(self)
        self.processing_commands = 0

    async def setup_hook(self) -> None:
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')

    async def start(self, token: str, reconnect: bool = True):
        async with Database() as self.conn:
            return await super().start(token, reconnect=reconnect)

    async def startup_task(self):
        await self.wait_until_ready()
        channel = self.get_channel(self.restart_channel)
        self.restart_channel = None
        embed = discord.Embed(title="I'm back online!")
        await channel.send(embed=embed)

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await self.tracker.cache_invites()
        print('Ready')

    async def on_invite_create(self, invite: discord.Invite) -> None:
        await self.tracker.update_invite_cache(invite)

    async def on_invite_delete(self, invite: discord.Invite) -> None:
        await self.tracker.remove_invite_cache(invite)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.tracker.update_guild_cache(guild)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.tracker.remove_guild_cache(guild)

    async def on_member_join(self, member: discord.Member) -> None:
        rules = member.guild.rules_channel
        if rules:
            rules = rules.mention
        else:
            rules = "No official rule channel set yet."
        embed = discord.Embed(
            title=f'Welcome to {member.guild.name}!',
            description=(
                f'Welcome {member.mention}, we\'re glad you joined! Before you get'
                ' started, here are some things to check out: \n**Read the Rules:'
                f'** {rules} \n**Get roles:** <#726074137168183356> and '
                '<#806909970482069556> \n**Want help? Read here:** '
                '<#799527165863395338> and <#754712400757784709>'),
            timestamp=dt.datetime.now(dt.timezone.utc)
        )
        file = await self.welcomer.construct_image(member=member)
        channel = member.guild.get_channel(743817386792058971)
        await channel.send(content=member.mention, file=file)
        verify_here = member.guild.get_channel(759220767711297566)
        await verify_here.send(
            f'Welcome {member.mention}! Follow the instructions in other channels to get verified. :)',                   
            embed=embed
        )

    async def on_error(self, event_method, *args, **kwargs):
        await log_error(self, event_method, *args, **kwargs)
