import discord

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
)