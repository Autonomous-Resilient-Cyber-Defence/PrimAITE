# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from prettytable import MARKDOWN, PrettyTable
from pydantic import BaseModel, Field, validate_call

from primaite import getLogger
from primaite.simulator.network.hardware.base import Layer3Interface, NetworkInterface, WiredNetworkInterface
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.system.core.packet_capture import PacketCapture

_LOGGER = getLogger(__name__)


def format_hertz(hertz: float, format_terahertz: bool = False, decimals: int = 3) -> str:
    """
    Convert a frequency in Hertz to a formatted string using the most appropriate unit.

    Optionally includes formatting for Terahertz.

    :param hertz: Frequency in Hertz.
    :param format_terahertz: Whether to format frequency in Terahertz, default is False.
    :param decimals: Number of decimal places to round to, default is 3.
    :returns: Formatted string with the frequency in the most suitable unit.
    """
    format_str = f"{{:.{decimals}f}}"
    if format_terahertz and hertz >= 1e12:  # Terahertz
        return format_str.format(hertz / 1e12) + " THz"
    elif hertz >= 1e9:  # Gigahertz
        return format_str.format(hertz / 1e9) + " GHz"
    elif hertz >= 1e6:  # Megahertz
        return format_str.format(hertz / 1e6) + " MHz"
    elif hertz >= 1e3:  # Kilohertz
        return format_str.format(hertz / 1e3) + " kHz"
    else:  # Hertz
        return format_str.format(hertz) + " Hz"


_default_frequency_set: Dict[str, Dict] = {
    "WIFI_2_4": {"frequency": 2.4e9, "data_rate_bps": 100_000_000.0},
    "WIFI_5": {"frequency": 5e9, "data_rate_bps": 500_000_000.0},
}
"""Frequency configuration that is automatically used for any new airspace."""


def register_default_frequency(freq_name: str, freq_hz: float, data_rate_bps: float) -> None:
    """Add to the default frequency configuration. This is intended as a plugin hook.

    If your plugin makes use of bespoke frequencies for wireless communication, you should make a call to this method
    wherever you define components that rely on the bespoke frequencies. That way, as soon as your components are
    imported, this function automatically updates the default frequency set.

    This should also be run before instances of AirSpace are created.

    :param freq_name: The frequency name. If this clashes with an existing frequency name, it will be overwritten.
    :type freq_name: str
    :param freq_hz: The frequency itself, measured in Hertz.
    :type freq_hz: float
    :param data_rate_bps: The transmission capacity over this frequency, in bits per second.
    :type data_rate_bps: float
    """
    _default_frequency_set.update({freq_name: {"frequency": freq_hz, "data_rate_bps": data_rate_bps}})


class AirSpace(BaseModel):
    """
    Represents a wireless airspace, managing wireless network interfaces and handling wireless transmission.

    This class provides functionalities to manage a collection of wireless network interfaces, each associated with
    specific frequencies. It includes methods to add and remove wireless interfaces, and handle data transmission
    across these interfaces.
    """

    wireless_interfaces: Dict[str, WirelessNetworkInterface] = Field(default_factory=lambda: {})
    wireless_interfaces_by_frequency: Dict[int, List[WirelessNetworkInterface]] = Field(default_factory=lambda: {})
    bandwidth_load: Dict[int, float] = Field(default_factory=lambda: {})
    frequencies: Dict[str, Dict] = Field(default_factory=lambda: copy.deepcopy(_default_frequency_set))

    @validate_call
    def get_frequency_max_capacity_mbps(self, freq_name: str) -> float:
        """
        Retrieves the maximum data transmission capacity for a specified frequency.

        :param freq_name: The frequency for which the maximum capacity is queried.
        :return: The maximum capacity in Mbps for the specified frequency.
        """
        if freq_name in self.frequencies:
            return self.frequencies[freq_name]["data_rate_bps"] / (1024.0 * 1024.0)
        return 0.0

    def set_frequency_max_capacity_mbps(self, cfg: Dict[int, float]) -> None:
        """
        Sets custom maximum data transmission capacities for multiple frequencies.

        :param cfg: A dictionary mapping frequencies to their new maximum capacities in Mbps.
        """
        for freq, mbps in cfg.items():
            self.frequencies[freq]["data_rate_bps"] = mbps * 1024 * 1024
            print(f"Overriding {freq} max capacity as {mbps:.3f} mbps")

    def register_frequency(self, freq_name: str, freq_hz: float, data_rate_bps: float) -> None:
        """
        Define a new frequency for this airspace.

        :param freq_name: The frequency name. If this clashes with an existing frequency name, it will be overwritten.
        :type freq_name: str
        :param freq_hz: The frequency itself, measured in Hertz.
        :type freq_hz: float
        :param data_rate_bps: The transmission capacity over this frequency, in bits per second.
        :type data_rate_bps: float
        """
        if freq_name in self.frequencies:
            _LOGGER.info(
                f"Overwriting Air space frequency {freq_name}. "
                f"Previous data rate: {self.frequencies[freq_name]['data_rate_bps']}. "
                f"Current data rate: {data_rate_bps}."
            )
        self.frequencies.update({freq_name: {"frequency": freq_hz, "data_rate_bps": data_rate_bps}})

    def show_bandwidth_load(self, markdown: bool = False):
        """
        Prints a table of the current bandwidth load for each frequency on the airspace.

        This method prints a tabulated view showing the utilisation of available bandwidth capacities for all
        frequencies. The table includes the current capacity usage as a percentage of the maximum capacity, alongside
        the absolute maximum capacity values in Mbps.

        :param markdown: Flag indicating if output should be in markdown format.
        """
        headers = ["Frequency", "Current Capacity (%)", "Maximum Capacity (Mbit)"]
        table = PrettyTable(headers)
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = "Airspace Frequency Channel Loads"
        for frequency, load in self.bandwidth_load.items():
            maximum_capacity = self.get_frequency_max_capacity_mbps(frequency)
            load_percent = load / maximum_capacity if maximum_capacity > 0 else 0.0
            if load_percent > 1.0:
                load_percent = 1.0
            table.add_row(
                [
                    format_hertz(self.frequencies[frequency]["frequency"]),
                    f"{load_percent:.0%}",
                    f"{maximum_capacity:.3f}",
                ]
            )
        print(table)

    def show_wireless_interfaces(self, markdown: bool = False):
        """
        Prints a table of wireless interfaces in the airspace.

        :param markdown: Flag indicating if output should be in markdown format.
        """
        headers = [
            "Connected Node",
            "MAC Address",
            "IP Address",
            "Subnet Mask",
            "Frequency",
            "Speed (Mbps)",
            "Status",
        ]
        table = PrettyTable(headers)
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = "Devices on Air Space"

        for interface in self.wireless_interfaces.values():
            status = "Enabled" if interface.enabled else "Disabled"
            table.add_row(
                [
                    interface._connected_node.hostname,  # noqa
                    interface.mac_address,
                    interface.ip_address if hasattr(interface, "ip_address") else None,
                    interface.subnet_mask if hasattr(interface, "subnet_mask") else None,
                    format_hertz(self.frequencies[interface.frequency]["frequency"]),
                    f"{interface.speed:.3f}",
                    status,
                ]
            )
        print(table.get_string(sortby="Frequency"))

    def show(self, markdown: bool = False):
        """
        Prints a summary of the current state of the airspace, including both wireless interfaces and bandwidth loads.

        This method is a convenient wrapper that calls two separate methods to display detailed tables: one for
        wireless interfaces and another for bandwidth load across all frequencies managed within the airspace. It
        provides a holistic view of the operational status and performance metrics of the airspace.

        :param markdown: Flag indicating if output should be in markdown format.
        """
        self.show_wireless_interfaces(markdown)
        self.show_bandwidth_load(markdown)

    def add_wireless_interface(self, wireless_interface: WirelessNetworkInterface):
        """
        Adds a wireless network interface to the airspace if it's not already present.

        :param wireless_interface: The wireless network interface to be added.
        """
        if wireless_interface.mac_address not in self.wireless_interfaces:
            self.wireless_interfaces[wireless_interface.mac_address] = wireless_interface
            if wireless_interface.frequency not in self.wireless_interfaces_by_frequency:
                self.wireless_interfaces_by_frequency[wireless_interface.frequency] = []
            self.wireless_interfaces_by_frequency[wireless_interface.frequency].append(wireless_interface)

    def remove_wireless_interface(self, wireless_interface: WirelessNetworkInterface):
        """
        Removes a wireless network interface from the airspace if it's present.

        :param wireless_interface: The wireless network interface to be removed.
        """
        if wireless_interface.mac_address in self.wireless_interfaces:
            self.wireless_interfaces.pop(wireless_interface.mac_address)
            self.wireless_interfaces_by_frequency[wireless_interface.frequency].remove(wireless_interface)

    def clear(self):
        """
        Clears all wireless network interfaces and their frequency associations from the airspace.

        After calling this method, the airspace will contain no wireless network interfaces, and transmissions cannot
        occur until new interfaces are added again.
        """
        self.wireless_interfaces.clear()
        self.wireless_interfaces_by_frequency.clear()

    def reset_bandwidth_load(self):
        """
        Resets the bandwidth load tracking for all frequencies in the airspace.

        This method clears the current load metrics for all operating frequencies, effectively setting the load to zero.
        """
        self.bandwidth_load = {}

    def can_transmit_frame(self, frame: Frame, sender_network_interface: WirelessNetworkInterface) -> bool:
        """
        Determines if a frame can be transmitted by the sender network interface based on the current bandwidth load.

        This method checks if adding the size of the frame to the current bandwidth load of the frequency used by the
        sender network interface would exceed the maximum allowed bandwidth for that frequency. It returns True if the
        frame can be transmitted without exceeding the limit, and False otherwise.

        :param frame: The frame to be transmitted, used to check its size against the frequency's bandwidth limit.
        :param sender_network_interface: The network interface attempting to transmit the frame, used to determine the
             relevant frequency and its current bandwidth load.
        :return: True if the frame can be transmitted within the bandwidth limit, False if it would exceed the limit.
        """
        if sender_network_interface.frequency not in self.bandwidth_load:
            self.bandwidth_load[sender_network_interface.frequency] = 0.0
        return self.bandwidth_load[
            sender_network_interface.frequency
        ] + frame.size_Mbits <= self.get_frequency_max_capacity_mbps(sender_network_interface.frequency)

    def transmit(self, frame: Frame, sender_network_interface: WirelessNetworkInterface):
        """
        Transmits a frame to all enabled wireless network interfaces on a specific frequency within the airspace.

        This ensures that a wireless interface does not receive its own transmission.

        :param frame: The frame to be transmitted.
        :param sender_network_interface: The wireless network interface sending the frame. This interface will be
            excluded from the list of receivers to prevent it from receiving its own transmission.
        """
        self.bandwidth_load[sender_network_interface.frequency] += frame.size_Mbits
        for wireless_interface in self.wireless_interfaces_by_frequency.get(sender_network_interface.frequency, []):
            if wireless_interface != sender_network_interface and wireless_interface.enabled:
                wireless_interface.receive_frame(frame)


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

    airspace: AirSpace
    frequency: str = "WIFI_2_4"

    def enable(self):
        """Attempt to enable the network interface."""
        if self.enabled:
            return

        if not self._connected_node:
            _LOGGER.warning(f"Interface {self} cannot be enabled as it is not connected to a Node")
            return

        if self._connected_node.operating_state != NodeOperatingState.ON:
            self._connected_node.sys_log.error(
                f"Interface {self} cannot be enabled as the connected Node is not powered on"
            )
            return

        self.enabled = True
        self._connected_node.sys_log.info(f"Network Interface {self} enabled")
        self.pcap = PacketCapture(
            hostname=self._connected_node.hostname, port_num=self.port_num, port_name=self.port_name
        )
        self.airspace.add_wireless_interface(self)

    def disable(self):
        """Disable the network interface."""
        if not self.enabled:
            return
        self.enabled = False
        if self._connected_node:
            self._connected_node.sys_log.info(f"Network Interface {self} disabled")
        else:
            _LOGGER.debug(f"Interface {self} disabled")
        self.airspace.remove_wireless_interface(self)

    def send_frame(self, frame: Frame) -> bool:
        """
        Attempts to send a network frame over the airspace.

        This method sends a frame if the network interface is enabled and connected to a wireless airspace. It captures
        the frame using PCAP (if available) and transmits it through the airspace. Returns True if the frame is
        successfully sent, False otherwise (e.g., if the network interface is disabled).

        :param frame: The network frame to be sent.
        :return: True if the frame is sent successfully, False if the network interface is disabled.
        """
        if not self.enabled:
            return False
        if not self.airspace.can_transmit_frame(frame, self):
            # Drop frame for now. Queuing will happen here (probably) if it's done in the future.
            self._connected_node.sys_log.info(f"{self}: Frame dropped as Link is at capacity")
            return False

        super().send_frame(frame)
        frame.set_sent_timestamp()
        self.pcap.capture_outbound(frame)
        self.airspace.transmit(frame, self)
        return True

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the network interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        if self.enabled:
            frame.set_sent_timestamp()
            self.pcap.capture_inbound(frame)
            self._connected_node.receive_frame(frame, self)
            return True
        # Cannot receive Frame as the network interface is not enabled
        return False


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
