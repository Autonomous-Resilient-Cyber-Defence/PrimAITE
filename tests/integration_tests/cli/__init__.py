# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import List

from typer.testing import CliRunner, Result

from primaite.cli import app


def cli(args: List[str]) -> Result:
    """Pass in a list of arguments and it will return the result."""
    runner = CliRunner()
    return runner.invoke(app, args)
