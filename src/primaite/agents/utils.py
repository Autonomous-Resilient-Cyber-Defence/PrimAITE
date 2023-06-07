from primaite.common.enums import NodeHardwareAction, NodePOLType, NodeSoftwareAction


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
