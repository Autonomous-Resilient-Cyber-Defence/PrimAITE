# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
Implements reward function
"""

from common.enums import *
from nodes.active_node import ActiveNode
from nodes.service_node import ServiceNode

def calculate_reward_function(initial_nodes, final_nodes, reference_nodes, green_iers, red_iers, step_count, config_values):
    """
    Compares the states of the initial and final nodes/links to get a reward

    Args:
        initial_nodes: The nodes before red and blue agents take effect
        final_nodes: The nodes after red and blue agents take effect
        reference_nodes: The nodes if there had been no red or blue effect
        green_iers: The green IERs (should be running)
        red_iers: Should be stopeed (ideally) by the blue agent
        step_count: current step
        config_values: Config values
    """

    reward_value = 0

    # For each node, compare operating state, o/s operating state, service states
    for node_key, final_node in final_nodes.items():
        initial_node = initial_nodes[node_key]
        reference_node = reference_nodes[node_key]
            
        # Operating State
        reward_value += score_node_operating_state(final_node, initial_node, reference_node, config_values)

        # Operating System State
        if (isinstance(final_node, ActiveNode) or isinstance(final_node, ServiceNode)):
            reward_value += score_node_os_state(final_node, initial_node, reference_node, config_values)

        # Service State
        if (isinstance(final_node, ServiceNode)):
            reward_value += score_node_service_state(final_node, initial_node, reference_node, config_values)

        # File System State
        if isinstance(final_node, ActiveNode):
            reward_value += score_node_file_system(final_node, initial_node, reference_node, config_values)
 
    # Go through each red IER - penalise if it is running
    for ier_key, ier_value in red_iers.items():
        start_step = ier_value.get_start_step()
        stop_step = ier_value.get_end_step()
        if step_count >= start_step and step_count <= stop_step:
            if ier_value.get_is_running():
                reward_value += config_values.red_ier_running

    # Go through each green IER - penalise if it's not running (weighted)
    for ier_key, ier_value in green_iers.items():
        start_step = ier_value.get_start_step()
        stop_step = ier_value.get_end_step()
        if step_count >= start_step and step_count <= stop_step:
            if not ier_value.get_is_running():
                reward_value += config_values.green_ier_blocked * ier_value.get_mission_criticality()

    return reward_value


def score_node_operating_state(final_node, initial_node, reference_node, config_values):
    """
    Calculates score relating to the operating state of a node

    Args:
        final_node: The node after red and blue agents take effect
        initial_node: The node before red and blue agents take effect
        reference_node: The node if there had been no red or blue effect
        config_values: Config values
    """
    
    score = 0    
    final_node_operating_state = final_node.get_state()
    initial_node_operating_state = initial_node.get_state()
    reference_node_operating_state = reference_node.get_state()

    if final_node_operating_state == reference_node_operating_state:
        # All is well - we're no different from the reference situation
        score += config_values.all_ok
    else:     
        # We're different from the reference situation
        # Need to compare initial and final state of node (i.e. after red and blue actions)
        if initial_node_operating_state == HARDWARE_STATE.ON:
            if final_node_operating_state == HARDWARE_STATE.OFF:
                score += config_values.off_should_be_on
            elif final_node_operating_state == HARDWARE_STATE.RESETTING:
                score += config_values.resetting_should_be_on
            else:
                pass
        elif initial_node_operating_state == HARDWARE_STATE.OFF:
            if final_node_operating_state == HARDWARE_STATE.ON:
                score += config_values.on_should_be_off
            elif final_node_operating_state == HARDWARE_STATE.RESETTING:
                score += config_values.resetting_should_be_off  
            else:
                pass
        elif initial_node_operating_state == HARDWARE_STATE.RESETTING:
            if final_node_operating_state == HARDWARE_STATE.ON:
                score += config_values.on_should_be_resetting
            elif final_node_operating_state == HARDWARE_STATE.OFF:
                score += config_values.off_should_be_resetting
            elif final_node_operating_state == HARDWARE_STATE.RESETTING:
                score += config_values.resetting
            else:
                pass
        else:
            pass

    return score

def score_node_os_state(final_node, initial_node, reference_node, config_values):
    """
    Calculates score relating to the operating system state of a node

    Args:
        final_node: The node after red and blue agents take effect
        initial_node: The node before red and blue agents take effect
        reference_node: The node if there had been no red or blue effect
        config_values: Config values
    """

    score = 0    
    final_node_os_state = final_node.get_os_state()
    initial_node_os_state = initial_node.get_os_state()
    reference_node_os_state = reference_node.get_os_state()

    if final_node_os_state == reference_node_os_state:
        # All is well - we're no different from the reference situation
        score += config_values.all_ok
    else:  
        # We're different from the reference situation
        # Need to compare initial and final state of node (i.e. after red and blue actions)
        if initial_node_os_state == SOFTWARE_STATE.GOOD:
            if final_node_os_state == SOFTWARE_STATE.PATCHING:
                score += config_values.patching_should_be_good
            elif final_node_os_state == SOFTWARE_STATE.COMPROMISED:
                score += config_values.compromised_should_be_good
            else:
                pass
        elif initial_node_os_state == SOFTWARE_STATE.PATCHING:
            if final_node_os_state == SOFTWARE_STATE.GOOD:
                score += config_values.good_should_be_patching
            elif final_node_os_state == SOFTWARE_STATE.COMPROMISED:
                score += config_values.compromised_should_be_patching  
            elif final_node_os_state == SOFTWARE_STATE.PATCHING:
                score += config_values.patching 
            else:
                pass              
        elif initial_node_os_state == SOFTWARE_STATE.COMPROMISED:
            if final_node_os_state == SOFTWARE_STATE.GOOD:
                score += config_values.good_should_be_compromised
            elif final_node_os_state == SOFTWARE_STATE.PATCHING:
                score += config_values.patching_should_be_compromised
            elif final_node_os_state == SOFTWARE_STATE.COMPROMISED:
                score += config_values.compromised 
            else:
                pass
        else:
            pass

    return score

def score_node_service_state(final_node, initial_node, reference_node, config_values):
    """
    Calculates score relating to the service state(s) of a node

    Args:
        final_node: The node after red and blue agents take effect
        initial_node: The node before red and blue agents take effect
        reference_node: The node if there had been no red or blue effect
        config_values: Config values
    """

    score = 0    
    final_node_services = final_node.get_services()
    initial_node_services = initial_node.get_services()
    reference_node_services = reference_node.get_services()
    
    for service_key, final_service in final_node_services.items():
        reference_service = reference_node_services[service_key]
        initial_service = initial_node_services[service_key]

        if final_service.get_state() == reference_service.get_state():
            # All is well - we're no different from the reference situation
            score += config_values.all_ok
        else:
            # We're different from the reference situation
            # Need to compare initial and final state of node (i.e. after red and blue actions)
            if initial_service.get_state() == SOFTWARE_STATE.GOOD:
                if final_service.get_state() == SOFTWARE_STATE.PATCHING:
                    score += config_values.patching_should_be_good
                elif final_service.get_state() == SOFTWARE_STATE.COMPROMISED:
                    score += config_values.compromised_should_be_good
                elif final_service.get_state() == SOFTWARE_STATE.OVERWHELMED:
                    score += config_values.overwhelmed_should_be_good
                else:
                    pass
            elif initial_service.get_state() == SOFTWARE_STATE.PATCHING:
                if final_service.get_state() == SOFTWARE_STATE.GOOD:
                    score += config_values.good_should_be_patching
                elif final_service.get_state() == SOFTWARE_STATE.COMPROMISED:
                    score += config_values.compromised_should_be_patching    
                elif final_service.get_state() == SOFTWARE_STATE.OVERWHELMED:
                    score += config_values.overwhelmed_should_be_patching 
                elif final_service.get_state() == SOFTWARE_STATE.PATCHING:
                    score += config_values.patching 
                else:
                    pass
            elif initial_service.get_state() == SOFTWARE_STATE.COMPROMISED:
                if final_service.get_state() == SOFTWARE_STATE.GOOD:
                    score += config_values.good_should_be_compromised
                elif final_service.get_state() == SOFTWARE_STATE.PATCHING:
                    score += config_values.patching_should_be_compromised
                elif final_service.get_state() == SOFTWARE_STATE.COMPROMISED:
                    score += config_values.compromised 
                elif final_service.get_state() == SOFTWARE_STATE.OVERWHELMED:
                    score += config_values.overwhelmed_should_be_compromised 
                else:
                    pass
            elif initial_service.get_state() == SOFTWARE_STATE.OVERWHELMED:
                if final_service.get_state() == SOFTWARE_STATE.GOOD:
                    score += config_values.good_should_be_overwhelmed
                elif final_service.get_state() == SOFTWARE_STATE.PATCHING:
                    score += config_values.patching_should_be_overwhelmed
                elif final_service.get_state() == SOFTWARE_STATE.COMPROMISED:
                    score += config_values.compromised_should_be_overwhelmed 
                elif final_service.get_state() == SOFTWARE_STATE.OVERWHELMED:
                    score += config_values.overwhelmed 
                else:
                    pass
            else:
                pass

    return score

def score_node_file_system(final_node, initial_node, reference_node, config_values):
    """
    Calculates score relating to the file system state of a node

    Args:
        final_node: The node after red and blue agents take effect
        initial_node: The node before red and blue agents take effect
        reference_node: The node if there had been no red or blue effect
    """

    score = 0    
    final_node_file_system_state = final_node.get_file_system_state_actual()
    initial_node_file_system_state = initial_node.get_file_system_state_actual()
    reference_node_file_system_state = reference_node.get_file_system_state_actual()

    final_node_scanning_state = final_node.is_scanning_file_system()
    reference_node_scanning_state = reference_node.is_scanning_file_system()

    # File System State
    if final_node_file_system_state == reference_node_file_system_state:
        # All is well - we're no different from the reference situation
        score += config_values.all_ok
    else:  
        # We're different from the reference situation
        # Need to compare initial and final state of node (i.e. after red and blue actions)
        if initial_node_file_system_state == FILE_SYSTEM_STATE.GOOD:
            if final_node_file_system_state == FILE_SYSTEM_STATE.REPAIRING:
                score += config_values.repairing_should_be_good
            elif final_node_file_system_state == FILE_SYSTEM_STATE.RESTORING:
                score += config_values.restoring_should_be_good
            elif final_node_file_system_state == FILE_SYSTEM_STATE.CORRUPT:
                score += config_values.corrupt_should_be_good
            elif final_node_file_system_state == FILE_SYSTEM_STATE.DESTROYED:
                score += config_values.destroyed_should_be_good
            else:
                pass
        elif initial_node_file_system_state == FILE_SYSTEM_STATE.REPAIRING:
            if final_node_file_system_state == FILE_SYSTEM_STATE.GOOD:
                score += config_values.good_should_be_repairing
            elif final_node_file_system_state == FILE_SYSTEM_STATE.RESTORING:
                score += config_values.restoring_should_be_repairing  
            elif final_node_file_system_state == FILE_SYSTEM_STATE.CORRUPT:
                score += config_values.corrupt_should_be_repairing  
            elif final_node_file_system_state == FILE_SYSTEM_STATE.DESTROYED:
                score += config_values.destroyed_should_be_repairing 
            elif final_node_file_system_state == FILE_SYSTEM_STATE.REPAIRING:
                score += config_values.repairing
            else:
                pass              
        elif initial_node_file_system_state == FILE_SYSTEM_STATE.RESTORING:
            if final_node_file_system_state == FILE_SYSTEM_STATE.GOOD:
                score += config_values.good_should_be_restoring
            elif final_node_file_system_state == FILE_SYSTEM_STATE.REPAIRING:
                score += config_values.repairing_should_be_restoring
            elif final_node_file_system_state == FILE_SYSTEM_STATE.CORRUPT:
                score += config_values.corrupt_should_be_restoring
            elif final_node_file_system_state == FILE_SYSTEM_STATE.DESTROYED:
                score += config_values.destroyed_should_be_restoring  
            elif final_node_file_system_state == FILE_SYSTEM_STATE.RESTORING:
                score += config_values.restoring  
            else:
                pass
        elif initial_node_file_system_state == FILE_SYSTEM_STATE.CORRUPT:
            if final_node_file_system_state == FILE_SYSTEM_STATE.GOOD:
                score += config_values.good_should_be_corrupt
            elif final_node_file_system_state == FILE_SYSTEM_STATE.REPAIRING:
                score += config_values.repairing_should_be_corrupt
            elif final_node_file_system_state == FILE_SYSTEM_STATE.RESTORING:
                score += config_values.restoring_should_be_corrupt
            elif final_node_file_system_state == FILE_SYSTEM_STATE.DESTROYED:
                score += config_values.destroyed_should_be_corrupt  
            elif final_node_file_system_state == FILE_SYSTEM_STATE.CORRUPT:
                score += config_values.corrupt  
            else:
                pass
        elif initial_node_file_system_state == FILE_SYSTEM_STATE.DESTROYED:
            if final_node_file_system_state == FILE_SYSTEM_STATE.GOOD:
                score += config_values.good_should_be_destroyed
            elif final_node_file_system_state == FILE_SYSTEM_STATE.REPAIRING:
                score += config_values.repairing_should_be_destroyed
            elif final_node_file_system_state == FILE_SYSTEM_STATE.RESTORING:
                score += config_values.restoring_should_be_destroyed
            elif final_node_file_system_state == FILE_SYSTEM_STATE.CORRUPT:
                score += config_values.corrupt_should_be_destroyed  
            elif final_node_file_system_state == FILE_SYSTEM_STATE.DESTROYED:
                score += config_values.destroyed  
            else:
                pass
        else:
            pass

    # Scanning State
    if final_node_scanning_state == reference_node_scanning_state:
        # All is well - we're no different from the reference situation
        score += config_values.all_ok
    else: 
        # We're different from the reference situation
        # We're scanning the file system which incurs a penalty (as it slows down systems)
        score += config_values.scanning

    return score