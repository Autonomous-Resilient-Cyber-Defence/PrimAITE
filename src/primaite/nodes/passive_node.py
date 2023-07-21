# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""The Passive Node class (i.e. an actuator)."""
from primaite.common.enums import HardwareState, NodeType, Priority
from primaite.config.training_config import TrainingConfig
from primaite.nodes.node import Node


class PassiveNode(Node):
    """The Passive Node class."""

    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: NodeType,
        priority: Priority,
        hardware_state: HardwareState,
        config_values: TrainingConfig,
    ) -> None:
        """
        Initialise a passive node.

        :param node_id: The node id.
        :param name: The name of the node.
        :param node_type: The type of the node.
        :param priority: The priority of the node.
        :param hardware_state: The state of the node.
        :param config_values: Config values.
        """
        # Pass through to Super for now
        super().__init__(node_id, name, node_type, priority, hardware_state, config_values)

    @property
    def ip_address(self) -> str:
        """
        Gets the node IP address as an empty string.

        No concept of IP address for passive nodes for now.

        :return: The node IP address.
        """
        return ""
