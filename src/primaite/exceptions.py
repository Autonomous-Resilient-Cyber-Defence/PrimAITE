# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
class PrimaiteError(Exception):
    """The root PrimAITe Error."""

    pass


class RLlibAgentError(PrimaiteError):
    """Raised when there is a generic error with a RLlib agent that is specific to PRimAITE."""

    pass
