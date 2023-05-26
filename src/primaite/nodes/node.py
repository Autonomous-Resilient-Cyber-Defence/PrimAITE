# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The base Node class."""
from typing import Final

from primaite.common.config_values_main import ConfigValuesMain
from primaite.common.enums import HardwareState, NodeType, Priority


class Node:
    """Node class."""

    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: NodeType,
        priority: Priority,
        hardware_state: HardwareState,
        config_values: ConfigValuesMain,
    ):
        """
        Init.

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
        self.config_values: ConfigValuesMain = config_values

    def __repr__(self):
        """Returns the name of the node."""
        return self.name

    def turn_on(self):
        """Sets the node state to ON."""
        self.hardware_state = HardwareState.ON

    def turn_off(self):
        """Sets the node state to OFF."""
        self.hardware_state = HardwareState.OFF

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
