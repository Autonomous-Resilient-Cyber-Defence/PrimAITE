# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
from typing import Dict, List, Union

import numpy as np

from primaite.common.custom_typing import NodeUnion
from primaite.common.enums import (
    HardwareState,
    LinkStatus,
    NodeHardwareAction,
    NodePOLType,
    NodeSoftwareAction,
    SoftwareState,
)


def transform_action_node_readable(action: List[int]) -> List[Union[int, str]]:
    """Convert a node action from enumerated format to readable format.

    example:
    [1, 3, 1, 0] -> [1, 'SERVICE', 'PATCHING', 0]

    :param action: Agent action, formatted as a list of ints, for more information check out
        `primaite.environment.primaite_env.Primaite`
    :type action: List[int]
    :return: The same action list, but with the encodings translated back into meaningful labels
    :rtype: List[Union[int,str]]
    """
    action_node_property = NodePOLType(action[1]).name

    if action_node_property == "OPERATING":
        property_action = NodeHardwareAction(action[2]).name
    elif (action_node_property == "OS" or action_node_property == "SERVICE") and action[2] <= 1:
        property_action = NodeSoftwareAction(action[2]).name
    else:
        property_action = "NONE"

    new_action = [action[0], action_node_property, property_action, action[3]]
    return new_action


def transform_action_acl_readable(action: List[str]) -> List[Union[str, int]]:
    """
    Transform an ACL action to a more readable format.

    example:
    [0, 1, 2, 5, 0, 1] -> ['NONE', 'ALLOW', 2, 5, 'ANY', 1]

    :param action: Agent action, formatted as a list of ints, for more information check out
        `primaite.environment.primaite_env.Primaite`
    :type action: List[int]
    :return: The same action list, but with the encodings translated back into meaningful labels
    :rtype: List[Union[int,str]]
    """
    action_decisions = {0: "NONE", 1: "CREATE", 2: "DELETE"}
    action_permissions = {0: "DENY", 1: "ALLOW"}

    action_decision = action_decisions[action[0]]
    action_permission = action_permissions[action[1]]

    # For IPs, Ports and Protocols, 0 means any, otherwise its just an index
    new_action = [action_decision, action_permission] + list(action[2:6])
    for n, val in enumerate(list(action[2:6])):
        if val == 0:
            new_action[n + 2] = "ANY"

    return new_action


def is_valid_node_action(action: List[int]) -> bool:
    """
    Is the node action an actual valid action.

    Only uses information about the action to determine if the action has an effect

    Does NOT consider:
    - Node ID not valid to perform an operation - e.g. selected node has no service so cannot patch
    - Node already being in that state (turning an ON node ON)

    :param action: Agent action, formatted as a list of ints, for more information check out
        `primaite.environment.primaite_env.Primaite`
    :type action: List[int]
    :return: Whether the action is valid
    :rtype: bool
    """
    action_r = transform_action_node_readable(action)

    node_property = action_r[1]
    node_action = action_r[2]

    # print("node property", node_property, "\nnode action", node_action)

    if node_property == "NONE":
        return False
    if node_action == "NONE":
        return False
    if node_property == "OPERATING" and node_action == "PATCHING":
        # Operating State cannot PATCH
        return False
    if node_property != "OPERATING" and node_action not in [
        "NONE",
        "PATCHING",
    ]:
        # Software States can only do Nothing or Patch
        return False
    return True


def is_valid_acl_action(action: List[int]) -> bool:
    """
    Is the ACL action an actual valid action.

    Only uses information about the action to determine if the action has an effect.

    Does NOT consider:
        - Trying to create identical rules
        - Trying to create a rule which is a subset of another rule (caused by "ANY")

    :param action: Agent action, formatted as a list of ints, for more information check out
        `primaite.environment.primaite_env.Primaite`
    :type action: List[int]
    :return: Whether the action is valid
    :rtype: bool
    """
    action_r = transform_action_acl_readable(action)

    action_decision = action_r[0]
    action_permission = action_r[1]
    action_source_id = action_r[2]
    action_destination_id = action_r[3]

    if action_decision == "NONE":
        return False
    if action_source_id == action_destination_id and action_source_id != "ANY" and action_destination_id != "ANY":
        # ACL rule towards itself
        return False
    if action_permission == "DENY":
        # DENY is unnecessary, we can create and delete allow rules instead
        # No allow rule = blocked/DENY by feault. ALLOW overrides existing DENY.
        return False

    return True


def is_valid_acl_action_extra(action: List[int]) -> bool:
    """
    Harsher version of valid acl actions, does not allow action.

    :param action: Agent action, formatted as a list of ints, for more information check out
        `primaite.environment.primaite_env.Primaite`
    :type action: List[int]
    :return: Whether the action is valid
    :rtype: bool
    """
    if is_valid_acl_action(action) is False:
        return False

    action_r = transform_action_acl_readable(action)
    action_protocol = action_r[4]
    action_port = action_r[5]

    # Don't allow protocols or ports to be ANY
    # in the future we might want to do the opposite, and only have ANY option for ports and service
    if action_protocol == "ANY":
        return False
    if action_port == "ANY":
        return False

    return True


def transform_change_obs_readable(obs: np.ndarray) -> List[List[Union[str, int]]]:
    """Transform list of transactions to readable list of each observation property.

    example:
    np.array([[1,2,1,3],[2,1,1,1]]) -> [[1, 2], ['OFF', 'ON'], ['GOOD', 'GOOD'], ['COMPROMISED', 'GOOD']]

    :param obs: Raw observation from the environment.
    :type obs: np.ndarray
    :return: The same observation, but the encoded integer values are replaced with readable names.
    :rtype: List[List[Union[str, int]]]
    """
    ids = [i for i in obs[:, 0]]
    operating_states = [HardwareState(i).name for i in obs[:, 1]]
    os_states = [SoftwareState(i).name for i in obs[:, 2]]
    new_obs = [ids, operating_states, os_states]

    for service in range(4, obs.shape[1]):
        # Links bit/s don't have a service state
        service_states = [SoftwareState(i).name if i <= 4 else i for i in obs[:, service]]
        new_obs.append(service_states)

    return new_obs


def transform_obs_readable(obs: np.ndarray) -> List[List[Union[str, int]]]:
    """Transform observation to readable format.

    example
    np.array([[1,2,1,3],[2,1,1,1]]) -> [[1, 'OFF', 'GOOD', 'COMPROMISED'], [2, 'ON', 'GOOD', 'GOOD']]

    :param obs: Raw observation from the environment.
    :type obs: np.ndarray
    :return: The same observation, but the encoded integer values are replaced with readable names.
    :rtype: List[List[Union[str, int]]]
    """
    changed_obs = transform_change_obs_readable(obs)
    new_obs = list(zip(*changed_obs))
    # Convert list of tuples to list of lists
    new_obs = [list(i) for i in new_obs]

    return new_obs


def convert_to_new_obs(obs: np.ndarray, num_nodes: int = 10) -> np.ndarray:
    """Convert original gym Box observation space to new multiDiscrete observation space.

    :param obs: observation in the 'old' (NodeLinkTable) format
    :type obs: np.ndarray
    :param num_nodes: number of nodes in the network, defaults to 10
    :type num_nodes: int, optional
    :return: reformatted observation
    :rtype: np.ndarray
    """
    # Remove ID columns, remove links and flatten to MultiDiscrete observation space
    new_obs = obs[:num_nodes, 1:].flatten()
    return new_obs


def convert_to_old_obs(obs: np.ndarray, num_nodes: int = 10, num_links: int = 10, num_services: int = 1) -> np.ndarray:
    """Convert to old observation.

    Links filled with 0's as no information is included in new observation space.

    example:
    obs = array([1, 1, 1, 1, 1, 1, 1, 1, 1,  ..., 1, 1, 1])

    new_obs = array([[ 1,  1,  1,  1],
                     [ 2,  1,  1,  1],
                     [ 3,  1,  1,  1],
                     ...
                    [20,  0,  0,  0]])

    :param obs: observation in the 'new' (MultiDiscrete) format
    :type obs: np.ndarray
    :param num_nodes: number of nodes in the network, defaults to 10
    :type num_nodes: int, optional
    :param num_links: number of links in the network, defaults to 10
    :type num_links: int, optional
    :param num_services: number of services on the network, defaults to 1
    :type num_services: int, optional
    :return: 2-d BOX observation space, in the same format as NodeLinkTable
    :rtype: np.ndarray
    """
    # Convert back to more readable, original format
    reshaped_nodes = obs[:-num_links].reshape(num_nodes, num_services + 2)

    # Add empty links back and add node ID back
    s = np.zeros(
        [reshaped_nodes.shape[0] + num_links, reshaped_nodes.shape[1] + 1],
        dtype=np.int64,
    )
    s[:, 0] = range(1, num_nodes + num_links + 1)  # Adding ID back
    s[:num_nodes, 1:] = reshaped_nodes  # put values back in
    new_obs = s

    # Add links back in
    links = obs[-num_links:]
    # Links will be added to the last protocol/service slot but they are not specific to that service
    new_obs[num_nodes:, -1] = links

    return new_obs


def describe_obs_change(
    obs1: np.ndarray, obs2: np.ndarray, num_nodes: int = 10, num_links: int = 10, num_services: int = 1
) -> str:
    """Build a string describing the difference between two observations.

    example:
    obs_1 = array([[1, 1, 1, 1, 3], [2, 1, 1, 1, 1]])
    obs_2 = array([[1, 1, 1, 1, 1], [2, 1, 1, 1, 1]])
    output = 'ID 1: SERVICE 2 set to GOOD'

    :param obs1: First observation
    :type obs1: np.ndarray
    :param obs2: Second observation
    :type obs2: np.ndarray
    :param num_nodes: How many nodes are in the network laydown, defaults to 10
    :type num_nodes: int, optional
    :param num_links: How many links are in the network laydown, defaults to 10
    :type num_links: int, optional
    :param num_services: How many services are configured for this scenario, defaults to 1
    :type num_services: int, optional
    :return: A multi-line string with a human-readable description of the difference.
    :rtype: str
    """
    obs1 = convert_to_old_obs(obs1, num_nodes, num_links, num_services)
    obs2 = convert_to_old_obs(obs2, num_nodes, num_links, num_services)
    list_of_changes = []
    for n, row in enumerate(obs1 - obs2):
        if row.any() != 0:
            relevant_changes = np.where(row != 0, obs2[n], -1)
            relevant_changes[0] = obs2[n, 0]  # ID is always relevant
            is_link = relevant_changes[0] > num_nodes
            desc = _describe_obs_change_helper(relevant_changes, is_link)
            list_of_changes.append(desc)

    change_string = "\n ".join(list_of_changes)
    if len(list_of_changes) > 0:
        change_string = "\n " + change_string
    return change_string


def _describe_obs_change_helper(obs_change: List[int], is_link: bool) -> str:
    """
    Helper funcion to describe what has changed.

    example:
    [ 1 -1 -1 -1  1] -> "ID 1: Service 1 changed to GOOD"

    Handles multiple changes e.g. 'ID 1: SERVICE 1 changed to PATCHING. SERVICE 2 set to GOOD.'

    :param obs_change: List of integers generated within the `describe_obs_change` function. It should correspond to one
        row of the observation table, and have `-1` at locations where the observation hasn't changed, and the new
        status where it has changed.
    :type obs_change: List[int]
    :param is_link: Whether the row of the observation space corresponds to a link. False means it represents a node.
    :type is_link: bool
    :return: A human-readable description of the difference between the two observation rows.
    :rtype: str
    """
    # Indexes where a change has occured, not including 0th index
    index_changed = [i for i in range(1, len(obs_change)) if obs_change[i] != -1]
    # Node pol types, Indexes >= 3 are service nodes
    NodePOLTypes = [NodePOLType(i).name if i < 3 else NodePOLType(3).name + " " + str(i - 3) for i in index_changed]
    # Account for hardware states, software sattes and links
    states = [
        LinkStatus(obs_change[i]).name
        if is_link
        else HardwareState(obs_change[i]).name
        if i == 1
        else SoftwareState(obs_change[i]).name
        for i in index_changed
    ]

    if not is_link:
        desc = f"ID {obs_change[0]}:"
        for node_pol_type, state in list(zip(NodePOLTypes, states)):
            desc = desc + " " + node_pol_type + " changed to " + state + "."
    else:
        desc = f"ID {obs_change[0]}: Link traffic changed to {states[0]}."

    return desc


def transform_action_node_enum(action: List[Union[str, int]]) -> List[int]:
    """Convert a node action from readable string format, to enumerated format.

    example:
    [1, 'SERVICE', 'PATCHING', 0] -> [1, 3, 1, 0]
    :param action: Action in 'readable' format
    :type action: List[Union[str,int]]
    :return: Action with verbs encoded as ints
    :rtype: List[int]
    """
    action_node_id = action[0]
    action_node_property = NodePOLType[action[1]].value

    if action[1] == "OPERATING":
        property_action = NodeHardwareAction[action[2]].value
    elif action[1] == "OS" or action[1] == "SERVICE":
        property_action = NodeSoftwareAction[action[2]].value
    else:
        property_action = 0

    action_service_index = action[3]

    new_action = [
        action_node_id,
        action_node_property,
        property_action,
        action_service_index,
    ]

    return new_action


def transform_action_acl_enum(action: List[Union[int, str]]) -> np.ndarray:
    """
    Convert acl action from readable str format, to enumerated format.

    :param action: ACL-based action expressed as a list of human-readable ints and strings
    :type action: List[Union[int,str]]
    :return: The same action but encoded to contain only integers.
    :rtype: np.ndarray
    """
    action_decisions = {"NONE": 0, "CREATE": 1, "DELETE": 2}
    action_permissions = {"DENY": 0, "ALLOW": 1}

    action_decision = action_decisions[action[0]]
    action_permission = action_permissions[action[1]]

    # For IPs, Ports and Protocols, ANY has value 0, otherwise its just an index
    new_action = [action_decision, action_permission] + list(action[2:6])
    for n, val in enumerate(list(action[2:6])):
        if val == "ANY":
            new_action[n + 2] = 0

    new_action = np.array(new_action)
    return new_action


def get_node_of_ip(ip: str, node_dict: Dict[str, NodeUnion]) -> str:
    """Get the node ID of an IP address.

    node_dict: dictionary of nodes where key is ID, and value is the node (can be ontained from env.nodes)

    :param ip: The IP address of the node whose ID is required
    :type ip: str
    :param node_dict: The environment's node registry dictionary
    :type node_dict: Dict[str,NodeUnion]
    :return: The key from the registry dict that corresponds to the node with the IP adress provided by `ip`
    :rtype: str
    """
    for node_key, node_value in node_dict.items():
        node_ip = node_value.ip_address
        if node_ip == ip:
            return node_key


def get_new_action(old_action: np.ndarray, action_dict: Dict[int, List]) -> int:
    """
    Get new action (e.g. 32) from old action e.g. [1,1,1,0].

    Old_action can be either node or acl action type

    :param old_action: Action expressed as a list of choices, eg. [1,1,1,0]
    :type old_action: np.ndarray
    :param action_dict: Dictionary for translating the multidiscrete actions into the list-based actions.
    :type action_dict: Dict[int,List]
    :return: Action key correspoinding to the input `old_action`
    :rtype: int
    """
    for key, val in action_dict.items():
        if list(val) == list(old_action):
            return key
    # Not all possible actions are included in dict, only valid action are
    # if action is not in the dict, its an invalid action so return 0
    return 0
