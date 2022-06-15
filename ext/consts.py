import discord

__all__ = (
    'INTENTS',
    'HELP_COMMAND',
    'OFFICIAL_HELPER_ROLE_ID',
    'TCR_GUILD_ID',
    'HELP_BAN_ROLE_ID',
    'READ_HELP_RULES_ROLE_ID',
    'TCR_STAFF_ROLE_ID'
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
    message_content=True,
    presences=True
)


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

# mods pls fill this up
TICKET_CATEGORY_ID = 0
