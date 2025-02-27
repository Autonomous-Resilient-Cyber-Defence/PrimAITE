# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Dict

from primaite.simulator.network.hardware.base import (
    IPWirelessNetworkInterface,
    Layer3Interface,
    WirelessNetworkInterface,
)
from primaite.simulator.network.transmission.data_link_layer import Frame


class WirelessNIC(IPWirelessNetworkInterface):
    """
    Represents a Wireless Network Interface Card (Wireless NIC) in a network device.

    This class encapsulates the functionalities and attributes of a wireless NIC, combining the characteristics of a
    wireless network interface with Layer 3 features. It is capable of connecting to wireless networks, managing
    wireless-specific properties such as signal strength and security protocols, and also handling IP-related
    functionalities like IP addressing and subnetting.

    Inherits from:
    - WirelessNetworkInterface: Provides basic properties and methods specific to wireless interfaces.
    - Layer3Interface: Provides Layer 3 properties like ip_address and subnet_mask, enabling the device to participate
      in IP-based networking.

    This class can be extended to include more advanced features or to tailor its behavior for specific types of
    wireless networks or protocols.
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
