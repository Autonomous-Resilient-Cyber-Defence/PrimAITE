# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
"""The protocol class."""


class Protocol(object):
    """Protocol class."""

    def __init__(self, _name):
        """
        Initialise a protocol.

        :param _name: The name of the protocol
        :type _name: str
        """
        self.name = _name
        self.load = 0  # bps

    def get_name(self):
        """
        Gets the protocol name.

        Returns:
             The protocol name
        """
        return self.name

    def get_load(self):
        """
        Gets the protocol load.

        Returns:
             The protocol load (bps)
        """
        return self.load

    def add_load(self, _load):
        """
        Adds load to the protocol.

        Args:
            _load: The load to add
        """
        self.load += _load

    def clear_load(self):
        """Clears the load on this protocol."""
        self.load = 0
