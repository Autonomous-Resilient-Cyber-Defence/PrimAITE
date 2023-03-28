# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
Implements Pattern of Life on the network (nodes and links) resulting from the red agent attack
"""

from networkx import shortest_path

from common.enums import *
from nodes.active_node import ActiveNode
from nodes.service_node import ServiceNode

_VERBOSE = False

def apply_red_agent_iers(network, nodes, links, iers, acl, step):
    """
    Applies IERs to the links (link pattern of life) resulting from red agent attack

    Args:
        network: The network modelled in the environment
        nodes: The nodes within the environment
        links: The links within the environment
        iers: The red agent IERs to apply to the links
        acl: The Access Control List
        step: The step number
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
            if source_node.get_type() == TYPE.SWITCH:
                # It's a switch
                if source_node.get_state() == HARDWARE_STATE.ON:
                    source_valid = True
                else:
                    # IER no longer valid
                    source_valid = False
            elif source_node.get_type() == TYPE.ACTUATOR:
                # It's an actuator
                # TO DO
                pass
            else:
                # It's not a switch or an actuator (so active node)
                if source_node.get_state() == HARDWARE_STATE.ON:
                    if source_node.has_service(protocol):
                        # Red agents IERs can only be valid if the source service is in a compromised state
                        if source_node.get_service_state(protocol) == SOFTWARE_STATE.COMPROMISED:
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
            if dest_node.get_type() == TYPE.SWITCH:
                # It's a switch
                if dest_node.get_state() == HARDWARE_STATE.ON:
                    dest_valid = True
                else:
                    # IER no longer valid
                    dest_valid = False
            elif dest_node.get_type() == TYPE.ACTUATOR:
                # It's an actuator
                pass
            else:
                # It's not a switch or an actuator (so active node)
                if dest_node.get_state() == HARDWARE_STATE.ON:
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
            acl_block = acl.is_blocked(source_node.get_ip_address(), dest_node.get_ip_address(), protocol, port)
            if acl_block:
                if _VERBOSE:
                    print("ACL block on source: " + source_node.get_ip_address() + ", dest: " + dest_node.get_ip_address() + ", protocol: " + protocol + ", port: " + port)
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
                    if node.get_state() != HARDWARE_STATE.ON:
                        path_valid = False

                
                if path_valid:
                    if _VERBOSE:
                        print("Applying IER to link(s)")
                    count = 0
                    link_capacity_exceeded = False

                    # Check that the link capacity is not exceeded by the new load
                    while count < path_node_list_length - 1:
                        # Get the link between the next two nodes
                        edge_dict = network.get_edge_data(path_node_list[count], path_node_list[count+1])
                        link_id = edge_dict[0].get('id')
                        link = links[link_id]
                        # Check whether the new load exceeds the bandwidth
                        if (link.get_current_load() + load) > link.get_bandwidth():
                            link_capacity_exceeded = True
                            if _VERBOSE:
                                print("Link capacity exceeded")
                            pass
                        count+=1

                    # Check whether the link capacity for any links on this path have been exceeded
                    if link_capacity_exceeded == False:
                        # Now apply the new loads to the links
                        count = 0
                        while count < path_node_list_length - 1:
                            # Get the link between the next two nodes
                            edge_dict = network.get_edge_data(path_node_list[count], path_node_list[count+1])
                            link_id = edge_dict[0].get('id')
                            link = links[link_id]
                            # Add the load from this IER
                            link.add_protocol_load(protocol, load)
                            count+=1
                        # This IER is now valid, so set it to running
                        ier_value.set_is_running(True)
                        if _VERBOSE:
                            print("Red IER was allowed to run in step " + str(step))
                else:
                    # One of the nodes is not operational
                    if _VERBOSE:
                        print("Path not valid - one or more nodes not operational")
                    pass
                
            else:
                if _VERBOSE:
                    print("Red IER was NOT allowed to run in step " + str(step))
                    print("Source, Dest or ACL were not valid")
                pass
            # ------------------------------------
        else:
            # Do nothing - IER no longer valid
            pass

    pass

def apply_red_agent_node_pol(nodes, iers, node_pol, step):
    """
    Applies node pattern of life

    Args:
        nodes: The nodes within the environment
        iers: The red agent IERs
        node_pol: The red agent node pattern of life to apply
        step: The step number
    """

    if _VERBOSE:
        print("Applying Node Red Agent PoL")
    
    for key, node_instruction in node_pol.items():
        start_step = node_instruction.get_start_step()
        stop_step = node_instruction.get_end_step()
        node_id = node_instruction.get_node_id()
        node_pol_type = node_instruction.get_node_pol_type()
        service_name = node_instruction.get_service_name()
        state = node_instruction.get_state()
        is_entry_node = node_instruction.get_is_entry_node()

        if step >= start_step and step <= stop_step:
            # continue -------------------------- 
            node = nodes[node_id]

            # for the red agent, either:
            # 1. the node has to be an entry node, or
            # 2. there is a red IER relevant to that service entering the node with a running status of True
            red_ier_incoming = is_red_ier_incoming(node, iers, node_pol_type)
            if is_entry_node or red_ier_incoming:
                if node_pol_type == NODE_POL_TYPE.OPERATING:
                    # Change operating state
                    node.set_state(state)
                elif node_pol_type == NODE_POL_TYPE.OS:
                    # Change OS state
                    if isinstance(node, ActiveNode) or isinstance(node, ServiceNode):
                        node.set_os_state(state)
                else:
                    # Change a service state
                    if isinstance(node, ServiceNode):
                        node.set_service_state(service_name, state)
            else:
                if _VERBOSE:
                    print("Node Red Agent PoL not allowed - not entry node, or running IER not present")
        else:
            # PoL is not valid in this time step
            pass

def is_red_ier_incoming(node, iers, node_pol_type):

    node_id = node.get_id()

    for ier_key, ier_value in iers.items():     
        if ier_value.get_is_running() and ier_value.get_dest_node_id() == node_id:
            if node_pol_type == NODE_POL_TYPE.OPERATING or node_pol_type == NODE_POL_TYPE.OS:
                # It's looking to change operating state or O/S state, so valid 
                return True
            elif node_pol_type == NODE_POL_TYPE.SERVICE:
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
            

