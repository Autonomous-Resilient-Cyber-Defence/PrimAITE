# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The base Node class."""
from typing import Final

from primaite.common.enums import HardwareState, NodeType, Priority
from primaite.config.training_config import TrainingConfig


class Node:
    """Node class."""

    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: NodeType,
        priority: Priority,
        hardware_state: HardwareState,
        config_values: TrainingConfig,
    ):
        """
        Initialise a node.

        :param node_id: The node id.
        :param name: The name of the node.
        :param node_type: The type of the node.
        :param priority: The priority of the node.
        :param hardware_state: The state of the node.
        :param config_values: Config values.
        """
        self.node_id: Final[str] = node_id
        self.name: Final[str] = name
        self.node_type: Final[NodeType] = node_type
        self.priority = priority
        self.hardware_state: HardwareState = hardware_state
        self.resetting_count: int = 0
        self.config_values: TrainingConfig = config_values
        self.booting_count: int = 0
        self.shutting_down_count: int = 0

    def __repr__(self):
        """Returns the name of the node."""
        return self.name

    def turn_on(self):
        """Sets the node state to ON."""
        self.hardware_state = HardwareState.BOOTING
        self.booting_count = self.config_values.node_booting_duration

    def turn_off(self):
        """Sets the node state to OFF."""
        self.hardware_state = HardwareState.OFF
        self.shutting_down_count = self.config_values.node_shutdown_duration

    def reset(self):
        """Sets the node state to Resetting and starts the reset count."""
        self.hardware_state = HardwareState.RESETTING
        self.resetting_count = self.config_values.node_reset_duration

    def update_resetting_status(self):
        """Updates the resetting count."""
        self.resetting_count -= 1
        if self.resetting_count <= 0:
            self.resetting_count = 0
            self.hardware_state = HardwareState.ON

    def update_booting_status(self):
        """Updates the booting count."""
        self.booting_count -= 1
        if self.booting_count <= 0:
            self.booting_count = 0
            self.hardware_state = HardwareState.ON

    def update_shutdown_status(self):
        """Updates the shutdown count."""
        self.shutting_down_count -= 1
        if self.shutting_down_count <= 0:
            self.shutting_down_count = 0
            self.hardware_state = HardwareState.OFF
