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

app = typer.Typer(no_args_is_help=True)


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


@app.command()
def mode(
    dev: Annotated[bool, typer.Option("--dev", help="Activates PrimAITE developer mode")] = None,
    prod: Annotated[bool, typer.Option("--prod", help="Activates PrimAITE production mode")] = None,
) -> None:
    """
    Switch PrimAITE between developer mode and production mode.

    By default, PrimAITE will be in production mode.

    To view the current mode, use: primaite mode

    To set to development mode, use: primaite mode --dev

    To return to production mode, use: primaite mode --prod
    """
    if PRIMAITE_PATHS.app_config_file_path.exists():
        with open(PRIMAITE_PATHS.app_config_file_path, "r") as file:
            primaite_config = yaml.safe_load(file)
            if dev and prod:
                print("Unable to activate developer and production modes concurrently.")
                return

            if (dev is None) and (prod is None):
                is_dev_mode = primaite_config["developer_mode"]

                if is_dev_mode:
                    print("PrimAITE is running in developer mode.")
                else:
                    print("PrimAITE is running in production mode.")
            if dev:
                # activate dev mode
                primaite_config["developer_mode"] = True
                with open(PRIMAITE_PATHS.app_config_file_path, "w") as file:
                    yaml.dump(primaite_config, file)
                print("PrimAITE is running in developer mode.")
            if prod:
                # activate prod mode
                primaite_config["developer_mode"] = False
                with open(PRIMAITE_PATHS.app_config_file_path, "w") as file:
                    yaml.dump(primaite_config, file)
                print("PrimAITE is running in production mode.")
