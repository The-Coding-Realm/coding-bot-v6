from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

import aiohttp
import discord
from discord.ext import commands
from DiscordUtils import InviteTracker
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pytimeparse import parse

from .consts import HELP_COMMAND, INTENTS
from .helpers import AntiRaid, WelcomeBanner, log_error

load_dotenv('.env', verbose=True)

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

    async def send_group_help(self, group: commands.Group[Any, ..., Any], /) -> None:
        embed = discord.Embed(title=f"{group.qualified_name} Commands",
                                description=group.help)

        for command in group.commands:
            if not command.hidden:
                embed.description += f"\n`{command.qualified_name} - {command.brief or 'Not documented yet'}`"

        destination = self.get_destination()
        await destination.send(embed=embed)

    async def send_command_help(self, command: commands.Command[Any, ..., Any], /) -> None:
        embed = discord.Embed(title=f"{command.qualified_name} Command",
                              description=command.help)

        destination = self.get_destination()
        await destination.send(embed=embed)
    
    async def send_cog_help(self, cog: commands.Cog[Any, ..., Any], /) -> None:
        embed = discord.Embed(title=f"{cog.qualified_name} Commands",
                              description=cog.help)

        for command in cog.get_commands():
            if not command.hidden:
                embed.description += f"\n`{command.qualified_name} {command.brief or 'Not documented yet'}`"

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
            command_prefix=[')'], intents=INTENTS, case_insensitive=True,
            help_command=help_command
        )
        self.database: AsyncIOMotorClient = None
        self.tracker = InviteTracker(self)
        self.default_prefixes = [")"]
        self.welcomer = WelcomeBanner(self)
        self.processing_commands = 0
        self.message_cache = {}
        self.spotify_session: Optional[tuple] = None
        self.spotify_client_id: str = os.environ.get("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret: str = os.environ.get("SPOTIFY_CLIENT_SECRET")
        self.welcomer_enabled = True
        self.welcomer_channel_id = 743817386792058971
        self.raid_mode_enabled = False
        self.raid_checker = AntiRaid(self)
        self.afk_cache: Dict[int, Dict[int, Tuple[str, int]]] = {}

    async def setup_hook(self) -> None:
        self.database = AsyncIOMotorClient(os.environ.get("MONGO_DB_URI"))
        self.raid_checker.check_for_raid.start()
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
        os.environ['JISHAKU_NO_UNDERSCORE'] = "True"
        await self.load_extension("jishaku")
        jishaku = self.get_cog('Jishaku')
        if jishaku:
            jishaku.hidden = True

    async def start(self, token: str, *, reconnect: bool = True) -> None:
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
        await self.tracker.add_guild_cache(guild)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.tracker.remove_guild_cache(guild)

    async def on_member_join(self, member: discord.Member) -> None:
        if not self.welcomer_enabled:
            return
        banned = await self.raid_checker.cache_insert_or_ban(member)
        if banned:
            return
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
        channel = member.guild.get_channel(self.welcomer_channel_id)
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
        self, ctx, *args, **kwargs
    ) -> discord.Message:
        if getattr(ctx, "msg_before", None) is not None:
            key = ctx.msg_before.id
            await self.message_cache[key].edit(*args, **kwargs)
        else:
            key = ctx.message.id
            self.message_cache[key] = await ctx.send(*args, **kwargs)
        return self.message_cache[key]

    async def reply(
            self, ctx, *args, **kwargs) -> discord.Message:
        if getattr(ctx, "msg_before", None) is not None:
            key = ctx.msg_before.id
            await self.message_cache[key].edit(*args, **kwargs)
        else:
            key = (
                ctx.id if isinstance(ctx, discord.Message) else ctx.message.id
            )
            self.message_cache[key] = await ctx.reply(
                *args, **kwargs
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
