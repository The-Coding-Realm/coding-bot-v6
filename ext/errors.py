from __future__ import annotations

from discord.ext import commands


class InsufficientPrivilegeError(commands.CheckFailure):
    """
    Exception for insufficient privilege
    """

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message
