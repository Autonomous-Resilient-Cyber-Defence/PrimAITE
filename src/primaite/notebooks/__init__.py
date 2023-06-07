# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import importlib.util
import os
import subprocess
import sys

from primaite import NOTEBOOKS_DIR, getLogger

_LOGGER = getLogger(__name__)


def start_jupyter_session():
    """
    Starts a new Jupyter notebook session in the app notebooks directory.

    Currently only works on Windows OS.

    .. todo:: Figure out how to get this working for Linux and MacOS too.
    """
    if sys.platform == "win32":
        if importlib.util.find_spec("jupyter") is not None:
            # Jupyter is installed
            working_dir = os.getcwd()
            os.chdir(NOTEBOOKS_DIR)
            subprocess.Popen("jupyter lab")
            os.chdir(working_dir)
        else:
            # Jupyter is not installed
            _LOGGER.error("Cannot start jupyter lab as it is not installed")
    else:
        msg = (
            "Feature currently only supported on Windows OS. For "
            "Linux/MacOS users, run 'cd ~/primaite/notebooks; jupyter "
            "lab' from your Python environment."
        )
        _LOGGER.warning(msg)
