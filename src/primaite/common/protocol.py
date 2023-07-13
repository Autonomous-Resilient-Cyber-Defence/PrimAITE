# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The protocol class."""


class Protocol(object):
    """Protocol class."""

    def __init__(self, _name: str) -> None:
        """
        Initialise a protocol.

        :param _name: The name of the protocol
        :type _name: str
        """
        self.name: str = _name
        self.load: int = 0  # bps

    def get_name(self) -> str:
        """
        Gets the protocol name.

        Returns:
             The protocol name
        """
        return self.name

    def get_load(self) -> int:
        """
        Gets the protocol load.

        Returns:
             The protocol load (bps)
        """
        return self.load

    def add_load(self, _load: int) -> None:
        """
        Adds load to the protocol.

        Args:
            _load: The load to add
        """
        self.load += _load

    def clear_load(self) -> None:
        """Clears the load on this protocol."""
        self.load = 0
