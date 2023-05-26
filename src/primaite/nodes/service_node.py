# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""A Service Node (i.e. not an actuator)."""
import logging
from typing import Dict, Final

from primaite.common.config_values_main import ConfigValuesMain
from primaite.common.enums import (
    FileSystemState,
    HardwareState,
    NodeType,
    Priority,
    SoftwareState,
)
from primaite.common.service import Service
from primaite.nodes.active_node import ActiveNode

_LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


class ServiceNode(ActiveNode):
    """ServiceNode class."""

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
        config_values: ConfigValuesMain,
    ):
        """
        Init.

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
        super().__init__(
            node_id,
            name,
            node_type,
            priority,
            hardware_state,
            ip_address,
            software_state,
            file_system_state,
            config_values,
        )
        self.services: Dict[str, Service] = {}

    def add_service(self, service: Service):
        """
        Adds a service to the node.

        :param service: The service to add
        """
        self.services[service.name] = service

    def has_service(self, protocol_name: str) -> bool:
        """
        Indicates whether a service is on a node.

        :param protocol_name: The service (protocol)e.
        :return: True if service (protocol) is on the node, otherwise False.
        """
        for service_key, service_value in self.services.items():
            if service_key == protocol_name:
                return True
        return False

    def service_running(self, protocol_name: str) -> bool:
        """
        Indicates whether a service is in a running state on the node.

        :param protocol_name: The service (protocol)
        :return: True if service (protocol) is in a running state on the
            node, otherwise False.
        """
        for service_key, service_value in self.services.items():
            if service_key == protocol_name:
                if service_value.software_state != SoftwareState.PATCHING:
                    return True
                else:
                    return False
        return False

    def service_is_overwhelmed(self, protocol_name: str) -> bool:
        """
        Indicates whether a service is in an overwhelmed state on the node.

        :param protocol_name: The service (protocol)
        :return: True if service (protocol) is in an overwhelmed state on the
            node, otherwise False.
        """
        for service_key, service_value in self.services.items():
            if service_key == protocol_name:
                if service_value.software_state == SoftwareState.OVERWHELMED:
                    return True
                else:
                    return False
        return False

    def set_service_state(self, protocol_name: str, software_state: SoftwareState):
        """
        Sets the software_state of a service (protocol) on the node.

        :param protocol_name: The service (protocol).
        :param software_state: The software_state.
        """
        if self.hardware_state != HardwareState.OFF:
            service_key = protocol_name
            service_value = self.services.get(service_key)
            if service_value:
                # Can't set to compromised if you're in a patching state
                if (
                    software_state == SoftwareState.COMPROMISED
                    and service_value.software_state != SoftwareState.PATCHING
                ) or software_state != SoftwareState.COMPROMISED:
                    service_value.software_state = software_state
                if software_state == SoftwareState.PATCHING:
                    service_value.patching_count = (
                        self.config_values.service_patching_duration
                    )
        else:
            _LOGGER.info(
                f"The Nodes hardware state is OFF so the state of a service "
                f"cannot be changed. "
                f"Node.node_id:{self.node_id}, "
                f"Node.hardware_state:{self.hardware_state}, "
                f"Node.services[<key>]:{protocol_name}, "
                f"Node.services[<key>].software_state:{software_state}"
            )

    def set_service_state_if_not_compromised(
        self, protocol_name: str, software_state: SoftwareState
    ):
        """
        Sets the software_state of a service (protocol) on the node.

        Done if the software_state is not "compromised".

        :param protocol_name: The service (protocol).
        :param software_state: The software_state.
        """
        if self.hardware_state != HardwareState.OFF:
            service_key = protocol_name
            service_value = self.services.get(service_key)
            if service_value:
                if service_value.software_state != SoftwareState.COMPROMISED:
                    service_value.software_state = software_state
                    if software_state == SoftwareState.PATCHING:
                        service_value.patching_count = (
                            self.config_values.service_patching_duration
                        )
        else:
            _LOGGER.info(
                f"The Nodes hardware state is OFF so the state of a service "
                f"cannot be changed. "
                f"Node.node_id:{self.node_id}, "
                f"Node.hardware_state:{self.hardware_state}, "
                f"Node.services[<key>]:{protocol_name}, "
                f"Node.services[<key>].software_state:{software_state}"
            )

    def get_service_state(self, protocol_name):
        """
        Gets the state of a service.

        :return: The software_state of the service.
        """
        service_key = protocol_name
        service_value = self.services.get(service_key)
        if service_value:
            return service_value.software_state

    def update_services_patching_status(self):
        """Updates the patching counter for any service that are patching."""
        for service_key, service_value in self.services.items():
            if service_value.software_state == SoftwareState.PATCHING:
                service_value.reduce_patching_count()
