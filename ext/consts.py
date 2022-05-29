import discord

__all__ = (
    'INTENTS',
    'PREFIX_CONFIG_SCHEMA',
    'COMMANDS_CONFIG_SCHEMA',
    'WARNINGS_CONFIG_SCHEMA'
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
