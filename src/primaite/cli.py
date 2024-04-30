# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""Provides a CLI using Typer as an entry point."""
import logging
import os
from enum import Enum
from typing import Optional

import typer
import yaml
from typing_extensions import Annotated

from primaite import PRIMAITE_PATHS
from primaite.utils.cli import dev_cli

app = typer.Typer(no_args_is_help=True)
app.add_typer(dev_cli.dev, name="dev-mode")


@app.command()
def build_dirs() -> None:
    """Build the PrimAITE app directories."""
    from primaite import PRIMAITE_PATHS

    PRIMAITE_PATHS.mkdirs()


@app.command()
def reset_notebooks(overwrite: bool = True) -> None:
    """
    Force a reset of the demo notebooks in the users notebooks directory.

    :param overwrite: If True, will overwrite existing demo notebooks.
    """
    from primaite.setup import reset_demo_notebooks

    reset_demo_notebooks.run(overwrite)


@app.command()
def logs(last_n: Annotated[int, typer.Option("-n")]) -> None:
    """
    Print the PrimAITE log file.

    :param last_n: The number of lines to print. Default value is 10.
    """
    import re

    from primaite import PRIMAITE_PATHS

    if os.path.isfile(PRIMAITE_PATHS.app_log_file_path):
        with open(PRIMAITE_PATHS.app_log_file_path) as file:
            lines = file.readlines()
        for line in lines[-last_n:]:
            print(re.sub(r"\n*", "", line))


_LogLevel = Enum("LogLevel", {k: k for k in logging._levelToName.values()})  # noqa


@app.command()
def log_level(level: Annotated[Optional[_LogLevel], typer.Argument()] = None) -> None:
    """
    View or set the PrimAITE Log Level.

    To View, simply call: primaite log-level

    To set, call: primaite log-level <desired log level>

    For example, to set the to debug, call: primaite log-level DEBUG
    """
    if PRIMAITE_PATHS.app_config_file_path.exists():
        with open(PRIMAITE_PATHS.app_config_file_path, "r") as file:
            primaite_config = yaml.safe_load(file)

        if level:
            primaite_config["logging"]["log_level"] = level.value
            with open(PRIMAITE_PATHS.app_config_file_path, "w") as file:
                yaml.dump(primaite_config, file)
            print(f"PrimAITE Log Level: {level}")
        else:
            level = primaite_config["logging"]["log_level"]
            print(f"PrimAITE Log Level: {level}")


@app.command()
def version() -> None:
    """Get the installed PrimAITE version number."""
    import primaite

    print(primaite.__version__)


@app.command()
def setup(overwrite_existing: bool = True) -> None:
    """
    Perform the PrimAITE first-time setup.

    WARNING: All user-data will be lost.
    """
    from primaite import getLogger
    from primaite.setup import reset_demo_notebooks, reset_example_configs

    _LOGGER = getLogger(__name__)

    _LOGGER.info("Performing the PrimAITE first-time setup...")

    _LOGGER.info("Building primaite_config.yaml...")

    _LOGGER.info("Building the PrimAITE app directories...")
    PRIMAITE_PATHS.mkdirs()

    _LOGGER.info("Rebuilding the demo notebooks...")
    reset_demo_notebooks.run(overwrite_existing=True)

    _LOGGER.info("Rebuilding the example notebooks...")
    reset_example_configs.run(overwrite_existing=True)

    _LOGGER.info("PrimAITE setup complete!")
