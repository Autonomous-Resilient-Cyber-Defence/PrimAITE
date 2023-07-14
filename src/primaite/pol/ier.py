# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
Information Exchange Requirements for APE.

Used to represent an information flow from source to destination.
"""


class IER(object):
    """Information Exchange Requirement class."""

    def __init__(
        self,
        _id: str,
        _start_step: int,
        _end_step: int,
        _load: int,
        _protocol: str,
        _port: str,
        _source_node_id: str,
        _dest_node_id: str,
        _mission_criticality: int,
        _running: bool = False,
    ) -> None:
        """
        Initialise an Information Exchange Request.

        :param _id: The IER id
        :param _start_step: The step when this IER should start
        :param _end_step: The step when this IER should end
        :param _load: The load this IER should put on a link (bps)
        :param _protocol: The protocol of this IER
        :param _port: The port this IER runs on
        :param _source_node_id: The source node ID
        :param _dest_node_id: The destination node ID
        :param _mission_criticality: Criticality of this IER to the mission (0 none, 5 mission critical)
        :param _running: Indicates whether the IER is currently running
        """
        self.id: str = _id
        self.start_step: int = _start_step
        self.end_step: int = _end_step
        self.source_node_id: str = _source_node_id
        self.dest_node_id: str = _dest_node_id
        self.load: int = _load
        self.protocol: str = _protocol
        self.port: str = _port
        self.mission_criticality: int = _mission_criticality
        self.running: bool = _running

    def get_id(self) -> str:
        """
        Gets IER ID.

        Returns:
             IER ID
        """
        return self.id

    def get_start_step(self) -> int:
        """
        Gets IER start step.

        Returns:
             IER start step
        """
        return self.start_step

    def get_end_step(self) -> int:
        """
        Gets IER end step.

        Returns:
             IER end step
        """
        return self.end_step

    def get_load(self) -> int:
        """
        Gets IER load.

        Returns:
             IER load
        """
        return self.load

    def get_protocol(self) -> str:
        """
        Gets IER protocol.

        Returns:
             IER protocol
        """
        return self.protocol

    def get_port(self) -> str:
        """
        Gets IER port.

        Returns:
             IER port
        """
        return self.port

    def get_source_node_id(self) -> str:
        """
        Gets IER source node ID.

        Returns:
             IER source node ID
        """
        return self.source_node_id

    def get_dest_node_id(self) -> str:
        """
        Gets IER destination node ID.

        Returns:
             IER destination node ID
        """
        return self.dest_node_id

    def get_is_running(self) -> bool:
        """
        Informs whether the IER is currently running.

        Returns:
             True if running
        """
        return self.running

    def set_is_running(self, _value: bool) -> None:
        """
        Sets the running state of the IER.

        Args:
             _value: running status
        """
        self.running = _value

    def get_mission_criticality(self) -> int:
        """
        Gets the IER mission criticality (used in the reward function).

        Returns:
             Mission criticality value (0 lowest to 5 highest)
        """
        return self.mission_criticality
