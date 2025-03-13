# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""Utility functions used in the PrimAITE game layer."""
from typing import Any, Dict, Hashable, Optional, Sequence

NOT_PRESENT_IN_STATE = object()
"""
Need an object to return when the sim state does not contain a requested value. Cannot use None because sometimes
the thing requested in the state could equal None. This NOT_PRESENT_IN_STATE is a sentinel for this purpose.
"""


def access_from_nested_dict(dictionary: Dict, keys: Optional[Sequence[Hashable]]) -> Any:
    """
    Access an item from a deeply dictionary with a list of keys.

    For example, if the dictionary is {1: 'a', 2: {3: {4: 'b'}}}, then the key [2, 3, 4] would return 'b', and the key
    [2, 3] would return {4: 'b'}. Raises a KeyError if specified key does not exist at any level of nesting.

    :param dictionary: Deeply nested dictionary
    :type dictionary: Dict
    :param keys: List of dict keys used to traverse the nested dict. Each item corresponds to one level of depth.
    :type keys: List[Hashable]
    :return: The value in the dictionary
    :rtype: Any
    """
    if keys is None:
        return NOT_PRESENT_IN_STATE
    key_list = [*keys]  # copy keys to a new list to prevent editing original list
    if len(key_list) == 0:
        return dictionary
    k = key_list.pop(0)
    if k not in dictionary:
        return NOT_PRESENT_IN_STATE
    return access_from_nested_dict(dictionary[k], key_list)
