# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
from pathlib import Path
from typing import Final

TEST_CONFIG_ROOT: Final[Path] = Path(__file__).parent / "config"
"The tests config root directory."

TEST_ASSETS_ROOT: Final[Path] = Path(__file__).parent / "assets"
"The tests assets root directory."
