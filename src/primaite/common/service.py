# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The Service class."""

from primaite.common.enums import SOFTWARE_STATE


class Service(object):
    """Service class."""

    def __init__(self, _name, _port, _state):
        """
        Init.

        Args:
            _name: The service name
            _port: The service port
            _state: The service state
        """
        self.name = _name
        self.port = _port
        self.state = _state
        self.patching_count = 0

    def set_name(self, _name):
        """
        Sets the service name.

        Args:
            _name: The service name
        """
        self.name = _name

    def get_name(self):
        """
        Gets the service name.

        Returns:
             The service name
        """
        return self.name

    def set_port(self, _port):
        """
        Sets the service port.

        Args:
            _port: The service port
        """
        self.port = _port

    def get_port(self):
        """
        Gets the service port.

        Returns:
             The service port
        """
        return self.port

    def set_state(self, _state):
        """
        Sets the service state.

        Args:
            _state: The service state
        """
        self.state = _state

    def get_state(self):
        """
        Gets the service state.

        Returns:
             The service state
        """
        return self.state

    def reduce_patching_count(self):
        """Reduces the patching count for the service."""
        self.patching_count -= 1
        if self.patching_count <= 0:
            self.patching_count = 0
            self.state = SOFTWARE_STATE.GOOD
