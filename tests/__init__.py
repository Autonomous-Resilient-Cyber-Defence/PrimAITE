# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from pathlib import Path
from typing import Final

TEST_CONFIG_ROOT: Final[Path] = Path(__file__).parent / "config"
"The tests config root directory."

TEST_ASSETS_ROOT: Final[Path] = Path(__file__).parent / "assets"
"The tests assets root directory."
