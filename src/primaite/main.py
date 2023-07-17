# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
"""The main PrimAITE session runner module."""
import argparse
from pathlib import Path
from typing import Optional, Union

from primaite import getLogger
from primaite.primaite_session import PrimaiteSession

_LOGGER = getLogger(__name__)


def run(
    training_config_path: Optional[Union[str, Path]] = "",
    lay_down_config_path: Optional[Union[str, Path]] = "",
    session_path: Optional[Union[str, Path]] = None,
):
    """
    Run the PrimAITE Session.

    :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
        :type training_config_path: Union[path, str]
        :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
        :type lay_down_config_path: Union[path, str]
        :param session_path: directory path of the session to load
    """
    session = PrimaiteSession(training_config_path, lay_down_config_path, session_path)

    session.setup()
    session.learn()
    session.evaluate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tc")
    parser.add_argument("--ldc")
    parser.add_argument("--load")

    args = parser.parse_args()
    if args.load:
        run(session_path=args.load)
    else:
        if not args.tc:
            _LOGGER.error("Please provide a training config file using the --tc " "argument")
        if not args.ldc:
            _LOGGER.error("Please provide a lay down config file using the --ldc " "argument")
        run(training_config_path=args.tc, lay_down_config_path=args.ldc)
