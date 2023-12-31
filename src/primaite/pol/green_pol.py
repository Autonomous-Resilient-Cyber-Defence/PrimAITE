# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""Implements Pattern of Life on the network (nodes and links)."""
from typing import Dict

from networkx import MultiGraph, shortest_path

from primaite.acl.access_control_list import AccessControlList
from primaite.common.custom_typing import NodeUnion
from primaite.common.enums import HardwareState, NodePOLType, NodeType, SoftwareState
from primaite.links.link import Link
from primaite.nodes.active_node import ActiveNode
from primaite.nodes.node_state_instruction_green import NodeStateInstructionGreen
from primaite.nodes.service_node import ServiceNode
from primaite.pol.ier import IER

_VERBOSE: bool = False


def apply_iers(
    network: MultiGraph,
    nodes: Dict[str, NodeUnion],
    links: Dict[str, Link],
    iers: Dict[str, IER],
    acl: AccessControlList,
    step: int,
) -> None:
    """
    Applies IERs to the links (link pattern of life).

    Args:
        network: The network modelled in the environment
        nodes: The nodes within the environment
        links: The links within the environment
        iers: The IERs to apply to the links
        acl: The Access Control List
        step: The step number.
    """
    if _VERBOSE:
        print("Applying IERs")

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
            # TODO: should be using isinstance rather than checking node type attribute. IE. just because it's a switch
            # doesn't mean it has a software state? It could be a PassiveNode or ActiveNode
            if source_node.node_type == NodeType.SWITCH:
                # It's a switch
                if (
                    source_node.hardware_state == HardwareState.ON
                    and source_node.software_state != SoftwareState.PATCHING
                ):
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
                if (
                    source_node.hardware_state == HardwareState.ON
                    and source_node.software_state != SoftwareState.PATCHING
                ):
                    if source_node.has_service(protocol):
                        if source_node.service_running(protocol) and not source_node.service_is_overwhelmed(protocol):
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
                if dest_node.hardware_state == HardwareState.ON and dest_node.software_state != SoftwareState.PATCHING:
                    dest_valid = True
                else:
                    # IER no longer valid
                    dest_valid = False
            elif dest_node.node_type == NodeType.ACTUATOR:
                # It's an actuator
                pass
            else:
                # It's not a switch or an actuator (so active node)
                if dest_node.hardware_state == HardwareState.ON and dest_node.software_state != SoftwareState.PATCHING:
                    if dest_node.has_service(protocol):
                        if dest_node.service_running(protocol) and not dest_node.service_is_overwhelmed(protocol):
                            dest_valid = True
                        else:
                            dest_valid = False
                    else:
                        # Do nothing - IER is not valid on this node
                        # (This shouldn't happen if the IER has been written correctly)
                        dest_valid = False
                else:
                    # Do nothing - IER no longer valid
                    dest_valid = False

            # 3. Check that the ACL doesn't block it
            acl_block = acl.is_blocked(source_node.ip_address, dest_node.ip_address, protocol, port)
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
                for node in path_node_list:
                    if node.hardware_state != HardwareState.ON or node.software_state == SoftwareState.PATCHING:
                        path_valid = False

                if path_valid:
                    if _VERBOSE:
                        print("Applying IER to link(s)")
                    count = 0
                    link_capacity_exceeded = False

                    # Check that the link capacity is not exceeded by the new load
                    while count < path_node_list_length - 1:
                        # Get the link between the next two nodes
                        edge_dict = network.get_edge_data(path_node_list[count], path_node_list[count + 1])
                        link_id = edge_dict[0].get("id")
                        link = links[link_id]
                        # Check whether the new load exceeds the bandwidth
                        if (link.get_current_load() + load) > link.get_bandwidth():
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
                else:
                    # One of the nodes is not operational
                    if _VERBOSE:
                        print("Path not valid - one or more nodes not operational")
                    pass

            else:
                if _VERBOSE:
                    print("Source, Dest or ACL were not valid")
                pass
            # ------------------------------------
        else:
            # Do nothing - IER no longer valid
            pass


def apply_node_pol(
    nodes: Dict[str, NodeUnion],
    node_pol: Dict[str, NodeStateInstructionGreen],
    step: int,
) -> None:
    """
    Applies node pattern of life.

    Args:
        nodes: The nodes within the environment
        node_pol: The node pattern of life to apply
        step: The step number.
    """
    if _VERBOSE:
        print("Applying Node PoL")

    for key, node_instruction in node_pol.items():
        start_step = node_instruction.get_start_step()
        stop_step = node_instruction.get_end_step()
        node_id = node_instruction.get_node_id()
        node_pol_type = node_instruction.get_node_pol_type()
        service_name = node_instruction.get_service_name()
        state = node_instruction.get_state()

        if step >= start_step and step <= stop_step:
            # continue --------------------------
            node = nodes[node_id]

            if node_pol_type == NodePOLType.OPERATING:
                # Change hardware state
                node.hardware_state = state
            elif node_pol_type == NodePOLType.OS:
                # Change OS state
                # Don't allow PoL to fix something that is compromised. Only the Blue agent can do this
                if isinstance(node, ActiveNode) or isinstance(node, ServiceNode):
                    node.set_software_state_if_not_compromised(state)
            elif node_pol_type == NodePOLType.SERVICE:
                # Change a service state
                # Don't allow PoL to fix something that is compromised. Only the Blue agent can do this
                if isinstance(node, ServiceNode):
                    node.set_service_state_if_not_compromised(service_name, state)
            else:
                # Change the file system status
                if isinstance(node, ActiveNode) or isinstance(node, ServiceNode):
                    node.set_file_system_state_if_not_compromised(state)
        else:
            # PoL is not valid in this time step
            pass
