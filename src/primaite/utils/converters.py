# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from enum import Enum
from typing import Any, Dict


def convert_dict_enum_keys_to_enum_values(d: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Convert dictionary keys from enums to their corresponding values.

    :param d: dict
        The dictionary with enum keys to be converted.
    :return: dict
        The dictionary with enum values as keys.
    """
    result = {}
    for key, value in d.items():
        if isinstance(key, Enum):
            new_key = key.value
        else:
            new_key = key

        if isinstance(value, dict):
            result[new_key] = convert_dict_enum_keys_to_enum_values(value)
        else:
            result[new_key] = value
    return result
