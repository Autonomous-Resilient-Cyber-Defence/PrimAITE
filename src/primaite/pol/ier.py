# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""Information Exchange Requirements for APE.

Used to represent an information flow from source to destination.
"""


class IER(object):
    """Information Exchange Requirement class.

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

    def __init__(
        self,
        _id,
        _start_step,
        _end_step,
        _load,
        _protocol,
        _port,
        _source_node_id,
        _dest_node_id,
        _mission_criticality,
        _running=False,
    ):
        self.id = _id
        self.start_step = _start_step
        self.end_step = _end_step
        self.source_node_id = _source_node_id
        self.dest_node_id = _dest_node_id
        self.load = _load
        self.protocol = _protocol
        self.port = _port
        self.mission_criticality = _mission_criticality
        self.running = _running

    def get_id(self):
        """Gets IER ID.

        Returns:
             IER ID
        """
        return self.id

    def get_start_step(self):
        """Gets IER start step.

        Returns:
             IER start step
        """
        return self.start_step

    def get_end_step(self):
        """Gets IER end step.

        Returns:
             IER end step
        """
        return self.end_step

    def get_load(self):
        """Gets IER load.

        Returns:
             IER load
        """
        return self.load

    def get_protocol(self):
        """Gets IER protocol.

        Returns:
             IER protocol
        """
        return self.protocol

    def get_port(self):
        """Gets IER port.

        Returns:
             IER port
        """
        return self.port

    def get_source_node_id(self):
        """Gets IER source node ID.

        Returns:
             IER source node ID
        """
        return self.source_node_id

    def get_dest_node_id(self):
        """Gets IER destination node ID.

        Returns:
             IER destination node ID
        """
        return self.dest_node_id

    def get_is_running(self):
        """Informs whether the IER is currently running.

        Returns:
             True if running
        """
        return self.running

    def set_is_running(self, _value):
        """Sets the running state of the IER.

        Args:
             _value: running status
        """
        self.running = _value

    def get_mission_criticality(self):
        """Gets the IER mission criticality (used in the reward function).

        Returns:
             Mission criticality value (0 lowest to 5 highest)
        """
        return self.mission_criticality
