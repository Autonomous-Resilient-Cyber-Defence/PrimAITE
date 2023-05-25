# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""An Active Node (i.e. not an actuator)."""
from primaite.common.enums import FILE_SYSTEM_STATE, SOFTWARE_STATE
from primaite.nodes.node import Node


class ActiveNode(Node):
    """Active Node class."""

    def __init__(
        self,
        _id,
        _name,
        _type,
        _priority,
        _state,
        _ip_address,
        _os_state,
        _file_system_state,
        _config_values,
    ):
        """
        Init.

        Args:
            _id: The node ID
            _name: The node name
            _type: The node type (enum)
            _priority: The node priority (enum)
            _state: The node state (enum)
            _ip_address: The node IP address
            _os_state: The node Operating System state
            _file_system_state: The node file system state
            _config_values: The config values
        """
        super().__init__(_id, _name, _type, _priority, _state, _config_values)
        self.ip_address = _ip_address
        # Related to O/S
        self.os_state = _os_state
        self.patching_count = 0
        # Related to File System
        self.file_system_state_actual = _file_system_state
        self.file_system_state_observed = _file_system_state
        self.file_system_scanning = False
        self.file_system_scanning_count = 0
        self.file_system_action_count = 0

    def set_ip_address(self, _ip_address):
        """
        Sets IP address.

        Args:
            _ip_address: IP address
        """
        self.ip_address = _ip_address

    def get_ip_address(self):
        """
        Gets IP address.

        Returns:
             IP address
        """
        return self.ip_address

    def set_os_state(self, _os_state):
        """
        Sets operating system state.

        Args:
            _os_state: Operating system state
        """
        self.os_state = _os_state
        if _os_state == SOFTWARE_STATE.PATCHING:
            self.patching_count = self.config_values.os_patching_duration

    def set_os_state_if_not_compromised(self, _os_state):
        """
        Sets operating system state if the node is not compromised.

        Args:
            _os_state: Operating system state
        """
        if self.os_state != SOFTWARE_STATE.COMPROMISED:
            self.os_state = _os_state
            if _os_state == SOFTWARE_STATE.PATCHING:
                self.patching_count = self.config_values.os_patching_duration

    def get_os_state(self):
        """
        Gets operating system state.

        Returns:
             Operating system state
        """
        return self.os_state

    def update_os_patching_status(self):
        """Updates operating system status based on patching cycle."""
        self.patching_count -= 1
        if self.patching_count <= 0:
            self.patching_count = 0
            self.os_state = SOFTWARE_STATE.GOOD

    def set_file_system_state(self, _file_system_state):
        """
        Sets the file system state (actual and observed).

        Args:
            _file_system_state: File system state
        """
        self.file_system_state_actual = _file_system_state

        if _file_system_state == FILE_SYSTEM_STATE.REPAIRING:
            self.file_system_action_count = (
                self.config_values.file_system_repairing_limit
            )
            self.file_system_state_observed = FILE_SYSTEM_STATE.REPAIRING
        elif _file_system_state == FILE_SYSTEM_STATE.RESTORING:
            self.file_system_action_count = (
                self.config_values.file_system_restoring_limit
            )
            self.file_system_state_observed = FILE_SYSTEM_STATE.RESTORING
        elif _file_system_state == FILE_SYSTEM_STATE.GOOD:
            self.file_system_state_observed = FILE_SYSTEM_STATE.GOOD

    def set_file_system_state_if_not_compromised(self, _file_system_state):
        """
        Sets the file system state (actual and observed) if not in a compromised state.

        Use for green PoL to prevent it overturning a compromised state

        Args:
            _file_system_state: File system state
        """
        if (
            self.file_system_state_actual != FILE_SYSTEM_STATE.CORRUPT
            and self.file_system_state_actual != FILE_SYSTEM_STATE.DESTROYED
        ):
            self.file_system_state_actual = _file_system_state

            if _file_system_state == FILE_SYSTEM_STATE.REPAIRING:
                self.file_system_action_count = (
                    self.config_values.file_system_repairing_limit
                )
                self.file_system_state_observed = FILE_SYSTEM_STATE.REPAIRING
            elif _file_system_state == FILE_SYSTEM_STATE.RESTORING:
                self.file_system_action_count = (
                    self.config_values.file_system_restoring_limit
                )
                self.file_system_state_observed = FILE_SYSTEM_STATE.RESTORING
            elif _file_system_state == FILE_SYSTEM_STATE.GOOD:
                self.file_system_state_observed = FILE_SYSTEM_STATE.GOOD

    def get_file_system_state_actual(self):
        """
        Gets file system state (actual).

        Returns:
             File system state (actual)
        """
        return self.file_system_state_actual

    def get_file_system_state_observed(self):
        """
        Gets file system state (observed).

        Returns:
             File system state (observed)
        """
        return self.file_system_state_observed

    def start_file_system_scan(self):
        """Starts a file system scan."""
        self.file_system_scanning = True
        self.file_system_scanning_count = self.config_values.file_system_scanning_limit

    def is_scanning_file_system(self):
        """
        Gets true/false on whether file system is being scanned.

        Returns:
             True if file system is being scanned
        """
        return self.file_system_scanning

    def update_file_system_state(self):
        """Updates file system status based on scanning / restore / repair cycle."""
        # Deprecate both the action count (for restoring or reparing) and the scanning count
        self.file_system_action_count -= 1
        self.file_system_scanning_count -= 1

        # Reparing / Restoring updates
        if self.file_system_action_count <= 0:
            self.file_system_action_count = 0
            if (
                self.file_system_state_actual == FILE_SYSTEM_STATE.REPAIRING
                or self.file_system_state_actual == FILE_SYSTEM_STATE.RESTORING
            ):
                self.file_system_state_actual = FILE_SYSTEM_STATE.GOOD
                self.file_system_state_observed = FILE_SYSTEM_STATE.GOOD

        # Scanning updates
        if self.file_system_scanning == True and self.file_system_scanning_count < 0:
            self.file_system_state_observed = self.file_system_state_actual
            self.file_system_scanning = False
            self.file_system_scanning_count = 0
