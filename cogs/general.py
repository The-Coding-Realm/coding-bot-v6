from __future__ import annotations

import inspect
import os
from typing import TYPE_CHECKING, List

import discord
from discord.ext import commands
from ext.helpers import UrbanDefinition, UrbanDictionary

if TYPE_CHECKING:
    from ext.models import CodingBot


class General(commands.Cog, command_attrs=dict(hidden=False)):
    hidden = False

    def __init__(self, bot: CodingBot) -> None:
        self.bot = bot
        self.ud = UrbanDictionary(bot.session)

    @commands.hybrid_command(name="source", aliases=["github", "code"])
    @commands.cooldown(1, 1, commands.BucketType.channel)
    async def _source(
        self, ctx: commands.Context[CodingBot], *, command: str = None
    ) -> None:
        """
        Displays my full source code or for a specific command.
        To display the source code of a subcommand you can separate it by
        periods or spaces.

        Usage:
        ------
        `{prefix}source` *will send link to my source code*
        `{prefix}source [command]` *will send link to the source code of the command*
        `{prefix}source [command] [subcommand]`:
        *will send link to the source code of the subcommand*
        """
        github = "<:githubwhite:804344724621230091>"
        embed = discord.Embed(title=f"{github} GitHub (Click Here) {github}")
        source_url = "https://github.com/The-Coding-Realm/coding-bot-v6"
        branch = "master"
        if command is None:
            embed.url = source_url
            return await self.bot.reply(ctx, embed=embed)

        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
            if help_command := self.bot.get_command("help"):
                embed.description = help_command.help.format(prefix=ctx.prefix)
        else:
            obj = self.bot.get_command(command.replace(".", " "))
            if obj is None:
                embed = discord.Embed(
                    title="Error 404", description=f"Command `{command}` not found."
                )
                return await self.bot.reply(ctx, embed=embed)

            if obj.help:
                embed.description = obj.help.format(prefix=ctx.prefix)

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith("discord"):
            # not a built-in command
            location = os.path.relpath(filename).replace("\\", "/")
        else:
            location = module.replace(".", "/") + ".py"
            source_url = "https://github.com/Rapptz/discord.py"
            branch = "master"

        final_url = (
            f"{source_url}/blob/{branch}/{location}#L{firstlineno}-L"
            f"{firstlineno + len(lines) - 1}"
        )
        embed.url = final_url
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_command(name="define")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def define(self, ctx: commands.Context[CodingBot], *, word: str):
        """
        Gets deinitions from Urban Dictionary.

        Usage:
        ------
        `{prefix}define [word]` *will send the definition of the word*
        """
        definition: List[UrbanDefinition] = await self.ud.define(word)
        if not definition:
            return await ctx.send(f"Could not find definition for `{word}`")
        definition = definition[0]
        embed = discord.Embed(
            title=f"Definition of {word}",
            description=f"**Meaning**: {definition.meaning}\n",
            color=discord.Color.random(),
        )
        embed.description += (
            f"\n**Example:** {definition.example}\n\n{definition.author}"
        )
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url
        )
        await self.bot.reply(ctx, embed=embed)

    @commands.hybrid_group(invoke_without_command=True)
    async def avatar(self, ctx: commands.Context[CodingBot]):
        """
        Commands for getting avatars.

        Usage:
        ------
        `{prefix}avatar` *will send a list of available methods*
        """
        embed = discord.Embed(
            title="Avatar command", description="Available methods: `main`, `display`"
        )
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url
        )
        await self.bot.reply(ctx, embed=embed)

    @avatar.command(name="main")
    async def avatar_main(
        self, ctx: commands.Context[CodingBot], member: discord.Member
    ):
        """
        Returns the main avatar of a user.

        Usage:
        ------
        `{prefix}avatar main [user]` *will send the main avatar of the user*
        """
        embed = discord.Embed(
            title=f"{member}'s Main Avatar",
            description=f"Showing {member.mention}'s Main Avatar",
            color=discord.Color.random(),
        )
        embed.set_image(url=member.avatar.url)
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url
        )
        await self.bot.reply(ctx, embed=embed)

    @avatar.command(name="display")
    async def avatar_display(
        self, ctx: commands.Context[CodingBot], member: discord.Member
    ):
        """
        Returns the display avatar of a user.

        Usage:
        ------
        `{prefix}avatar display [user]` *will send the display avatar of the user*
        """
        embed = discord.Embed(
            title=f"{member}'s Avatar",
            description=f"Showing {member.mention}'s Avatar",
            color=discord.Color.random(),
        )
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url
        )
        await self.bot.reply(ctx, embed=embed)


async def setup(bot: CodingBot) -> None:
    await bot.add_cog(General(bot))
