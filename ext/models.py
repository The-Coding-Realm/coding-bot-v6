from __future__ import annotations

import aiohttp
import datetime as dt
from dataclasses import dataclass, field
import os
from typing import Any, Dict, List, Mapping, Optional, Union, Tuple, Set, Iterable

import aiosqlite
import discord
from discord.ext import commands
from DiscordUtils import InviteTracker
from pytimeparse import parse

from .consts import (
    INTENTS,
    PREFIX_CONFIG_SCHEMA,
    COMMANDS_CONFIG_SCHEMA,
    WARNINGS_CONFIG_SCHEMA,
    AFK_CONFIG_SCHEMA,
    HELP_WARNINGS_CONFIG_SCHEMA,
    HELP_COMMAND
)
from .helpers import WelcomeBanner, log_error


class Record:
    __slots__ = ("arguments",)

    def __init__(self, arguments: Dict[str, Any]) -> None:
        self.arguments = arguments

    def __getitem__(self, __item: Union[str, int]) -> Any:
        if isinstance(__item, str):
            if __item in self.arguments:
                return self.arguments[__item]
            raise AttributeError(
                f'Dynamic object has no attribute \'{__item}\'')
        elif isinstance(__item, int):  # type: ignore
            return tuple(self.arguments.values())[__item]

    def __getattr__(self, __item: str):
        if __item in self.arguments:
            return self.arguments[__item]
        raise AttributeError(f"Dynamic object has no attribute '{__item}'")

    def __len__(self):
        return len(self.arguments.keys())

    def __repr__(self) -> str:
        argument = ", ".join(
            f"{key}={value}" for key, value in self.arguments.items()
        )
        return f"<Record: {argument}>"

    @classmethod
    def from_tuple(cls, arguments: Iterable[Any], tuple_: Iterable[Any]) -> Record:
        return cls(dict(zip(arguments, tuple_)))


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
    prefixes: List[str]
    commands: Set[str] = field(default_factory=set)


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
        self.conn["config"] = await aiosqlite.connect("./database/config.db")
        self.conn["warnings"] = await aiosqlite.connect(
            "./database/warnings.db"
        )
        self.conn["afk"] = await aiosqlite.connect("./database/afk.db")
        await self.init_dbs()
        return self

    async def init_dbs(self):
        async with self.cursor("config") as cursor:
            await cursor.execute(PREFIX_CONFIG_SCHEMA)
            await cursor.execute(COMMANDS_CONFIG_SCHEMA)

        async with self.cursor("warnings") as cursor:
            await cursor.execute(WARNINGS_CONFIG_SCHEMA)
            await cursor.execute(HELP_WARNINGS_CONFIG_SCHEMA)

        async with self.cursor("afk") as cursor:
            await cursor.execute(AFK_CONFIG_SCHEMA)

        await self.commit()

    async def __aexit__(self, *args: Any) -> None:
        await self.commit()
        await self.close()

    def cursor(self, conn: str) -> aiosqlite.Cursor:
        return getattr(self, conn).cursor()

    def __repr__(self) -> str:
        return f"<Database: {self.conn}>"

    async def select_record(self,
                            connection: str,
                            /,
                            *,
                            arguments: Tuple[str, ...],
                            table: str,
                            where: Optional[Tuple[str, ...]] = None,
                            values: Optional[Tuple[Any, ...]] = None,
                            extras: Optional[List[str]] = None,
                            ) -> Optional[List[Record]]:
        statement = """SELECT {} FROM {}""".format(
            ", ".join(arguments), table
        )
        if where is not None:
            assign_question = map(lambda x: f"{x} = ?", where)
            statement += " WHERE {}".format(
                " AND ".join(assign_question)
            )
        if extras:
            for stuff in extras:
                statement += f" {stuff}"
        async with self.cursor(connection) as cursor:
            await cursor.execute(statement, values or ())
            # type: ignore # Type checker cries unnecessarily.
            rows: List[aiosqlite.Row[Any]] = [i async for i in cursor]
            if rows:
                return [Record.from_tuple(arguments, row) for row in rows]
            return None

    async def delete_record(self, connection: str, /, *, table: str, where: Tuple[str, ...], values: Optional[Tuple[Any, ...]] = None) -> None:
        delete_statement = f"DELETE FROM {table}"
        if where is not None:
            assign_question = map(lambda x: f"{x} = ?", where)
            delete_statement += " WHERE {}".format(
                " AND ".join(assign_question))
            
        async with self.cursor(connection) as cursor:
            await cursor.execute(delete_statement, values or ())
            await getattr(self, connection).commit()

    async def insert_record(self, connection: str, /, *, table: str, values: Tuple[Any, ...], columns: Tuple[str, ...]) -> None:
        insert_statement = """
                           INSERT INTO {}({}) VALUES ({})
                           """.format(
            table, ", ".join(columns), ", ".join(["?"] * len(values))
        )
        async with self.cursor(connection) as cursor:
            await cursor.execute(insert_statement, values)
            await getattr(self, connection).commit()

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


class CodingHelp(commands.HelpCommand):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    async def send_bot_help(
            self,
            mapping: Mapping[
                Optional[commands.Cog],
                List[commands.Command]
            ]
    ) -> None:
        embed = discord.Embed(title="Bot Commands",
                              description="Coding Bot V6")
        for cog, commands in mapping.items():
            if cog and not cog.hidden:
                embed.add_field(name=cog.qualified_name, value=" ".join(
                    f"`{command.name}`" for command in commands))
        destination = self.get_destination()
        await destination.send(embed=embed)


class CodingBot(commands.Bot):
    def __init__(self) -> None:
        help_command = CodingHelp(
            command_attrs={
                'cooldown': commands.CooldownMapping.from_cooldown(
                    3, 5, commands.BucketType.user
                ),
                'cooldown_after_parsing': True,
                'help': HELP_COMMAND
            }
        )
        super().__init__(
            command_prefix=[","], intents=INTENTS, case_insensitive=True,
            help_command=help_command
        )
        self.conn: Database = discord.utils.MISSING
        self.tracker = InviteTracker(self)
        self.default_prefixes = [","]
        self.welcomer = WelcomeBanner(self)
        self.processing_commands = 0
        self.message_cache = {}

    async def setup_hook(self) -> None:
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        async with Database() as self.conn:
            async with aiohttp.ClientSession() as self.session:
                return await super().start(token, reconnect=reconnect)

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await self.tracker.cache_invites()
        print("Ready")

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
            rules_channel = rules.mention
        else:
            rules_channel = "No official rule channel set yet."
        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=(

                f'Welcome {member.mention}, we\'re glad you joined! Before you get'
                ' started, here are some things to check out: \n**Read the Rules:'
                f'** {rules_channel} \n**Get roles:** <#726074137168183356> and '
                '<#806909970482069556> \n**Want help? Read here:** '
                '<#799527165863395338> and <#754712400757784709>'),
            timestamp=dt.datetime.now(dt.timezone.utc)
        )
        file = await self.welcomer.construct_image(member=member)
        channel = member.guild.get_channel(743817386792058971)
        verify_here = member.guild.get_channel(759220767711297566)

        # Assertions for narrowing types
        assert channel is not None
        assert verify_here is not None

        # type: ignore  # Always a Messageable
        await channel.send(content=member.mention, file=file)
        await verify_here.send(  # type: ignore  # Always a Messageable
            f'Welcome {member.mention}! Follow the instructions in other channels to get verified. :)',
            embed=embed
        )

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any):
        await log_error(self, event_method, *args, **kwargs)

    async def send(
        self, ctx, txt=None, *, embed=None, view=None, file=None
    ) -> discord.Message:
        if embed is None:
            embed = await self.embed(title=" ", description=txt)
        if getattr(ctx, "msg_before", None) is not None:
            key = ctx.msg_before.id
            await self.message_cache[key].edit(embed=embed)
        else:
            key = ctx.message.id
            self.message_cache[key] = await ctx.send(embed=embed, file=file)
        return self.message_cache[key]

    async def reply(
        self, ctx, txt=None, *, embed=None, view=None, file=None
    ) -> discord.Message:
        if embed is None:
            embed = await self.embed(title=" ", description=txt)
        if getattr(ctx, "msg_before", None) is not None:
            key = ctx.msg_before.id
            await self.message_cache[key].edit(embed=embed, view=view)
        else:
            key = (
                ctx.id if isinstance(ctx, discord.Message) else ctx.message.id
            )
            self.message_cache[key] = await ctx.reply(
                embed=embed, file=file, view=view
            )
        return self.message_cache[key]

    async def embed(
        self,
        *,
        title: str = None,
        description: str = None,
        url=None,
        color=0x2F3136,
    ):
        if url:
            return discord.Embed(
                title=title, description=description, color=color, url=url
            )
        return discord.Embed(title=title, description=description, color=color)

    async def process_edit(self, msg_before, msg_after):
        ctx = await super().get_context(msg_after)
        if msg_before.id in self.message_cache:
            setattr(ctx, "msg_before", msg_before)
        await super().invoke(ctx)

class TimeConverter(commands.Converter[dt.timedelta]):
    async def convert(self, ctx: commands.Context[CodingBot], argument: str) -> dt.timedelta:
        """
        Parses a string into a timedelta object

        Parameters
        ----------
        ctx : commands.Context
            The context of the command
        argument : str
            The string argument of time to parse

        Returns
        -------
        Optional[dt.timedelta]
            The parsed timedelta object

        Raises
        ------
        commands.BadArgument
            If the argument is not a valid time
        """
        time_in_secs = parse(argument)
        if time_in_secs is None:
            raise commands.BadArgument(f"{argument} is not a valid time.")
        return dt.timedelta(seconds=time_in_secs)
