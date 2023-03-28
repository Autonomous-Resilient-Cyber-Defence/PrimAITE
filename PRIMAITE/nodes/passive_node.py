# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
The Passive Node class (i.e. an actuator)
"""

from nodes.node import Node

class PassiveNode(Node):
    """
    The Passive Node class
    """

    def __init__(self, _id, _name, _type, _priority, _state, _config_values):
        """
        Init

        Args:
            _id: The node id
            _name: The name of the node
            _type: The type of the node
            _priority: The priority of the node
            _state: The state of the node
        """

        # Pass through to Super for now
        super().__init__(_id, _name, _type, _priority, _state, _config_values)

    def get_ip_address(self):
        """
        Gets the node IP address

        Returns:
             The node IP address
        """

        # No concept of IP address for passive nodes for now
        return ""