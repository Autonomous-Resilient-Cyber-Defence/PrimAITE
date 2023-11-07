# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
class PrimaiteError(Exception):
    """The root PrimAITe Error."""

    pass


class NetworkError(PrimaiteError):
    """Raised when an error occurs at the network level."""

    pass
