from pathlib import Path
from typing import Union

import yaml

from primaite import getLogger

_LOGGER = getLogger(__name__)


def load(file_path: Union[str, Path]) -> Dict:
    """
    Read a YAML file and return the contents as a dictionary.

    :param file_path: Path to the YAML file.
    :type file_path: Union[str, Path]
    :return: Config dictionary
    :rtype: Dict
    """

    if not isinstance(file_path, Path):
        file_path = Path(file_path)
