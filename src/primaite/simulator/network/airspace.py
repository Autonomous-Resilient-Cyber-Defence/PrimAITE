from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Final, List, Optional

from prettytable import PrettyTable

from primaite import getLogger
from primaite.simulator.network.hardware.base import Layer3Interface, NetworkInterface, WiredNetworkInterface
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.system.core.packet_capture import PacketCapture

_LOGGER = getLogger(__name__)

__all__ = ["AIR_SPACE", "AirSpaceFrequency", "WirelessNetworkInterface", "IPWirelessNetworkInterface"]


class AirSpace:
    """Represents a wireless airspace, managing wireless network interfaces and handling wireless transmission."""

    def __init__(self):
        self._wireless_interfaces: Dict[str, WirelessNetworkInterface] = {}
        self._wireless_interfaces_by_frequency: Dict[AirSpaceFrequency, List[WirelessNetworkInterface]] = {}

    def show(self, frequency: Optional[AirSpaceFrequency] = None):
        """
        Displays a summary of wireless interfaces in the airspace, optionally filtered by a specific frequency.

        :param frequency: The frequency band to filter devices by. If None, devices for all frequencies are shown.
        """
        table = PrettyTable()
        table.field_names = ["Connected Node", "MAC Address", "IP Address", "Subnet Mask", "Frequency", "Status"]

        # If a specific frequency is provided, filter by it; otherwise, use all frequencies.
        frequencies_to_show = [frequency] if frequency else self._wireless_interfaces_by_frequency.keys()

        for freq in frequencies_to_show:
            interfaces = self._wireless_interfaces_by_frequency.get(freq, [])
            for interface in interfaces:
                status = "Enabled" if interface.enabled else "Disabled"
                table.add_row(
                    [
                        interface._connected_node.hostname,  # noqa
                        interface.mac_address,
                        interface.ip_address if hasattr(interface, "ip_address") else None,
                        interface.subnet_mask if hasattr(interface, "subnet_mask") else None,
                        str(freq),
                        status,
                    ]
                )

        print(table)

    def add_wireless_interface(self, wireless_interface: WirelessNetworkInterface):
        """
        Adds a wireless network interface to the airspace if it's not already present.

        :param wireless_interface: The wireless network interface to be added.
        """
        if wireless_interface.mac_address not in self._wireless_interfaces:
            self._wireless_interfaces[wireless_interface.mac_address] = wireless_interface
            if wireless_interface.frequency not in self._wireless_interfaces_by_frequency:
                self._wireless_interfaces_by_frequency[wireless_interface.frequency] = []
            self._wireless_interfaces_by_frequency[wireless_interface.frequency].append(wireless_interface)

    def remove_wireless_interface(self, wireless_interface: WirelessNetworkInterface):
        """
        Removes a wireless network interface from the airspace if it's present.

        :param wireless_interface: The wireless network interface to be removed.
        """
        if wireless_interface.mac_address in self._wireless_interfaces:
            self._wireless_interfaces.pop(wireless_interface.mac_address)
            self._wireless_interfaces_by_frequency[wireless_interface.frequency].remove(wireless_interface)

    def clear(self):
        """
        Clears all wireless network interfaces and their frequency associations from the airspace.

        After calling this method, the airspace will contain no wireless network interfaces, and transmissions cannot
        occur until new interfaces are added again.
        """
        self._wireless_interfaces.clear()
        self._wireless_interfaces_by_frequency.clear()

    def transmit(self, frame: Frame, sender_network_interface: WirelessNetworkInterface):
        """
        Transmits a frame to all enabled wireless network interfaces on a specific frequency within the airspace.

        This ensures that a wireless interface does not receive its own transmission.

        :param frame: The frame to be transmitted.
        :param sender_network_interface: The wireless network interface sending the frame. This interface will be
            excluded from the list of receivers to prevent it from receiving its own transmission.
        """
        for wireless_interface in self._wireless_interfaces_by_frequency.get(sender_network_interface.frequency, []):
            if wireless_interface != sender_network_interface and wireless_interface.enabled:
                wireless_interface.receive_frame(frame)


AIR_SPACE: Final[AirSpace] = AirSpace()
"""
A singleton instance of the AirSpace class, representing the global wireless airspace.

This instance acts as the central management point for all wireless communications within the simulated network
environment. By default, there is only one airspace in the simulation, making this variable a singleton that
manages the registration, removal, and transmission of wireless frames across all wireless network interfaces configured
in the simulation. It ensures that wireless frames are appropriately transmitted to and received by wireless
interfaces based on their operational status and frequency band.
"""


class AirSpaceFrequency(Enum):
    """Enumeration representing the operating frequencies for wireless communications."""

    WIFI_2_4 = 2.4e9
    """WiFi 2.4 GHz. Known for its extensive range and ability to penetrate solid objects effectively."""
    WIFI_5 = 5e9
    """WiFi 5 GHz. Known for its higher data transmission speeds and reduced interference from other devices."""

    def __str__(self) -> str:
        if self == AirSpaceFrequency.WIFI_2_4:
            return "WiFi 2.4 GHz"
        elif self == AirSpaceFrequency.WIFI_5:
            return "WiFi 5 GHz"
        else:
            return "Unknown Frequency"


class WirelessNetworkInterface(NetworkInterface, ABC):
    """
    Represents a wireless network interface in a network device.

    This abstract base class models wireless network interfaces, encapsulating properties and behaviors specific to
    wireless connectivity. It provides a framework for managing wireless connections, including signal strength,
    security protocols, and other wireless-specific attributes and methods.

    Wireless network interfaces differ from wired ones in their medium of communication, relying on radio frequencies
    for data transmission and reception. This class serves as a base for more specific types of wireless network
    interfaces, such as Wi-Fi adapters or radio network interfaces, ensuring that essential wireless functionality is
    defined and standardised.

    Inherits from:
    - NetworkInterface: Provides basic network interface properties and methods.

    As an abstract base class, it requires subclasses to implement specific methods related to wireless communication
    and may define additional properties and methods specific to wireless technology.
    """

    frequency: AirSpaceFrequency = AirSpaceFrequency.WIFI_2_4

    def enable(self):
        """Attempt to enable the network interface."""
        if self.enabled:
            return

        if not self._connected_node:
            _LOGGER.error(f"Interface {self} cannot be enabled as it is not connected to a Node")
            return

        if self._connected_node.operating_state != NodeOperatingState.ON:
            self._connected_node.sys_log.info(
                f"Interface {self} cannot be enabled as the connected Node is not powered on"
            )
            return

        self.enabled = True
        self._connected_node.sys_log.info(f"Network Interface {self} enabled")
        self.pcap = PacketCapture(hostname=self._connected_node.hostname, interface_num=self.port_num)
        AIR_SPACE.add_wireless_interface(self)

    def disable(self):
        """Disable the network interface."""
        if not self.enabled:
            return
        self.enabled = False
        if self._connected_node:
            self._connected_node.sys_log.info(f"Network Interface {self} disabled")
        else:
            _LOGGER.debug(f"Interface {self} disabled")
        AIR_SPACE.remove_wireless_interface(self)

    def send_frame(self, frame: Frame) -> bool:
        """
        Attempts to send a network frame over the airspace.

        This method sends a frame if the network interface is enabled and connected to a wireless airspace. It captures
        the frame using PCAP (if available) and transmits it through the airspace. Returns True if the frame is
        successfully sent, False otherwise (e.g., if the network interface is disabled).

        :param frame: The network frame to be sent.
        :return: True if the frame is sent successfully, False if the network interface is disabled.
        """
        if self.enabled:
            frame.set_sent_timestamp()
            self.pcap.capture_outbound(frame)
            AIR_SPACE.transmit(frame, self)
            return True
        # Cannot send Frame as the network interface is not enabled
        return False

    @abstractmethod
    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the network interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        pass


class IPWirelessNetworkInterface(WirelessNetworkInterface, Layer3Interface, ABC):
    """
    Represents an IP wireless network interface.

    This interface operates at both the data link layer (Layer 2) and the network layer (Layer 3) of the OSI model,
    specifically tailored for IP-based communication over wireless connections. This abstract class provides a
    template for creating specific wireless network interfaces that support Internet Protocol (IP) functionalities.

    As this class is a combination of its parent classes without additional attributes or methods, please refer to
    the documentation of `WirelessNetworkInterface` and `Layer3Interface` for more details on the supported operations
    and functionalities.

    The class inherits from:
    - `WirelessNetworkInterface`: Providing the functionalities and characteristics of a wireless connection, such as
        managing wireless signal transmission, reception, and associated wireless protocols.
    - `Layer3Interface`: Enabling network layer capabilities, including IP address assignment, routing, and
        potentially, Layer 3 protocols like IPsec.

    As an abstract class, `IPWirelessNetworkInterface` does not implement specific methods but ensures that any derived
    class provides implementations for the functionalities of both `WirelessNetworkInterface` and `Layer3Interface`.
    This setup is ideal for representing network interfaces in devices that require wireless connections and are capable
    of IP routing and addressing, such as wireless routers, access points, and wireless end-host devices like
    smartphones and laptops.

    This class should be extended by concrete classes that define specific behaviors and properties of an IP-capable
    wireless network interface.
    """

    def model_post_init(self, __context: Any) -> None:
        """
        Performs post-initialisation checks to ensure the model's IP configuration is valid.

        This method is invoked after the initialisation of a network model object to validate its network settings,
        particularly to ensure that the assigned IP address is not a network address. This validation is crucial for
        maintaining the integrity of network simulations and avoiding configuration errors that could lead to
        unrealistic or incorrect behavior.

        :param __context: Contextual information or parameters passed to the method, used for further initializing or
            validating the model post-creation.
        :raises ValueError: If the IP address is the same as the network address, indicating an incorrect configuration.
        """
        if self.ip_network.network_address == self.ip_address:
            raise ValueError(f"{self.ip_address}/{self.subnet_mask} must not be a network address")

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        # Get the state from the WiredNetworkInterface
        state = WiredNetworkInterface.describe_state(self)

        # Update the state with information from Layer3Interface
        state.update(Layer3Interface.describe_state(self))

        state["frequency"] = self.frequency

        return state

    def enable(self):
        """
        Enables this wired network interface and attempts to send a "hello" message to the default gateway.

        This method activates the network interface, making it operational for network communications. After enabling,
        it tries to initiate a default gateway "hello" process, typically to establish initial connectivity and resolve
        the default gateway's MAC address. This step is crucial for ensuring the interface can successfully send data
        to and receive data from the network.

        The method safely handles cases where the connected node might not have a default gateway set or the
        `default_gateway_hello` method is not defined, ignoring such errors to proceed without interruption.
        """
        super().enable()
        try:
            self._connected_node.default_gateway_hello()
        except AttributeError:
            pass

    @abstractmethod
    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        pass
