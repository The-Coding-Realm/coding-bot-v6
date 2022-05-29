from discord.ext.commands import CheckFailure


class InsufficientPrivilegeError(CheckFailure):
    """
    Exception for insufficient privilege
    """

    def __init__(self, message) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message
