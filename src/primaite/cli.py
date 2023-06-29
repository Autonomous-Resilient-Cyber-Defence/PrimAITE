# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""Provides a CLI using Typer as an entry point."""
import logging
import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional

import pkg_resources
import typer
import yaml
from platformdirs import PlatformDirs
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def build_dirs():
    """Build the PrimAITE app directories."""
    from primaite.setup import setup_app_dirs

    setup_app_dirs.run()


@app.command()
def reset_notebooks(overwrite: bool = True):
    """
    Force a reset of the demo notebooks in the users notebooks directory.

    :param overwrite: If True, will overwrite existing demo notebooks.
    """
    from primaite.setup import reset_demo_notebooks

    reset_demo_notebooks.run(overwrite)


@app.command()
def logs(last_n: Annotated[int, typer.Option("-n")]):
    """
    Print the PrimAITE log file.

    :param last_n: The number of lines to print. Default value is 10.
    """
    import re

    from primaite import LOG_PATH

    if os.path.isfile(LOG_PATH):
        with open(LOG_PATH) as file:
            lines = file.readlines()
        for line in lines[-last_n:]:
            print(re.sub(r"\n*", "", line))


_LogLevel = Enum("LogLevel", {k: k for k in logging._levelToName.values()})  # noqa


@app.command()
def log_level(level: Annotated[Optional[_LogLevel], typer.Argument()] = None):
    """
    View or set the PrimAITE Log Level.

    To View, simply call: primaite log-level

    To set, call: primaite log-level <desired log level>

    For example, to set the to debug, call: primaite log-level DEBUG
    """
    app_dirs = PlatformDirs(appname="primaite")
    app_dirs.user_config_path.mkdir(exist_ok=True, parents=True)
    user_config_path = app_dirs.user_config_path / "primaite_config.yaml"
    if user_config_path.exists():
        with open(user_config_path, "r") as file:
            primaite_config = yaml.safe_load(file)

        if level:
            primaite_config["log_level"] = level.value
            with open(user_config_path, "w") as file:
                yaml.dump(primaite_config, file)
        else:
            level = primaite_config["log_level"]
            print(f"PrimAITE Log Level: {level}")


@app.command()
def notebooks():
    """Start Jupyter Lab in the users PrimAITE notebooks directory."""
    from primaite.notebooks import start_jupyter_session

    start_jupyter_session()


@app.command()
def version():
    """Get the installed PrimAITE version number."""
    import primaite

    print(primaite.__version__)


@app.command()
def clean_up():
    """Cleans up left over files from previous version installations."""
    from primaite.setup import old_installation_clean_up

    old_installation_clean_up.run()


@app.command()
def setup(overwrite_existing: bool = True):
    """
    Perform the PrimAITE first-time setup.

    WARNING: All user-data will be lost.
    """
    # Does this way to avoid using PrimAITE package before config is loaded
    app_dirs = PlatformDirs(appname="primaite")
    app_dirs.user_config_path.mkdir(exist_ok=True, parents=True)
    user_config_path = app_dirs.user_config_path / "primaite_config.yaml"
    build_config = overwrite_existing or (not user_config_path.exists())
    if build_config:
        pkg_config_path = Path(
            pkg_resources.resource_filename(
                "primaite", "setup/_package_data/primaite_config.yaml"
            )
        )

        shutil.copy2(pkg_config_path, user_config_path)

    from primaite import getLogger
    from primaite.setup import (
        old_installation_clean_up,
        reset_demo_notebooks,
        reset_example_configs,
        setup_app_dirs,
    )

    _LOGGER = getLogger(__name__)

    _LOGGER.info("Performing the PrimAITE first-time setup...")

    if build_config:
        _LOGGER.info("Building primaite_config.yaml...")

    _LOGGER.info("Building the PrimAITE app directories...")
    setup_app_dirs.run()

    _LOGGER.info("Rebuilding the demo notebooks...")
    reset_demo_notebooks.run(overwrite_existing=True)

    _LOGGER.info("Rebuilding the example notebooks...")
    reset_example_configs.run(overwrite_existing=True)

    _LOGGER.info("Performing a clean-up of previous PrimAITE installations...")
    old_installation_clean_up.run()

    _LOGGER.info("PrimAITE setup complete!")


@app.command()
def session(tc: str, ldc: str):
    """
    Run a PrimAITE session.

    :param tc: The training config filepath.
    :param ldc: The lay down config file path.
    """
    from primaite.main import run

    run(training_config_path=tc, lay_down_config_path=ldc)
