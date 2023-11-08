# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import os
from logging import Logger
from pathlib import Path

import pkg_resources

from primaite import getLogger

_LOGGER: Logger = getLogger(__name__)


def get_file_path(path: str) -> Path:
    """
    Get PrimAITE package data.

    :Example:

    >>> from primaite.utils.package_data import get_file_path
    >>> main_env_config = get_file_path("config/_package_data/training_config_main.yaml")


    :param path: The path from the primaite root.
    :return: The file path of the package data file.
    :raise FileNotFoundError: When the filepath does not exist.
    """
    fp = pkg_resources.resource_filename("primaite", path)
    if os.path.isfile(fp):
        return Path(fp)
    else:
        msg = f"Cannot PrimAITE package data: {fp}"
        _LOGGER.error(msg)
        raise FileNotFoundError(msg)
