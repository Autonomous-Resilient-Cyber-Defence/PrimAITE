# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Dict

from primaite.simulator.network.hardware.base import (
    IPWirelessNetworkInterface,
    Layer3Interface,
    WirelessNetworkInterface,
)
from primaite.simulator.network.transmission.data_link_layer import Frame


class WirelessAccessPoint(IPWirelessNetworkInterface):
    """
    Represents a Wireless Access Point (AP) in a network.

    This class models a Wireless Access Point, a device that allows wireless devices to connect to a wired network
    using Wi-Fi or other wireless standards. The Wireless Access Point bridges the wireless and wired segments of
    the network, allowing wireless devices to communicate with other devices on the network.

    As an integral component of wireless networking, a Wireless Access Point provides functionalities for network
    management, signal broadcasting, security enforcement, and connection handling. It also possesses Layer 3
    capabilities such as IP addressing and subnetting, allowing for network segmentation and routing.

    Inherits from:
    - WirelessNetworkInterface: Provides basic properties and methods specific to wireless interfaces.
    - Layer3Interface: Provides Layer 3 properties like ip_address and subnet_mask, enabling the device to manage
      network traffic and routing.

    This class can be further specialised or extended to support specific features or standards related to wireless
    networking, such as different Wi-Fi versions, frequency bands, or advanced security protocols.
    """

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        # Get the state from the WirelessNetworkInterface
        state = WirelessNetworkInterface.describe_state(self)

        # Update the state with information from Layer3Interface
        state.update(Layer3Interface.describe_state(self))

        # Update the state with NIC-specific information
        state.update(
            {
                "wake_on_lan": self.wake_on_lan,
            }
        )

        return state

    def enable(self) -> bool:
        """Enable the interface."""
        pass
        return True

    def disable(self) -> bool:
        """Disable the interface."""
        pass
        return True

    def send_frame(self, frame: Frame) -> bool:
        """
        Attempts to send a network frame through the interface.

        :param frame: The network frame to be sent.
        :return: A boolean indicating whether the frame was successfully sent.
        """
        pass

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        pass

    def __str__(self) -> str:
        """
        String representation of the NIC.

        :return: A string combining the port number, MAC address and IP address of the NIC.
        """
        return f"Port {self.port_name if self.port_name else self.port_num}: {self.mac_address}/{self.ip_address}"
