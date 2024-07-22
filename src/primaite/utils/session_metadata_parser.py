# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
# flake8: noqa
raise DeprecationWarning(
    "Benchmarking depends on deprecated functionality and it has not been updated to primaite v3 yet."
)
import json
from pathlib import Path
from typing import Any, Dict, Union

import yaml

from primaite import getLogger

_LOGGER = getLogger(__name__)


def parse_session_metadata(session_path: Union[Path, str], dict_only: bool = False) -> Dict[str, Any]:
    """
    Loads a session metadata from the given directory path.

    :param session_path: Directory where the session metadata file is in
    :param dict_only: If dict_only is true, the function will only return the dict contents of session metadata

    :return: Dictionary which has all the session metadata contents
    :rtype: Dict

    :return: Path where the YAML copy of the training config is dumped into
    :rtype: str
    :return: Path where the YAML copy of the laydown config is dumped into
    :rtype: str
    """
    if not isinstance(session_path, Path):
        session_path = Path(session_path)

    if not session_path.exists():
        # Session path does not exist
        msg = f"Failed to load PrimAITE Session, path does not exist: {session_path}"
        _LOGGER.error(msg)
        raise FileNotFoundError(msg)

    # Unpack the session_metadata.json file
    md_file = session_path / "session_metadata.json"
    with open(md_file, "r") as file:
        md_dict = json.load(file)

    # if dict only, return dict without doing anything else
    if dict_only:
        return md_dict

    # Create a temp directory and dump the training and lay down
    # configs into it
    temp_dir = session_path / ".temp"
    temp_dir.mkdir(exist_ok=True)

    temp_tc = temp_dir / "tc.yaml"
    with open(temp_tc, "w") as file:
        yaml.dump(md_dict["env"]["training_config"], file)

    temp_ldc = temp_dir / "ldc.yaml"
    with open(temp_ldc, "w") as file:
        yaml.dump(md_dict["env"]["lay_down_config"], file)

    return [md_dict, temp_tc, temp_ldc]
