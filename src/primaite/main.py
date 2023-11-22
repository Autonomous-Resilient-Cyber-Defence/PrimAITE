# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""The main PrimAITE session runner module."""
import argparse
from pathlib import Path
from typing import Optional, Union

from primaite import getLogger
from primaite.config.load import load
from primaite.game.game import PrimaiteGame

# from primaite.primaite_session import PrimaiteSession

_LOGGER = getLogger(__name__)


def run(
    config_path: Optional[Union[str, Path]] = "",
    agent_load_path: Optional[Union[str, Path]] = None,
) -> None:
    """
    Run the PrimAITE Session.

    :param training_config_path: YAML file containing configurable items defined in
            `primaite.config.training_config.TrainingConfig`
    :type training_config_path: Union[path, str]
    :param lay_down_config_path: YAML file containing configurable items for generating network laydown.
    :type lay_down_config_path: Union[path, str]
    :param session_path: directory path of the session to load
    :param legacy_training_config: True if the training config file is a legacy file from PrimAITE < 2.0,
        otherwise False.
    :param legacy_lay_down_config: True if the lay_down config file is a legacy file from PrimAITE < 2.0,
        otherwise False.
    """
    cfg = load(config_path)
    sess = PrimaiteGame.from_config(cfg=cfg, agent_load_path=agent_load_path)
    sess.start_session()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")

    args = parser.parse_args()
    if not args.config:
        _LOGGER.error("Please provide a config file using the --config " "argument")

    run(session_path=args.config)
