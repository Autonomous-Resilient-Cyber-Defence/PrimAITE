# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""Defines node behaviour for Green PoL."""
from typing import TYPE_CHECKING, Union

from primaite.common.enums import NodePOLType

if TYPE_CHECKING:
    from primaite.common.enums import FileSystemState, HardwareState, NodePOLInitiator, SoftwareState


class NodeStateInstructionRed:
    """The Node State Instruction class."""

    def __init__(
        self,
        _id: str,
        _start_step: int,
        _end_step: int,
        _target_node_id: str,
        _pol_initiator: "NodePOLInitiator",
        _pol_type: NodePOLType,
        pol_protocol: str,
        _pol_state: Union["HardwareState", "SoftwareState", "FileSystemState"],
        _pol_source_node_id: str,
        _pol_source_node_service: str,
        _pol_source_node_service_state: str,
    ) -> None:
        """
        Initialise the Node State Instruction for the red agent.

        :param _id: The node state instruction id
        :param _start_step: The start step of the instruction
        :param _end_step: The end step of the instruction
        :param _target_node_id: The id of the associated node
        :param -pol_initiator: The way the PoL is applied (DIRECT, IER or SERVICE)
        :param _pol_type: The pattern of life type
        :param pol_protocol: The pattern of life protocol/service affected
        :param _pol_state: The state (node or service)
        :param _pol_source_node_id: The source node Id (used for initiator type SERVICE)
        :param _pol_source_node_service: The source node service (used for initiator type SERVICE)
        :param _pol_source_node_service_state: The source node service state (used for initiator type SERVICE)
        """
        self.id: str = _id
        self.start_step: int = _start_step
        self.end_step: int = _end_step
        self.target_node_id: str = _target_node_id
        self.initiator: "NodePOLInitiator" = _pol_initiator
        self.pol_type: NodePOLType = _pol_type
        self.service_name: str = pol_protocol  # Not used when not a service instruction
        self.state: Union["HardwareState", "SoftwareState", "FileSystemState"] = _pol_state
        self.source_node_id: str = _pol_source_node_id
        self.source_node_service: str = _pol_source_node_service
        self.source_node_service_state = _pol_source_node_service_state

    def get_start_step(self) -> int:
        """
        Gets the start step.

        Returns:
             The start step
        """
        return self.start_step

    def get_end_step(self) -> int:
        """
        Gets the end step.

        Returns:
             The end step
        """
        return self.end_step

    def get_target_node_id(self) -> str:
        """
        Gets the node ID.

        Returns:
             The node ID
        """
        return self.target_node_id

    def get_initiator(self) -> "NodePOLInitiator":
        """
        Gets the initiator.

        Returns:
             The initiator
        """
        return self.initiator

    def get_pol_type(self) -> NodePOLType:
        """
        Gets the node pattern of life type (enum).

        Returns:
             The node pattern of life type (enum)
        """
        return self.pol_type

    def get_service_name(self) -> str:
        """
        Gets the service name.

        Returns:
             The service name
        """
        return self.service_name

    def get_state(self) -> Union["HardwareState", "SoftwareState", "FileSystemState"]:
        """
        Gets the state (node or service).

        Returns:
             The state (node or service)
        """
        return self.state

    def get_source_node_id(self) -> str:
        """
        Gets the source node id (used for initiator type SERVICE).

        Returns:
             The source node id
        """
        return self.source_node_id

    def get_source_node_service(self) -> str:
        """
        Gets the source node service (used for initiator type SERVICE).

        Returns:
             The source node service
        """
        return self.source_node_service

    def get_source_node_service_state(self) -> str:
        """
        Gets the source node service state (used for initiator type SERVICE).

        Returns:
             The source node service state
        """
        return self.source_node_service_state
