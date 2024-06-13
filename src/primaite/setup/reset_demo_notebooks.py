# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import filecmp
import shutil
from logging import Logger
from pathlib import Path

from primaite import getLogger, PRIMAITE_PATHS

_LOGGER: Logger = getLogger(__name__)


def should_copy_file(src: Path, dest: Path, overwrite_existing: bool) -> bool:
    """
    Determine if the file should be copied.

    :param src: The source file Path.
    :param dest: The destination file Path.
    :param overwrite_existing: A bool to toggle replacing existing edited files on or off.
    :return: True if file should be copied, otherwise False.
    """
    if not dest.is_file():
        return True

    if overwrite_existing and not filecmp.cmp(src, dest):
        return True

    return False


def run(overwrite_existing: bool = True) -> None:
    """
    Resets the demo Jupyter notebooks in the user's app notebooks directory.

    :param overwrite_existing: A bool to toggle replacing existing edited notebooks on or off.
    """
    primaite_root = Path(__file__).parent.parent
    example_notebooks_user_dir = PRIMAITE_PATHS.user_notebooks_path / "example_notebooks"
    example_notebooks_user_dir.mkdir(exist_ok=True, parents=True)

    for src_fp in primaite_root.glob("**/*.ipynb"):
        dst_fp = example_notebooks_user_dir / src_fp.name

        if should_copy_file(src_fp, dst_fp, overwrite_existing):
            print(dst_fp)
            shutil.copy2(src_fp, dst_fp)
            _LOGGER.info(f"Reset example notebook: {dst_fp}")

    for src_fp in primaite_root.glob("notebooks/_package_data/*"):
        dst_fp = example_notebooks_user_dir / "_package_data" / src_fp.name
        if should_copy_file(src_fp, dst_fp, overwrite_existing):
            if not Path.exists(example_notebooks_user_dir / "_package_data/"):
                Path.mkdir(example_notebooks_user_dir / "_package_data/")
            print(dst_fp)
            shutil.copy2(src_fp, dst_fp)
            _LOGGER.info(f"Copied notebook resource to: {dst_fp}")
