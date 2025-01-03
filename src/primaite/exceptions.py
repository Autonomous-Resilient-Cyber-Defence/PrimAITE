# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
class PrimaiteError(Exception):
    """The root PrimAITE Error."""

    pass


class NetworkError(PrimaiteError):
    """Raised when an error occurs at the network level."""

    pass
