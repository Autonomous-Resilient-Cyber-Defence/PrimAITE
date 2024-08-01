# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import subprocess
import sys
from typing import Any


def run_command(command: Any):
    """Runs a command and returns the exit code."""
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


# Run pytest with coverage
run_command(
    "coverage run -m --source=primaite pytest -v -o junit_family=xunit2 "
    "--junitxml=junit/test-results.xml --cov-fail-under=80"
)

# Generate coverage reports if tests passed
run_command("coverage xml -o coverage.xml -i")
run_command("coverage html -d htmlcov -i")
