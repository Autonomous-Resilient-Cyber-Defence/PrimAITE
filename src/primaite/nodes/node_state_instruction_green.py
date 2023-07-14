# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""Defines node behaviour for Green PoL."""
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from primaite.common.enums import FileSystemState, HardwareState, NodePOLType, SoftwareState


class NodeStateInstructionGreen(object):
    """The Node State Instruction class."""

    def __init__(
        self,
        _id: str,
        _start_step: int,
        _end_step: int,
        _node_id: str,
        _node_pol_type: "NodePOLType",
        _service_name: str,
        _state: Union["HardwareState", "SoftwareState", "FileSystemState"],
    ):
        """
        Initialise the Node State Instruction.

        :param _id: The node state instruction id
        :param _start_step: The start step of the instruction
        :param _end_step: The end step of the instruction
        :param _node_id: The id of the associated node
        :param _node_pol_type: The pattern of life type
        :param _service_name: The service name
        :param _state: The state (node or service)
        """
        self.id = _id
        self.start_step = _start_step
        self.end_step = _end_step
        self.node_id = _node_id
        self.node_pol_type: "NodePOLType" = _node_pol_type
        self.service_name: str = _service_name  # Not used when not a service instruction
        # TODO: confirm type of state
        self.state: Union["HardwareState", "SoftwareState", "FileSystemState"] = _state

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

    def get_node_id(self) -> str:
        """
        Gets the node ID.

        Returns:
             The node ID
        """
        return self.node_id

    def get_node_pol_type(self) -> "NodePOLType":
        """
        Gets the node pattern of life type (enum).

        Returns:
             The node pattern of life type (enum)
        """
        return self.node_pol_type

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
