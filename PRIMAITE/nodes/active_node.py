# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
An Active Node (i.e. not an actuator)
"""

from nodes.node import Node
from common.enums import *

class ActiveNode(Node):
    """
    Active Node class
    """

    def __init__(self, _id, _name, _type, _priority, _state, _ip_address, _os_state, _config_values):
        """
        Init

        Args:
            _id: The node ID
            _name: The node name
            _type: The node type (enum)
            _priority: The node priority (enum)
            _state: The node state (enum)
            _ip_address: The node IP address
            _os_state: The node Operating System state
        """

        super().__init__(_id, _name, _type, _priority, _state, _config_values)
        self.ip_address = _ip_address
        self.os_state = _os_state
        self.patching_count = 0

    def set_ip_address(self, _ip_address):
        """
        Sets IP address

        Args:
            _ip_address: IP address
        """

        self.ip_address = _ip_address

    def get_ip_address(self):
        """
        Gets IP address

        Returns:
             IP address
        """
        return self.ip_address

    def set_os_state(self, _os_state):
        """
        Sets operating system state

        Args:
            _os_state: Operating system state
        """

        self.os_state = _os_state
        if _os_state == SOFTWARE_STATE.PATCHING:
            self.patching_count = self.config_values.os_patching_duration

    def set_os_state_if_not_compromised(self, _os_state):
        """
        Sets operating system state if the node is not compromised

        Args:
            _os_state: Operating system state
        """

        if self.os_state != SOFTWARE_STATE.COMPROMISED:
            self.os_state = _os_state
            if _os_state == SOFTWARE_STATE.PATCHING:
                self.patching_count = self.config_values.os_patching_duration

    def get_os_state(self):
        """
        Gets operating system state

        Returns:
             Operating system state
        """

        return self.os_state

    def update_os_patching_status(self):
        """
        Updates operating system status based on patching cycle
        """

        self.patching_count -= 1
        if self.patching_count <= 0:
            self.patching_count = 0
            self.os_state = SOFTWARE_STATE.GOOD
