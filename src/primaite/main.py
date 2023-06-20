# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The main PrimAITE session runner module."""
import argparse
from pathlib import Path
from typing import Union

from primaite import getLogger
from primaite.primaite_session import PrimaiteSession

_LOGGER = getLogger(__name__)


def run(training_config_path: Union[str, Path], lay_down_config_path: Union[str, Path]):
    """Run the PrimAITE Session.

    :param training_config_path: The training config filepath.
    :param lay_down_config_path: The lay down config filepath.
    """
    session = PrimaiteSession(training_config_path, lay_down_config_path)

    session.setup()
    session.learn()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tc")
    parser.add_argument("--ldc")
    args = parser.parse_args()
    if not args.tc:
        _LOGGER.error(
            "Please provide a training config file using the --tc " "argument"
        )
    if not args.ldc:
        _LOGGER.error(
            "Please provide a lay down config file using the --ldc " "argument"
        )
    run(training_config_path=args.tc, lay_down_config_path=args.ldc)


