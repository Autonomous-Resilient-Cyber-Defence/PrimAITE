# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""A Service Node (i.e. not an actuator)."""
import logging
from typing import Final

from primaite.common.enums import HARDWARE_STATE, SOFTWARE_STATE
from primaite.nodes.active_node import ActiveNode

_LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


class ServiceNode(ActiveNode):
    """ServiceNode class."""

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
            _id: The node id
            _name: The name of the node
            _type: The type of the node
            _priority: The priority of the node
            _state: The state of the node
            _ipAddress: The IP address of the node
            _osState: The operating system state of the node
            _file_system_state: The file system state of the node
        """
        super().__init__(
            _id,
            _name,
            _type,
            _priority,
            _state,
            _ip_address,
            _os_state,
            _file_system_state,
            _config_values,
        )
        self.services = {}

    def add_service(self, _service):
        """
        Adds a service to the node.

        Args:
            _service: The service to add
        """
        self.services[_service.get_name()] = _service

    def get_services(self):
        """
        Gets the dictionary of services on this node.

        Returns:
             Dictionary of services on this node
        """
        return self.services

    def has_service(self, _protocol):
        """
        Indicates whether a service is on a node.

        Returns:
             True if service (protocol) is on the node
        """
        for service_key, service_value in self.services.items():
            if service_key == _protocol:
                return True
            else:
                pass
        return False

    def service_running(self, _protocol):
        """
        Indicates whether a service is in a running state on the node.

        Returns:
             True if service (protocol) is in a running state on the node
        """
        for service_key, service_value in self.services.items():
            if service_key == _protocol:
                if service_value.get_state() != SOFTWARE_STATE.PATCHING:
                    return True
                else:
                    return False
            else:
                pass
        return False

    def service_is_overwhelmed(self, _protocol):
        """
        Indicates whether a service is in an overwhelmed state on the node.

        Returns:
             True if service (protocol) is in an overwhelmed state on the node
        """
        for service_key, service_value in self.services.items():
            if service_key == _protocol:
                if service_value.get_state() == SOFTWARE_STATE.OVERWHELMED:
                    return True
                else:
                    return False
            else:
                pass
        return False

    def set_service_state(self, _protocol, _state):
        """
        Sets the state of a service (protocol) on the node.

        Args:
            _protocol: The service (protocol)
            _state: The state value
        """
        if self.operating_state != HARDWARE_STATE.OFF:
            for service_key, service_value in self.services.items():
                if service_key == _protocol:
                    # Can't set to compromised if you're in a patching state
                    if (
                        _state == SOFTWARE_STATE.COMPROMISED
                        and service_value.get_state() != SOFTWARE_STATE.PATCHING
                    ) or _state != SOFTWARE_STATE.COMPROMISED:
                        service_value.set_state(_state)
                    else:
                        # Do nothing
                        pass
                    if _state == SOFTWARE_STATE.PATCHING:
                        service_value.patching_count = (
                            self.config_values.service_patching_duration
                        )
                    else:
                        # Do nothing
                        pass
        else:
            _LOGGER.info(
                f"The Nodes operating state is OFF so the state of a service "
                f"cannot be changed. "
                f"Node:{self.id}, "
                f"Node Operating State:{self.operating_state}, "
                f"Node Service Protocol:{_protocol}, "
                f"Node Service State: {_state}"
            )

    def set_service_state_if_not_compromised(self, _protocol, _state):
        """
        Sets the state of a service (protocol) on the node if the operating state is not "compromised".

        Args:
            _protocol: The service (protocol)
            _state: The state value
        """
        if self.operating_state != HARDWARE_STATE.OFF:
            for service_key, service_value in self.services.items():
                if service_key == _protocol:
                    if service_value.get_state() != SOFTWARE_STATE.COMPROMISED:
                        service_value.set_state(_state)
                        if _state == SOFTWARE_STATE.PATCHING:
                            service_value.patching_count = (
                                self.config_values.service_patching_duration
                            )
        else:
            _LOGGER.info(
                f"The Nodes operating state is OFF so the state of a service "
                f"cannot be changed. "
                f"Node:{self.id}, "
                f"Node Operating State:{self.operating_state}, "
                f"Node Service Protocol:{_protocol}, "
                f"Node Service State:{_state}"
            )

    def get_service_state(self, _protocol):
        """
        Gets the state of a service.

        Returns:
             The state of the service
        """
        for service_key, service_value in self.services.items():
            if service_key == _protocol:
                return service_value.get_state()

    def update_services_patching_status(self):
        """Updates the patching counter for any service that are patching."""
        for service_key, service_value in self.services.items():
            if service_value.get_state() == SOFTWARE_STATE.PATCHING:
                service_value.reduce_patching_count()
