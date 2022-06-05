import discord

__all__ = (
    'INTENTS',
    'PREFIX_CONFIG_SCHEMA',
    'COMMANDS_CONFIG_SCHEMA',
    'WARNINGS_CONFIG_SCHEMA',
    'AFK_CONFIG_SCHEMA',
    'HELP_WARNINGS_CONFIG_SCHEMA',
    'HELP_COMMAND',
    'OFFICIAL_HELPER_ROLE_ID',
    'TCR_GUILD_ID',
    'HELP_BAN_ROLE_ID',
    'READ_HELP_RULES_ROLE_ID',
    'THANK_INFO_CONFIG_SCHEMA',
    'THANK_DATA_CONFIG_SCHEMA'
)

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
    message_content=True
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
                            user_id BIGINT,
                            guild_id BIGINT,
                            thanks INT,
                      );
                      """

THANK_DATA_CONFIG_SCHEMA = """CREATE TABLE IF NOT EXISTS thanks_data (
                            user_id BIGINT,
                            giver_id BIGINT,
                            guild_id BIGINT,
                            date BIGINT,
                            reason TEXT,
                            message_link TEXT
                      );
                      """

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

