# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""Defines node behaviour for Green PoL."""


class NodeStateInstructionGreen(object):
    """The Node State Instruction class.#

    :param _id: The node state instruction id
    :param _start_step: The start step of the instruction
    :param _end_step: The end step of the instruction
    :param _node_id: The id of the associated node
    :param _node_pol_type: The pattern of life type
    :param _service_name: The service name
    :param _state: The state (node or service)
    """

    def __init__(
        self,
        _id,
        _start_step,
        _end_step,
        _node_id,
        _node_pol_type,
        _service_name,
        _state,
    ):
        self.id = _id
        self.start_step = _start_step
        self.end_step = _end_step
        self.node_id = _node_id
        self.node_pol_type = _node_pol_type
        self.service_name = _service_name  # Not used when not a service instruction
        self.state = _state

    def get_start_step(self):
        """Gets the start step.

        Returns:
             The start step
        """
        return self.start_step

    def get_end_step(self):
        """Gets the end step.

        Returns:
             The end step
        """
        return self.end_step

    def get_node_id(self):
        """Gets the node ID.

        Returns:
             The node ID
        """
        return self.node_id

    def get_node_pol_type(self):
        """Gets the node pattern of life type (enum).

        Returns:
             The node pattern of life type (enum)
        """
        return self.node_pol_type

    def get_service_name(self):
        """Gets the service name.

        Returns:
             The service name
        """
        return self.service_name

    def get_state(self):
        """Gets the state (node or service).

        Returns:
             The state (node or service)
        """
        return self.state
