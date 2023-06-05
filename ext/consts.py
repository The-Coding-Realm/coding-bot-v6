from typing import NamedTuple

import discord


__all__ = (
    "INTENTS",
    "PREFIX_CONFIG_SCHEMA",
    "COMMANDS_CONFIG_SCHEMA",
    "WARNINGS_CONFIG_SCHEMA",
    "AFK_CONFIG_SCHEMA",
    "HELP_WARNINGS_CONFIG_SCHEMA",
    "HELP_COMMAND",
    "OFFICIAL_HELPER_ROLE_ID",
    "TCR_GUILD_ID",
    "HELP_BAN_ROLE_ID",
    "READ_HELP_RULES_ROLE_ID",
    "THANK_INFO_CONFIG_SCHEMA",
    "THANK_DATA_CONFIG_SCHEMA",
    "MESSAGE_METRIC_SCHEMA",
    "TCR_STAFF_ROLE_ID",
    "VERSION",
)


class Version(NamedTuple):
    major: int
    submajor: int
    minor: int
    release: str

    def __str__(self) -> str:
        return f"v{self.major}.{self.submajor}.{self.minor} [{self.release}]"

    def release_format(self):
        return f"Version: `{self.major}.{self.submajor}.{self.minor}`\nPatch: `{self.release}`"


VERSION = Version(major=0, submajor=0, minor=1, release="alpha")

INTENTS = discord.Intents(
    messages=True,
    guilds=True,
    members=True,
    bans=True,
    emojis=True,
    integrations=True,
    invites=True,
    webhooks=True,
    voice_states=True,
    reactions=True,
    message_content=True,
    presences=True,
)


PREFIX_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS prefixconf (
                           id BIGINT,
                           prefix TEXT
                        );
                        """

COMMANDS_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS commandconf (
                            id BIGINT,
                            command TEXT
                        );
                        """

WARNINGS_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS warnings (
                            user_id BIGINT,
                            guild_id BIGINT,
                            moderator_id BIGINT,
                            reason TEXT,
                            date BIGINT
                        );
                        """

AFK_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS afk (
                            user_id BIGINT,
                            reason TEXT,
                            afk_time BIGINT
                        );
                        """

HELP_WARNINGS_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS help_warns (
                            user_id BIGINT,
                            guild_id BIGINT,
                            helper_id BIGINT,
                            reason TEXT,
                            date BIGINT
                       );
                       """

THANK_INFO_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS thanks_info (
                            user_id BIGINT UNIQUE,
                            guild_id BIGINT,
                            thanks_count INT
                      );
                      """

THANK_DATA_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS thanks_data (
                            user_id BIGINT,
                            giver_id BIGINT,
                            guild_id BIGINT,
                            message_id BIGINT,
                            channel_id BIGINT,
                            thank_id TEXT,
                            date BIGINT,
                            reason TEXT DEFAULT "No reason given",
                            is_staff BOOLEAN CHECK(is_staff IN (0, 1)) DEFAULT 0,
                            thank_revoked BOOLEAN CHECK(thank_revoked IN (0, 1)) DEFAULT 0
                      );
                      """

MESSAGE_METRIC_SCHEMA = """CREATE TABLE IF NOT EXISTS message_metric (
                            user_id BIGINT,
                            guild_id BIGINT,
                            message_count INT,
                            deleted_message_count INT DEFAULT 0,
                            offline INT DEFAULT 0,
                            online INT DEFAULT 0,
                            dnd INT DEFAULT 0,
                            idle INT DEFAULT 0,
                            is_staff BOOLEAN CHECK(is_staff IN (0, 1)) DEFAULT 0,
                            UNIQUE(user_id, guild_id)
                        );"""

HELP_COMMAND = """
            Help command for Coding Bot

            Usage:
            ------
            `{prefix}help`
            `{prefix}help <command>`
            `{prefix}help <category>`
            `{prefix}help <command> <sub-command>`
            """

OFFICIAL_HELPER_ROLE_ID = 726650418444107869
TCR_GUILD_ID = 681882711945641997
HELP_BAN_ROLE_ID = 903133405317857300
READ_HELP_RULES_ROLE_ID = 903133599715459153
TCR_STAFF_ROLE_ID = 795145820210462771
TCR_MEMBER_ROLE_ID = 744403871262179430

# mods pls fill this up
TICKET_CATEGORY_ID = 0
