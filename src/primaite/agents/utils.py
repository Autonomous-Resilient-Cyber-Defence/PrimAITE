import logging
import os.path
from datetime import datetime

import numpy as np
import yaml

from primaite.common.config_values_main import ConfigValuesMain
from primaite.common.enums import (
    ActionType,
    HardwareState,
    LinkStatus,
    NodeHardwareAction,
    NodePOLType,
    NodeSoftwareAction,
    SoftwareState,
)


def load_config_values(config_path):
    """Loads the config values from the main config file into a config object."""
    config_file_main = open(config_path, "r")
    config_data = yaml.safe_load(config_file_main)
    # Create a config class
    config_values = ConfigValuesMain()

    try:
        # Generic
        config_values.red_agent_identifier = config_data["redAgentIdentifier"]
        config_values.action_type = ActionType[config_data["actionType"]]
        config_values.config_filename_use_case = config_data["configFilename"]
        # Reward values
        # Generic
        config_values.all_ok = float(config_data["allOk"])
        # Node Operating State
        config_values.off_should_be_on = float(config_data["offShouldBeOn"])
        config_values.off_should_be_resetting = float(
            config_data["offShouldBeResetting"]
        )
        config_values.on_should_be_off = float(config_data["onShouldBeOff"])
        config_values.on_should_be_resetting = float(config_data["onShouldBeResetting"])
        config_values.resetting_should_be_on = float(config_data["resettingShouldBeOn"])
        config_values.resetting_should_be_off = float(
            config_data["resettingShouldBeOff"]
        )
        # Node O/S or Service State
        config_values.good_should_be_patching = float(
            config_data["goodShouldBePatching"]
        )
        config_values.good_should_be_compromised = float(
            config_data["goodShouldBeCompromised"]
        )
        config_values.good_should_be_overwhelmed = float(
            config_data["goodShouldBeOverwhelmed"]
        )
        config_values.patching_should_be_good = float(
            config_data["patchingShouldBeGood"]
        )
        config_values.patching_should_be_compromised = float(
            config_data["patchingShouldBeCompromised"]
        )
        config_values.patching_should_be_overwhelmed = float(
            config_data["patchingShouldBeOverwhelmed"]
        )
        config_values.compromised_should_be_good = float(
            config_data["compromisedShouldBeGood"]
        )
        config_values.compromised_should_be_patching = float(
            config_data["compromisedShouldBePatching"]
        )
        config_values.compromised_should_be_overwhelmed = float(
            config_data["compromisedShouldBeOverwhelmed"]
        )
        config_values.compromised = float(config_data["compromised"])
        config_values.overwhelmed_should_be_good = float(
            config_data["overwhelmedShouldBeGood"]
        )
        config_values.overwhelmed_should_be_patching = float(
            config_data["overwhelmedShouldBePatching"]
        )
        config_values.overwhelmed_should_be_compromised = float(
            config_data["overwhelmedShouldBeCompromised"]
        )
        config_values.overwhelmed = float(config_data["overwhelmed"])
        # IER status
        config_values.red_ier_running = float(config_data["redIerRunning"])
        config_values.green_ier_blocked = float(config_data["greenIerBlocked"])
        # Patching / Reset durations
        config_values.os_patching_duration = int(config_data["osPatchingDuration"])
        config_values.node_reset_duration = int(config_data["nodeResetDuration"])
        config_values.service_patching_duration = int(
            config_data["servicePatchingDuration"]
        )

    except Exception as e:
        print(f"Could not save load config data: {e} ")

    return config_values


def configure_logging(log_name):
    """Configures logging."""
    try:
        now = datetime.now()  # current date and time
        time = now.strftime("%Y%m%d_%H%M%S")
        filename = "/app/logs/" + log_name + "/" + time + ".log"
        path = f"/app/logs/{log_name}"
        is_dir = os.path.isdir(path)
        if not is_dir:
            os.makedirs(path)
        logging.basicConfig(
            filename=filename,
            filemode="w",
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.INFO,
        )
    except Exception as e:
        print("ERROR: Could not start logging", e)


def transform_change_obs_readable(obs):
    """Transform list of transactions to readable list of each observation property.

    example:
    np.array([[1,2,1,3],[2,1,1,1]]) -> [[1, 2], ['OFF', 'ON'], ['GOOD', 'GOOD'], ['COMPROMISED', 'GOOD']]
    """
    ids = [i for i in obs[:, 0]]
    operating_states = [HardwareState(i).name for i in obs[:, 1]]
    os_states = [SoftwareState(i).name for i in obs[:, 2]]
    new_obs = [ids, operating_states, os_states]

    for service in range(3, obs.shape[1]):
        # Links bit/s don't have a service state
        service_states = [
            SoftwareState(i).name if i <= 4 else i for i in obs[:, service]
        ]
        new_obs.append(service_states)

    return new_obs


def transform_obs_readable(obs):
    """
    Transform obs readable function.

    example:
    np.array([[1,2,1,3],[2,1,1,1]]) -> [[1, 'OFF', 'GOOD', 'COMPROMISED'], [2, 'ON', 'GOOD', 'GOOD']].
    """
    changed_obs = transform_change_obs_readable(obs)
    new_obs = list(zip(*changed_obs))
    # Convert list of tuples to list of lists
    new_obs = [list(i) for i in new_obs]

    return new_obs


def convert_to_new_obs(obs, num_nodes=10):
    """Convert original gym Box observation space to new multiDiscrete observation space."""
    # Remove ID columns, remove links and flatten to MultiDiscrete observation space
    new_obs = obs[:num_nodes, 1:].flatten()
    return new_obs


def convert_to_old_obs(obs, num_nodes=10, num_links=10, num_services=1):
    """
    Convert to old observation, links filled with 0's as no information is included in new observation space.

    example:
    obs = array([1, 1, 1, 1, 1, 1, 1, 1, 1,  ..., 1, 1, 1])

    new_obs = array([[ 1,  1,  1,  1],
                     [ 2,  1,  1,  1],
                     [ 3,  1,  1,  1],
                     ...
                    [20,  0,  0,  0]])
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


def describe_obs_change(obs1, obs2, num_nodes=10, num_links=10, num_services=1):
    """Return string describing change between two observations.

    example:
    obs_1 = array([[1, 1, 1, 1, 3], [2, 1, 1, 1, 1]])
    obs_2 = array([[1, 1, 1, 1, 1], [2, 1, 1, 1, 1]])
    output = 'ID 1: SERVICE 2 set to GOOD'
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


def _describe_obs_change_helper(obs_change, is_link):
    """
    Helper funcion to describe what has changed.

    example:
    [ 1 -1 -1 -1  1] -> "ID 1: Service 1 changed to GOOD"

    Handles multiple changes e.g. 'ID 1: SERVICE 1 changed to PATCHING. SERVICE 2 set to GOOD.'
    """
    # Indexes where a change has occured, not including 0th index
    index_changed = [i for i in range(1, len(obs_change)) if obs_change[i] != -1]
    # Node pol types, Indexes >= 3 are service nodes
    node_pol_types = [
        NodePOLType(i).name if i < 3 else NodePOLType(3).name + " " + str(i - 3)
        for i in index_changed
    ]
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
        for node_pol_type, state in list(zip(node_pol_types, states)):
            desc = desc + " " + node_pol_type + " changed to " + state + "."
    else:
        desc = f"ID {obs_change[0]}: Link traffic changed to {states[0]}."

    return desc


def transform_action_node_enum(action):
    """
    Convert a node action from readable string format, to enumerated format.

    example:
    [1, 'SERVICE', 'PATCHING', 0] -> [1, 3, 1, 0]
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


def transform_action_node_readable(action):
    """
    Convert a node action from enumerated format to readable format.

    example:
    [1, 3, 1, 0] -> [1, 'SERVICE', 'PATCHING', 0]
    """
    action_node_property = NodePOLType(action[1]).name

    if action_node_property == "OPERATING":
        property_action = NodeHardwareAction(action[2]).name
    elif (action_node_property == "OS" or action_node_property == "SERVICE") and action[
        2
    ] <= 1:
        property_action = NodeSoftwareAction(action[2]).name
    else:
        property_action = "NONE"

    new_action = [action[0], action_node_property, property_action, action[3]]
    return new_action


def node_action_description(action):
    """Generate string describing a node-based action."""
    if isinstance(action[1], (int, np.int64)):
        # transform action to readable format
        action = transform_action_node_readable(action)

    node_id = action[0]
    node_property = action[1]
    property_action = action[2]
    service_id = action[3]

    if property_action == "NONE":
        return ""
    if node_property == "OPERATING" or node_property == "OS":
        description = f"NODE {node_id}, {node_property}, SET TO {property_action}"
    elif node_property == "SERVICE":
        description = (
            f"NODE {node_id} FROM SERVICE {service_id}, SET TO {property_action}"
        )
    else:
        return ""

    return description


def transform_action_acl_readable(action):
    """
    Transform an ACL action to a more readable format.

    example:
    [0, 1, 2, 5, 0, 1] -> ['NONE', 'ALLOW', 2, 5, 'ANY', 1]
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


def transform_action_acl_enum(action):
    """Convert a acl action from readable string format, to enumerated format."""
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


def acl_action_description(action):
    """Generate string describing a acl-based action."""
    if isinstance(action[0], (int, np.int64)):
        # transform action to readable format
        action = transform_action_acl_readable(action)
    if action[0] == "NONE":
        description = "NO ACL RULE APPLIED"
    else:
        description = (
            f"{action[0]} RULE: {action[1]} traffic from IP {action[2]} to IP {action[3]},"
            f" for protocol/service index {action[4]} on port index {action[5]}"
        )

    return description


def get_node_of_ip(ip, node_dict):
    """
    Get the node ID of an IP address.

    node_dict: dictionary of nodes where key is ID, and value is the node (can be ontained from env.nodes)
    """
    for node_key, node_value in node_dict.items():
        node_ip = node_value.get_ip_address()
        if node_ip == ip:
            return node_key


def is_valid_node_action(action):
    """Is the node action an actual valid action.

    Only uses information about the action to determine if the action has an effect

    Does NOT consider:
    - Node ID not valid to perform an operation - e.g. selected node has no service so cannot patch
    - Node already being in that state (turning an ON node ON)
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
    if node_property != "OPERATING" and node_action not in ["NONE", "PATCHING"]:
        # Software States can only do Nothing or Patch
        return False
    return True


def is_valid_acl_action(action):
    """
    Is the ACL action an actual valid action.

    Only uses information about the action to determine if the action has an effect.

    Does NOT consider:
        - Trying to create identical rules
        - Trying to create a rule which is a subset of another rule (caused by "ANY")
    """
    action_r = transform_action_acl_readable(action)

    action_decision = action_r[0]
    action_permission = action_r[1]
    action_source_id = action_r[2]
    action_destination_id = action_r[3]

    if action_decision == "NONE":
        return False
    if (
        action_source_id == action_destination_id
        and action_source_id != "ANY"
        and action_destination_id != "ANY"
    ):
        # ACL rule towards itself
        return False
    if action_permission == "DENY":
        # DENY is unnecessary, we can create and delete allow rules instead
        # No allow rule = blocked/DENY by feault. ALLOW overrides existing DENY.
        return False

    return True


def is_valid_acl_action_extra(action):
    """Harsher version of valid acl actions, does not allow action."""
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


def get_new_action(old_action, action_dict):
    """Get new action (e.g. 32) from old action e.g. [1,1,1,0].

    old_action can be either node or acl action type.
    """
    for key, val in action_dict.items():
        if list(val) == list(old_action):
            return key
    # Not all possible actions are included in dict, only valid action are
    # if action is not in the dict, its an invalid action so return 0
    return 0


def get_action_description(action, action_dict):
    """Get a string describing/explaining what an action is doing in words."""
    action_array = action_dict[action]
    if len(action_array) == 4:
        # node actions have length 4
        action_description = node_action_description(action_array)
    elif len(action_array) == 6:
        # acl actions have length 6
        action_description = acl_action_description(action_array)
    else:
        # Should never happen
        action_description = "Unrecognised action"

    return action_description
