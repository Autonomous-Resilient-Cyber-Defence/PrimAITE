# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""Contains default jupyter notebooks which demonstrate PrimAITE functionality."""

import importlib.util
import os
import subprocess
import sys
from logging import Logger

from primaite import getLogger, PRIMAITE_PATHS

_LOGGER: Logger = getLogger(__name__)


def start_jupyter_session() -> None:
    """
    Starts a new Jupyter notebook session in the app notebooks directory.

    Currently only works on Windows OS.

    .. todo:: Figure out how to get this working for Linux and MacOS too.
    """
    if importlib.util.find_spec("jupyter") is not None:
        jupyter_cmd = "python3 -m jupyter lab"
        if sys.platform == "win32":
            jupyter_cmd = "jupyter lab"

        working_dir = os.getcwd()
        os.chdir(PRIMAITE_PATHS.user_notebooks_path)
        subprocess.Popen(jupyter_cmd)
        os.chdir(working_dir)
    else:
        # Jupyter is not installed
        _LOGGER.error("Cannot start jupyter lab as it is not installed")
