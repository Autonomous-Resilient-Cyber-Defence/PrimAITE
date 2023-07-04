# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""An Active Node (i.e. not an actuator)."""
import logging
from typing import Final

from primaite.common.enums import FileSystemState, HardwareState, NodeType, Priority, SoftwareState
from primaite.config.training_config import TrainingConfig
from primaite.nodes.node import Node

_LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


class ActiveNode(Node):
    """Active Node class."""

    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: NodeType,
        priority: Priority,
        hardware_state: HardwareState,
        ip_address: str,
        software_state: SoftwareState,
        file_system_state: FileSystemState,
        config_values: TrainingConfig,
    ):
        """Init.

        :param node_id: The node ID
        :param name: The node name
        :param node_type: The node type (enum)
        :param priority: The node priority (enum)
        :param hardware_state: The node Hardware State
        :param ip_address: The node IP address
        :param software_state: The node Software State
        :param file_system_state: The node file system state
        :param config_values: The config values
        """
        super().__init__(node_id, name, node_type, priority, hardware_state, config_values)
        self.ip_address: str = ip_address
        # Related to Software
        self._software_state: SoftwareState = software_state
        self.patching_count: int = 0
        # Related to File System
        self.file_system_state_actual: FileSystemState = file_system_state
        self.file_system_state_observed: FileSystemState = file_system_state
        self.file_system_scanning: bool = False
        self.file_system_scanning_count: int = 0
        self.file_system_action_count: int = 0

    @property
    def software_state(self) -> SoftwareState:
        """Get the software_state.

        :return: The software_state.
        """
        return self._software_state

    @software_state.setter
    def software_state(self, software_state: SoftwareState):
        """Get the software_state.

        :param software_state: Software State.
        """
        if self.hardware_state != HardwareState.OFF:
            self._software_state = software_state
            if software_state == SoftwareState.PATCHING:
                self.patching_count = self.config_values.os_patching_duration
        else:
            _LOGGER.info(
                f"The Nodes hardware state is OFF so OS State cannot be "
                f"changed. "
                f"Node.node_id:{self.node_id}, "
                f"Node.hardware_state:{self.hardware_state}, "
                f"Node.software_state:{self._software_state}"
            )

    def set_software_state_if_not_compromised(self, software_state: SoftwareState):
        """Sets Software State if the node is not compromised.

        Args:
            software_state: Software State
        """
        if self.hardware_state != HardwareState.OFF:
            if self._software_state != SoftwareState.COMPROMISED:
                self._software_state = software_state
                if software_state == SoftwareState.PATCHING:
                    self.patching_count = self.config_values.os_patching_duration
        else:
            _LOGGER.info(
                f"The Nodes hardware state is OFF so OS State cannot be changed."
                f"Node.node_id:{self.node_id}, "
                f"Node.hardware_state:{self.hardware_state}, "
                f"Node.software_state:{self._software_state}"
            )

    def update_os_patching_status(self):
        """Updates operating system status based on patching cycle."""
        self.patching_count -= 1
        if self.patching_count <= 0:
            self.patching_count = 0
            self._software_state = SoftwareState.GOOD

    def set_file_system_state(self, file_system_state: FileSystemState):
        """Sets the file system state (actual and observed).

        Args:
            file_system_state: File system state
        """
        if self.hardware_state != HardwareState.OFF:
            self.file_system_state_actual = file_system_state

            if file_system_state == FileSystemState.REPAIRING:
                self.file_system_action_count = self.config_values.file_system_repairing_limit
                self.file_system_state_observed = FileSystemState.REPAIRING
            elif file_system_state == FileSystemState.RESTORING:
                self.file_system_action_count = self.config_values.file_system_restoring_limit
                self.file_system_state_observed = FileSystemState.RESTORING
            elif file_system_state == FileSystemState.GOOD:
                self.file_system_state_observed = FileSystemState.GOOD
        else:
            _LOGGER.info(
                f"The Nodes hardware state is OFF so File System State "
                f"cannot be changed. "
                f"Node.node_id:{self.node_id}, "
                f"Node.hardware_state:{self.hardware_state}, "
                f"Node.file_system_state.actual:{self.file_system_state_actual}"
            )

    def set_file_system_state_if_not_compromised(self, file_system_state: FileSystemState):
        """Sets the file system state (actual and observed) if not in a compromised state.

        Use for green PoL to prevent it overturning a compromised state

        Args:
            file_system_state: File system state
        """
        if self.hardware_state != HardwareState.OFF:
            if (
                self.file_system_state_actual != FileSystemState.CORRUPT
                and self.file_system_state_actual != FileSystemState.DESTROYED
            ):
                self.file_system_state_actual = file_system_state

                if file_system_state == FileSystemState.REPAIRING:
                    self.file_system_action_count = self.config_values.file_system_repairing_limit
                    self.file_system_state_observed = FileSystemState.REPAIRING
                elif file_system_state == FileSystemState.RESTORING:
                    self.file_system_action_count = self.config_values.file_system_restoring_limit
                    self.file_system_state_observed = FileSystemState.RESTORING
                elif file_system_state == FileSystemState.GOOD:
                    self.file_system_state_observed = FileSystemState.GOOD
        else:
            _LOGGER.info(
                f"The Nodes hardware state is OFF so File System State (if not "
                f"compromised) cannot be changed. "
                f"Node.node_id:{self.node_id}, "
                f"Node.hardware_state:{self.hardware_state}, "
                f"Node.file_system_state.actual:{self.file_system_state_actual}"
            )

    def start_file_system_scan(self):
        """Starts a file system scan."""
        self.file_system_scanning = True
        self.file_system_scanning_count = self.config_values.file_system_scanning_limit

    def update_file_system_state(self):
        """Updates file system status based on scanning/restore/repair cycle."""
        # Deprecate both the action count (for restoring or reparing) and the scanning count
        self.file_system_action_count -= 1
        self.file_system_scanning_count -= 1

        # Reparing / Restoring updates
        if self.file_system_action_count <= 0:
            self.file_system_action_count = 0
            if (
                self.file_system_state_actual == FileSystemState.REPAIRING
                or self.file_system_state_actual == FileSystemState.RESTORING
            ):
                self.file_system_state_actual = FileSystemState.GOOD
                self.file_system_state_observed = FileSystemState.GOOD

        # Scanning updates
        if self.file_system_scanning == True and self.file_system_scanning_count < 0:
            self.file_system_state_observed = self.file_system_state_actual
            self.file_system_scanning = False
            self.file_system_scanning_count = 0

    def update_resetting_status(self):
        """Updates the reset count & makes software and file state to GOOD."""
        super().update_resetting_status()
        if self.resetting_count <= 0:
            self.file_system_state_actual = FileSystemState.GOOD
            self.software_state = SoftwareState.GOOD

    def update_booting_status(self):
        """Updates the booting software and file state to GOOD."""
        super().update_booting_status()
        if self.booting_count <= 0:
            self.file_system_state_actual = FileSystemState.GOOD
            self.software_state = SoftwareState.GOOD
