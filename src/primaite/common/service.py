# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The Service class."""

from primaite.common.enums import SoftwareState


class Service(object):
    """Service class."""

    def __init__(self, name: str, port: str, software_state: SoftwareState):
        """
        Init.

        :param name: The service name.
        :param port: The service port.
        :param software_state: The service SoftwareState.
        """
        self.name = name
        self.port = port
        self.software_state = software_state
        self.patching_count = 0

    def reduce_patching_count(self):
        """Reduces the patching count for the service."""
        self.patching_count -= 1
        if self.patching_count <= 0:
            self.patching_count = 0
            self.software_state = SoftwareState.GOOD
