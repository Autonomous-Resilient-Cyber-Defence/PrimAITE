# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""Implements reward function."""
from logging import Logger
from typing import Dict, TYPE_CHECKING, Union

from primaite import getLogger
from primaite.common.custom_typing import NodeUnion
from primaite.common.enums import FileSystemState, HardwareState, SoftwareState
from primaite.common.service import Service
from primaite.nodes.active_node import ActiveNode
from primaite.nodes.service_node import ServiceNode

if TYPE_CHECKING:
    from primaite.config.training_config import TrainingConfig
    from primaite.pol.ier import IER

_LOGGER: Logger = getLogger(__name__)


def calculate_reward_function(
    initial_nodes: Dict[str, NodeUnion],
    final_nodes: Dict[str, NodeUnion],
    reference_nodes: Dict[str, NodeUnion],
    green_iers: Dict[str, "IER"],
    green_iers_reference: Dict[str, "IER"],
    red_iers: Dict[str, "IER"],
    step_count: int,
    config_values: "TrainingConfig",
) -> float:
    """
    Compares the states of the initial and final nodes/links to get a reward.

    Args:
        initial_nodes: The nodes before red and blue agents take effect
        final_nodes: The nodes after red and blue agents take effect
        reference_nodes: The nodes if there had been no red or blue effect
        green_iers: The green IERs (should be running)
        red_iers: Should be stopeed (ideally) by the blue agent
        step_count: current step
        config_values: Config values
    """
    reward_value: float = 0.0

    # For each node, compare hardware state, SoftwareState, service states
    for node_key, final_node in final_nodes.items():
        initial_node = initial_nodes[node_key]
        reference_node = reference_nodes[node_key]

        # Hardware State
        reward_value += score_node_operating_state(final_node, initial_node, reference_node, config_values)

        # Software State
        if isinstance(final_node, ActiveNode) or isinstance(final_node, ServiceNode):
            reward_value += score_node_os_state(final_node, initial_node, reference_node, config_values)

        # Service State
        if isinstance(final_node, ServiceNode):
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
    # but only if it's supposed to be running (it's running in reference)
    for ier_key, ier_value in green_iers.items():
        reference_ier = green_iers_reference[ier_key]
        start_step = ier_value.get_start_step()
        stop_step = ier_value.get_end_step()
        if step_count >= start_step and step_count <= stop_step:
            reference_blocked = not reference_ier.get_is_running()
            live_blocked = not ier_value.get_is_running()
            ier_reward = config_values.green_ier_blocked * ier_value.get_mission_criticality()

            if live_blocked and not reference_blocked:
                reward_value += ier_reward
            elif live_blocked and reference_blocked:
                _LOGGER.debug(
                    (
                        f"IER {ier_key} is blocked in the reference and live environments. "
                        f"Penalty of {ier_reward} was NOT applied."
                    )
                )
            elif not live_blocked and reference_blocked:
                _LOGGER.debug(
                    (
                        f"IER {ier_key} is blocked in the reference env but not in the live one. "
                        f"Penalty of {ier_reward} was NOT applied."
                    )
                )
    return reward_value


def score_node_operating_state(
    final_node: NodeUnion, initial_node: NodeUnion, reference_node: NodeUnion, config_values: "TrainingConfig"
) -> float:
    """
    Calculates score relating to the hardware state of a node.

    Args:
        final_node: The node after red and blue agents take effect
        initial_node: The node before red and blue agents take effect
        reference_node: The node if there had been no red or blue effect
        config_values: Config values
    """
    score: float = 0.0
    final_node_operating_state = final_node.hardware_state
    reference_node_operating_state = reference_node.hardware_state

    if final_node_operating_state == reference_node_operating_state:
        # All is well - we're no different from the reference situation
        score += config_values.all_ok
    else:
        # We're different from the reference situation
        # Need to compare reference and final (current) state of node (i.e. at every step)
        if reference_node_operating_state == HardwareState.ON:
            if final_node_operating_state == HardwareState.OFF:
                score += config_values.off_should_be_on
            elif final_node_operating_state == HardwareState.RESETTING:
                score += config_values.resetting_should_be_on
            else:
                pass
        elif reference_node_operating_state == HardwareState.OFF:
            if final_node_operating_state == HardwareState.ON:
                score += config_values.on_should_be_off
            elif final_node_operating_state == HardwareState.RESETTING:
                score += config_values.resetting_should_be_off
            else:
                pass
        elif reference_node_operating_state == HardwareState.RESETTING:
            if final_node_operating_state == HardwareState.ON:
                score += config_values.on_should_be_resetting
            elif final_node_operating_state == HardwareState.OFF:
                score += config_values.off_should_be_resetting
            elif final_node_operating_state == HardwareState.RESETTING:
                score += config_values.resetting
            else:
                pass
        else:
            pass

    return score


def score_node_os_state(
    final_node: Union[ActiveNode, ServiceNode],
    initial_node: Union[ActiveNode, ServiceNode],
    reference_node: Union[ActiveNode, ServiceNode],
    config_values: "TrainingConfig",
) -> float:
    """
    Calculates score relating to the Software State of a node.

    Args:
        final_node: The node after red and blue agents take effect
        initial_node: The node before red and blue agents take effect
        reference_node: The node if there had been no red or blue effect
        config_values: Config values
    """
    score: float = 0.0
    final_node_os_state = final_node.software_state
    reference_node_os_state = reference_node.software_state

    if final_node_os_state == reference_node_os_state:
        # All is well - we're no different from the reference situation
        score += config_values.all_ok
    else:
        # We're different from the reference situation
        # Need to compare reference and final (current) state of node (i.e. at every step)
        if reference_node_os_state == SoftwareState.GOOD:
            if final_node_os_state == SoftwareState.PATCHING:
                score += config_values.patching_should_be_good
            elif final_node_os_state == SoftwareState.COMPROMISED:
                score += config_values.compromised_should_be_good
            else:
                pass
        elif reference_node_os_state == SoftwareState.PATCHING:
            if final_node_os_state == SoftwareState.GOOD:
                score += config_values.good_should_be_patching
            elif final_node_os_state == SoftwareState.COMPROMISED:
                score += config_values.compromised_should_be_patching
            elif final_node_os_state == SoftwareState.PATCHING:
                score += config_values.patching
            else:
                pass
        elif reference_node_os_state == SoftwareState.COMPROMISED:
            if final_node_os_state == SoftwareState.GOOD:
                score += config_values.good_should_be_compromised
            elif final_node_os_state == SoftwareState.PATCHING:
                score += config_values.patching_should_be_compromised
            elif final_node_os_state == SoftwareState.COMPROMISED:
                score += config_values.compromised
            else:
                pass
        else:
            pass

    return score


def score_node_service_state(
    final_node: ServiceNode, initial_node: ServiceNode, reference_node: ServiceNode, config_values: "TrainingConfig"
) -> float:
    """
    Calculates score relating to the service state(s) of a node.

    Args:
        final_node: The node after red and blue agents take effect
        initial_node: The node before red and blue agents take effect
        reference_node: The node if there had been no red or blue effect
        config_values: Config values
    """
    score: float = 0.0
    final_node_services: Dict[str, Service] = final_node.services
    reference_node_services: Dict[str, Service] = reference_node.services

    for service_key, final_service in final_node_services.items():
        reference_service = reference_node_services[service_key]
        final_service = final_node_services[service_key]

        if final_service.software_state == reference_service.software_state:
            # All is well - we're no different from the reference situation
            score += config_values.all_ok
        else:
            # We're different from the reference situation
            # Need to compare reference and final state of node (i.e. at every step)
            if reference_service.software_state == SoftwareState.GOOD:
                if final_service.software_state == SoftwareState.PATCHING:
                    score += config_values.patching_should_be_good
                elif final_service.software_state == SoftwareState.COMPROMISED:
                    score += config_values.compromised_should_be_good
                elif final_service.software_state == SoftwareState.OVERWHELMED:
                    score += config_values.overwhelmed_should_be_good
                else:
                    pass
            elif reference_service.software_state == SoftwareState.PATCHING:
                if final_service.software_state == SoftwareState.GOOD:
                    score += config_values.good_should_be_patching
                elif final_service.software_state == SoftwareState.COMPROMISED:
                    score += config_values.compromised_should_be_patching
                elif final_service.software_state == SoftwareState.OVERWHELMED:
                    score += config_values.overwhelmed_should_be_patching
                elif final_service.software_state == SoftwareState.PATCHING:
                    score += config_values.patching
                else:
                    pass
            elif reference_service.software_state == SoftwareState.COMPROMISED:
                if final_service.software_state == SoftwareState.GOOD:
                    score += config_values.good_should_be_compromised
                elif final_service.software_state == SoftwareState.PATCHING:
                    score += config_values.patching_should_be_compromised
                elif final_service.software_state == SoftwareState.COMPROMISED:
                    score += config_values.compromised
                elif final_service.software_state == SoftwareState.OVERWHELMED:
                    score += config_values.overwhelmed_should_be_compromised
                else:
                    pass
            elif reference_service.software_state == SoftwareState.OVERWHELMED:
                if final_service.software_state == SoftwareState.GOOD:
                    score += config_values.good_should_be_overwhelmed
                elif final_service.software_state == SoftwareState.PATCHING:
                    score += config_values.patching_should_be_overwhelmed
                elif final_service.software_state == SoftwareState.COMPROMISED:
                    score += config_values.compromised_should_be_overwhelmed
                elif final_service.software_state == SoftwareState.OVERWHELMED:
                    score += config_values.overwhelmed
                else:
                    pass
            else:
                pass

    return score


def score_node_file_system(
    final_node: Union[ActiveNode, ServiceNode],
    initial_node: Union[ActiveNode, ServiceNode],
    reference_node: Union[ActiveNode, ServiceNode],
    config_values: "TrainingConfig",
) -> float:
    """
    Calculates score relating to the file system state of a node.

    Args:
        final_node: The node after red and blue agents take effect
        initial_node: The node before red and blue agents take effect
        reference_node: The node if there had been no red or blue effect
    """
    score: float = 0.0
    final_node_file_system_state = final_node.file_system_state_actual
    reference_node_file_system_state = reference_node.file_system_state_actual

    final_node_scanning_state = final_node.file_system_scanning
    reference_node_scanning_state = reference_node.file_system_scanning

    # File System State
    if final_node_file_system_state == reference_node_file_system_state:
        # All is well - we're no different from the reference situation
        score += config_values.all_ok
    else:
        # We're different from the reference situation
        # Need to compare reference and final state of node (i.e. at every step)
        if reference_node_file_system_state == FileSystemState.GOOD:
            if final_node_file_system_state == FileSystemState.REPAIRING:
                score += config_values.repairing_should_be_good
            elif final_node_file_system_state == FileSystemState.RESTORING:
                score += config_values.restoring_should_be_good
            elif final_node_file_system_state == FileSystemState.CORRUPT:
                score += config_values.corrupt_should_be_good
            elif final_node_file_system_state == FileSystemState.DESTROYED:
                score += config_values.destroyed_should_be_good
            else:
                pass
        elif reference_node_file_system_state == FileSystemState.REPAIRING:
            if final_node_file_system_state == FileSystemState.GOOD:
                score += config_values.good_should_be_repairing
            elif final_node_file_system_state == FileSystemState.RESTORING:
                score += config_values.restoring_should_be_repairing
            elif final_node_file_system_state == FileSystemState.CORRUPT:
                score += config_values.corrupt_should_be_repairing
            elif final_node_file_system_state == FileSystemState.DESTROYED:
                score += config_values.destroyed_should_be_repairing
            elif final_node_file_system_state == FileSystemState.REPAIRING:
                score += config_values.repairing
            else:
                pass
        elif reference_node_file_system_state == FileSystemState.RESTORING:
            if final_node_file_system_state == FileSystemState.GOOD:
                score += config_values.good_should_be_restoring
            elif final_node_file_system_state == FileSystemState.REPAIRING:
                score += config_values.repairing_should_be_restoring
            elif final_node_file_system_state == FileSystemState.CORRUPT:
                score += config_values.corrupt_should_be_restoring
            elif final_node_file_system_state == FileSystemState.DESTROYED:
                score += config_values.destroyed_should_be_restoring
            elif final_node_file_system_state == FileSystemState.RESTORING:
                score += config_values.restoring
            else:
                pass
        elif reference_node_file_system_state == FileSystemState.CORRUPT:
            if final_node_file_system_state == FileSystemState.GOOD:
                score += config_values.good_should_be_corrupt
            elif final_node_file_system_state == FileSystemState.REPAIRING:
                score += config_values.repairing_should_be_corrupt
            elif final_node_file_system_state == FileSystemState.RESTORING:
                score += config_values.restoring_should_be_corrupt
            elif final_node_file_system_state == FileSystemState.DESTROYED:
                score += config_values.destroyed_should_be_corrupt
            elif final_node_file_system_state == FileSystemState.CORRUPT:
                score += config_values.corrupt
            else:
                pass
        elif reference_node_file_system_state == FileSystemState.DESTROYED:
            if final_node_file_system_state == FileSystemState.GOOD:
                score += config_values.good_should_be_destroyed
            elif final_node_file_system_state == FileSystemState.REPAIRING:
                score += config_values.repairing_should_be_destroyed
            elif final_node_file_system_state == FileSystemState.RESTORING:
                score += config_values.restoring_should_be_destroyed
            elif final_node_file_system_state == FileSystemState.CORRUPT:
                score += config_values.corrupt_should_be_destroyed
            elif final_node_file_system_state == FileSystemState.DESTROYED:
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
