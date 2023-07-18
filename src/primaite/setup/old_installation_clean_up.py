# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
from typing import TYPE_CHECKING

from primaite import getLogger

if TYPE_CHECKING:
    from logging import Logger

_LOGGER: Logger = getLogger(__name__)


def run() -> None:
    """Perform the full clean-up."""
    pass


if __name__ == "__main__":
    run()
