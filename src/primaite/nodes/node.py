# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
The base Node class
"""

from primaite.common.enums import *

class Node:
    """
    Node class
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

        self.id = _id
        self.name = _name
        self.type = _type
        self.priority = _priority
        self.operating_state = _state
        self.resetting_count = 0    
        self.config_values = _config_values

    def __repr__(self):
        """
        Returns the name of the node
        """

        return self.name

    def set_id(self, _id):
        """
        Sets the node ID

        Args:
            _id: The node ID
        """

        self.id = _id

    def get_id(self):
        """
        Gets the node ID

        Returns:
             The node ID
        """

        return self.id

    def set_name(self, _name):
        """
        Sets the node name

        Args:
            _name: The node name
        """

        self.name = _name

    def get_name(self):
        """
        Gets the node name

        Returns:
             The node name
        """

        return self.name

    def set_type(self, _type):
        """
        Sets the node type

        Args:
            _type: The node type
        """

        self.type = _type

    def get_type(self):
        """
        Gets the node type

        Returns:
             The node type
        """

        return self.type

    def set_priority(self, _priority):
        """
        Sets the node priority

        Args:
            _priority: The node priority
        """

        self.priority = _priority

    def get_priority(self):
        """
        Gets the node priority

        Returns:
             The node priority
        """

        return self.priority

    def set_state(self, _state):
        """
        Sets the node state

        Args:
            _state: The node state
        """

        self.operating_state = _state

    def get_state(self):
        """
        Gets the node operating state

        Returns:
             The node operating state
        """

        return self.operating_state

    def turn_on(self):
        """
        Sets the node state to ON
        """

        self.operating_state = HARDWARE_STATE.ON

    def turn_off(self):
        """
        Sets the node state to OFF
        """

        self.operating_state = HARDWARE_STATE.OFF

    def reset(self):
        """
        Sets the node state to Resetting and starts the reset count
        """

        self.operating_state = HARDWARE_STATE.RESETTING
        self.resetting_count = self.config_values.node_reset_duration

    def update_resetting_status(self):
        """
        Updates the resetting count
        """

        self.resetting_count -= 1
        if self.resetting_count <= 0:
            self.resetting_count = 0
            self.operating_state = HARDWARE_STATE.ON






