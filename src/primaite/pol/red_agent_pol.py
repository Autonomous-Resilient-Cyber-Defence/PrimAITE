# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""Implements POL on the network (nodes and links) resulting from the red agent attack."""
from typing import Dict

from networkx import MultiGraph, shortest_path

from primaite.acl.access_control_list import AccessControlList
from primaite.common.custom_typing import NodeUnion
from primaite.common.enums import (
    HardwareState,
    NodePOLInitiator,
    NodePOLType,
    NodeType,
    SoftwareState,
)
from primaite.links.link import Link
from primaite.nodes.active_node import ActiveNode
from primaite.nodes.node_state_instruction_red import NodeStateInstructionRed
from primaite.nodes.service_node import ServiceNode
from primaite.pol.ier import IER

_VERBOSE = False


def apply_red_agent_iers(
    network: MultiGraph,
    nodes: Dict[str, NodeUnion],
    links: Dict[str, Link],
    iers: Dict[str, IER],
    acl: AccessControlList,
    step: int,
):
    """
    Applies IERs to the links (link POL) resulting from red agent attack.

    Args:
        network: The network modelled in the environment
        nodes: The nodes within the environment
        links: The links within the environment
        iers: The red agent IERs to apply to the links
        acl: The Access Control List
        step: The step number.
    """
    # Go through each IER and check the conditions for it being applied
    # If everything is in place, apply the IER protocol load to the relevant links
    for ier_key, ier_value in iers.items():
        start_step = ier_value.get_start_step()
        stop_step = ier_value.get_end_step()
        protocol = ier_value.get_protocol()
        port = ier_value.get_port()
        load = ier_value.get_load()
        source_node_id = ier_value.get_source_node_id()
        dest_node_id = ier_value.get_dest_node_id()

        # Need to set the running status to false first for all IERs
        ier_value.set_is_running(False)

        source_valid = True
        dest_valid = True
        acl_block = False

        if step >= start_step and step <= stop_step:
            # continue --------------------------

            # Get the source and destination node for this link
            source_node = nodes[source_node_id]
            dest_node = nodes[dest_node_id]

            # 1. Check the source node situation
            if source_node.node_type == NodeType.SWITCH:
                # It's a switch
                if source_node.hardware_state == HardwareState.ON:
                    source_valid = True
                else:
                    # IER no longer valid
                    source_valid = False
            elif source_node.node_type == NodeType.ACTUATOR:
                # It's an actuator
                # TO DO
                pass
            else:
                # It's not a switch or an actuator (so active node)
                if source_node.hardware_state == HardwareState.ON:
                    if source_node.has_service(protocol):
                        # Red agents IERs can only be valid if the source service is in a compromised state
                        if (
                            source_node.get_service_state(protocol)
                            == SoftwareState.COMPROMISED
                        ):
                            source_valid = True
                        else:
                            source_valid = False
                    else:
                        # Do nothing - IER is not valid on this node
                        # (This shouldn't happen if the IER has been written correctly)
                        source_valid = False
                else:
                    # Do nothing - IER no longer valid
                    source_valid = False

            # 2. Check the dest node situation
            if dest_node.node_type == NodeType.SWITCH:
                # It's a switch
                if dest_node.hardware_state == HardwareState.ON:
                    dest_valid = True
                else:
                    # IER no longer valid
                    dest_valid = False
            elif dest_node.node_type == NodeType.ACTUATOR:
                # It's an actuator
                pass
            else:
                # It's not a switch or an actuator (so active node)
                if dest_node.hardware_state == HardwareState.ON:
                    if dest_node.has_service(protocol):
                        # We don't care what state the destination service is in for an IER
                        dest_valid = True
                    else:
                        # Do nothing - IER is not valid on this node
                        # (This shouldn't happen if the IER has been written correctly)
                        dest_valid = False
                else:
                    # Do nothing - IER no longer valid
                    dest_valid = False

            # 3. Check that the ACL doesn't block it
            acl_block = acl.is_blocked(
                source_node.ip_address, dest_node.ip_address, protocol, port
            )
            if acl_block:
                if _VERBOSE:
                    print(
                        "ACL block on source: "
                        + source_node.ip_address
                        + ", dest: "
                        + dest_node.ip_address
                        + ", protocol: "
                        + protocol
                        + ", port: "
                        + port
                    )
            else:
                if _VERBOSE:
                    print("No ACL block")

            # Check whether both the source and destination are valid, and there's no ACL block
            if source_valid and dest_valid and not acl_block:
                # Load up the link(s) with the traffic

                if _VERBOSE:
                    print("Source, Dest and ACL valid")

                # Get the shortest path (i.e. nodes) between source and destination
                path_node_list = shortest_path(network, source_node, dest_node)
                path_node_list_length = len(path_node_list)
                path_valid = True

                # We might have a switch in the path, so check all nodes are operational
                # We're assuming here that red agents can get past switches that are patching
                for node in path_node_list:
                    if node.hardware_state != HardwareState.ON:
                        path_valid = False

                if path_valid:
                    if _VERBOSE:
                        print("Applying IER to link(s)")
                    count = 0
                    link_capacity_exceeded = False

                    # Check that the link capacity is not exceeded by the new load
                    while count < path_node_list_length - 1:
                        # Get the link between the next two nodes
                        edge_dict = network.get_edge_data(
                            path_node_list[count], path_node_list[count + 1]
                        )
                        link_id = edge_dict[0].get("id")
                        link = links[link_id]
                        # Check whether the new load exceeds the bandwidth
                        if (
                            link.get_current_load() + load
                        ) > link.get_bandwidth():
                            link_capacity_exceeded = True
                            if _VERBOSE:
                                print("Link capacity exceeded")
                            pass
                        count += 1

                    # Check whether the link capacity for any links on this path have been exceeded
                    if link_capacity_exceeded == False:
                        # Now apply the new loads to the links
                        count = 0
                        while count < path_node_list_length - 1:
                            # Get the link between the next two nodes
                            edge_dict = network.get_edge_data(
                                path_node_list[count],
                                path_node_list[count + 1],
                            )
                            link_id = edge_dict[0].get("id")
                            link = links[link_id]
                            # Add the load from this IER
                            link.add_protocol_load(protocol, load)
                            count += 1
                        # This IER is now valid, so set it to running
                        ier_value.set_is_running(True)
                        if _VERBOSE:
                            print(
                                "Red IER was allowed to run in step "
                                + str(step)
                            )
                else:
                    # One of the nodes is not operational
                    if _VERBOSE:
                        print(
                            "Path not valid - one or more nodes not operational"
                        )
                    pass

            else:
                if _VERBOSE:
                    print(
                        "Red IER was NOT allowed to run in step " + str(step)
                    )
                    print("Source, Dest or ACL were not valid")
                pass
            # ------------------------------------
        else:
            # Do nothing - IER no longer valid
            pass

    pass


def apply_red_agent_node_pol(
    nodes: Dict[str, NodeUnion],
    iers: Dict[str, IER],
    node_pol: Dict[str, NodeStateInstructionRed],
    step: int,
):
    """
    Applies node pattern of life.

    Args:
        nodes: The nodes within the environment
        iers: The red agent IERs
        node_pol: The red agent node pattern of life to apply
        step: The step number.
    """
    if _VERBOSE:
        print("Applying Node Red Agent PoL")

    for key, node_instruction in node_pol.items():
        start_step = node_instruction.get_start_step()
        stop_step = node_instruction.get_end_step()
        target_node_id = node_instruction.get_target_node_id()
        initiator = node_instruction.get_initiator()
        pol_type = node_instruction.get_pol_type()
        service_name = node_instruction.get_service_name()
        state = node_instruction.get_state()
        source_node_id = node_instruction.get_source_node_id()
        source_node_service_name = node_instruction.get_source_node_service()
        source_node_service_state_value = (
            node_instruction.get_source_node_service_state()
        )

        passed_checks = False

        if step >= start_step and step <= stop_step:
            # continue --------------------------
            target_node: NodeUnion = nodes[target_node_id]

            # Based the action taken on the initiator type
            if initiator == NodePOLInitiator.DIRECT:
                # No conditions required, just apply the change
                passed_checks = True
            elif initiator == NodePOLInitiator.IER:
                # Need to check there is a red IER incoming
                passed_checks = is_red_ier_incoming(
                    target_node, iers, pol_type
                )
            elif initiator == NodePOLInitiator.SERVICE:
                # Need to check the condition of a service on another node
                source_node = nodes[source_node_id]
                if source_node.has_service(source_node_service_name):
                    if (
                        source_node.get_service_state(source_node_service_name)
                        == SoftwareState[source_node_service_state_value]
                    ):
                        passed_checks = True
                    else:
                        # Do nothing, no matching state value
                        pass
                else:
                    # Do nothing, service not on this node
                    pass
            else:
                if _VERBOSE:
                    print("Node Red Agent PoL not allowed - misconfiguration")

            # Only apply the PoL if the checks have passed (based on the initiator type)
            if passed_checks:
                # Apply the change
                if pol_type == NodePOLType.OPERATING:
                    # Change hardware state
                    target_node.hardware_state = state
                elif pol_type == NodePOLType.OS:
                    # Change OS state
                    if isinstance(target_node, ActiveNode) or isinstance(
                        target_node, ServiceNode
                    ):
                        target_node.software_state = state
                elif pol_type == NodePOLType.SERVICE:
                    # Change a service state
                    if isinstance(target_node, ServiceNode):
                        target_node.set_service_state(service_name, state)
                else:
                    # Change the file system status
                    if isinstance(target_node, ActiveNode) or isinstance(
                        target_node, ServiceNode
                    ):
                        target_node.set_file_system_state(state)
            else:
                if _VERBOSE:
                    print(
                        "Node Red Agent PoL not allowed - did not pass checks"
                    )
        else:
            # PoL is not valid in this time step
            pass


def is_red_ier_incoming(node, iers, node_pol_type):
    """
    Checks if the RED IER is incoming.

    TODO: Write more descriptive docstring with params and returns.
    """
    node_id = node.node_id

    for ier_key, ier_value in iers.items():
        if (
            ier_value.get_is_running()
            and ier_value.get_dest_node_id() == node_id
        ):
            if (
                node_pol_type == NodePOLType.OPERATING
                or node_pol_type == NodePOLType.OS
                or node_pol_type == NodePOLType.FILE
            ):
                # It's looking to change hardware state, file system or SoftwareState, so valid
                return True
            elif node_pol_type == NodePOLType.SERVICE:
                # Check if the service is present on the node and running
                ier_protocol = ier_value.get_protocol()
                if isinstance(node, ServiceNode):
                    if node.has_service(ier_protocol):
                        if node.service_running(ier_protocol):
                            # Matching service is present and running, so valid
                            return True
                        else:
                            # Service is present, but not running
                            return False
                    else:
                        # Service is not present
                        return False
                else:
                    # Not a service node
                    return False
            else:
                # Shouldn't get here - instruction type is undefined
                return False
        else:
            # The IER destination is not this node, or the IER is not running
            return False
