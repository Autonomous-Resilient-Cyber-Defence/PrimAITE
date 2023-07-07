# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
import filecmp
import os
import shutil
from pathlib import Path

import pkg_resources

from primaite import getLogger, NOTEBOOKS_DIR

_LOGGER = getLogger(__name__)


def run(overwrite_existing: bool = True):
    """
    Resets the demo jupyter notebooks in the users app notebooks directory.

    :param overwrite_existing: A bool to toggle replacing existing edited notebooks on or off.
    """
    notebooks_package_data_root = pkg_resources.resource_filename("primaite", "notebooks/_package_data")
    for subdir, dirs, files in os.walk(notebooks_package_data_root):
        for file in files:
            fp = os.path.join(subdir, file)
            path_split = os.path.relpath(fp, notebooks_package_data_root).split(os.sep)
            target_fp = NOTEBOOKS_DIR / Path(*path_split)
            target_fp.parent.mkdir(exist_ok=True, parents=True)
            copy_file = not target_fp.is_file()

            if overwrite_existing and not copy_file:
                copy_file = (not filecmp.cmp(fp, target_fp)) and (".ipynb_checkpoints" not in str(target_fp))

            if copy_file:
                shutil.copy2(fp, target_fp)
                _LOGGER.info(f"Reset example notebook: {target_fp}")
