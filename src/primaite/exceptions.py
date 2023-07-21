# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
class PrimaiteError(Exception):
    """The root PrimAITe Error."""

    pass


class RLlibAgentError(PrimaiteError):
    """Raised when there is a generic error with a RLlib agent that is specific to PRimAITE."""

    pass
