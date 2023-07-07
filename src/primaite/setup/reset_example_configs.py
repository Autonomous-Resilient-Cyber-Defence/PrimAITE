import filecmp
import os
import shutil
from pathlib import Path

import pkg_resources

from primaite import getLogger, USERS_CONFIG_DIR

_LOGGER = getLogger(__name__)


def run(overwrite_existing=True):
    """
    Resets the example config files in the users app config directory.

    :param overwrite_existing: A bool to toggle replacing existing edited config on or off.
    """
    configs_package_data_root = pkg_resources.resource_filename("primaite", "config/_package_data")

    for subdir, dirs, files in os.walk(configs_package_data_root):
        for file in files:
            fp = os.path.join(subdir, file)
            path_split = os.path.relpath(fp, configs_package_data_root).split(os.sep)
            target_fp = USERS_CONFIG_DIR / "example_config" / Path(*path_split)
            target_fp.parent.mkdir(exist_ok=True, parents=True)
            copy_file = not target_fp.is_file()

            if overwrite_existing and not copy_file:
                copy_file = not filecmp.cmp(fp, target_fp)

            if copy_file:
                shutil.copy2(fp, target_fp)
                _LOGGER.info(f"Reset example config: {target_fp}")
