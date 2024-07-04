# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Tuple

import numpy as np
from prettytable import MARKDOWN, PrettyTable
from pydantic import BaseModel, computed_field, Field, model_validator

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


class AirSpaceFrequency(Enum):
    """Enumeration representing the operating frequencies for wireless communications."""

    WIFI_2_4 = 2.4e9
    """WiFi 2.4 GHz. Known for its extensive range and ability to penetrate solid objects effectively."""
    WIFI_5 = 5e9
    """WiFi 5 GHz. Known for its higher data transmission speeds and reduced interference from other devices."""

    def __str__(self) -> str:
        hertz_str = format_hertz(hertz=self.value)
        if self == AirSpaceFrequency.WIFI_2_4:
            return f"WiFi {hertz_str}"
        if self == AirSpaceFrequency.WIFI_5:
            return f"WiFi {hertz_str}"
        return "Unknown Frequency"


class ChannelWidth(Enum):
    """
    Enumeration representing the available channel widths in MHz for wireless communications.

    This enum facilitates standardising and validating channel width configurations.

    Attributes:
        WIDTH_20_MHZ (int): Represents a channel width of 20 MHz, commonly used for basic
                            Wi-Fi connectivity with standard range and interference resistance.
        WIDTH_40_MHZ (int): Represents a channel width of 40 MHz, offering higher data
                            throughput at the expense of potentially increased interference.
        WIDTH_80_MHZ (int): Represents a channel width of 80 MHz, typically used in modern
                            Wi-Fi setups for high data rate applications but with higher susceptibility to interference.
        WIDTH_160_MHZ (int): Represents a channel width of 160 MHz, used for ultra-high-speed
                             network applications, providing maximum data throughput with significant
                             requirements on the spectral environment to minimize interference.
    """

    WIDTH_20_MHZ = 20
    """
    Represents a channel width of 20 MHz, commonly used for basic Wi-Fi connectivity with standard range and
    interference resistance
    """

    WIDTH_40_MHZ = 40
    """
    Represents a channel width of 40 MHz, offering higher data throughput at the expense of potentially increased
    interference.
    """

    WIDTH_80_MHZ = 80
    """
    Represents a channel width of 80 MHz, typically used in modern Wi-Fi setups for high data rate applications but
    with higher susceptibility to interference.
    """

    WIDTH_160_MHZ = 160
    """
    Represents a channel width of 160 MHz, used for ultra-high-speed network applications, providing maximum data
    throughput with significant requirements on the spectral environment to minimize interference.
    """

    def __str__(self) -> str:
        """
        Returns a string representation of the channel width.

        :return: String in the format of "<value> MHz" indicating the channel width.
        """
        return f"{self.value} MHz"


AirSpaceKeyType = Tuple[AirSpaceFrequency, ChannelWidth]


class AirspaceEnvironmentType(Enum):
    """Enum representing different types of airspace environments which affect wireless communication signals."""

    RURAL = "rural"
    """
    A rural environment offers clear channel conditions due to low population density and minimal electronic device
    presence.
    """

    OUTDOOR = "outdoor"
    """
    Outdoor environments like parks or fields have minimal electronic interference.
    """

    SUBURBAN = "suburban"
    """
    Suburban environments strike a balance with fewer electronic interferences than urban but more than rural.
    """

    OFFICE = "office"
    """
    Office environments have moderate interference from numerous electronic devices and overlapping networks.
    """

    URBAN = "urban"
    """
    Urban environments are characterized by tall buildings and a high density of electronic devices, leading to
    significant interference.
    """

    INDUSTRIAL = "industrial"
    """
    Industrial areas face high interference from heavy machinery and numerous electronic devices.
    """

    TRANSPORT = "transport"
    """
    Environments such as subways and buses where metal structures and high mobility create complex interference
    patterns.
    """

    DENSE_URBAN = "dense_urban"
    """
    Dense urban areas like city centers have the highest level of signal interference due to the very high density of
    buildings and devices.
    """

    JAMMING_ZONE = "jamming_zone"
    """
    A jamming zone environment where signals are actively interfered with, typically through the use of signal jammers
    or scrambling devices. This represents the environment with the highest level of interference.
    """

    BLOCKED = "blocked"
    """
    A jamming zone environment with total levels of interference. Airspace is completely blocked.
    """

    @property
    def snr_impact(self) -> int:
        """
        Returns the SNR impact associated with the environment.

        :return: SNR impact in dB.
        """
        impacts = {
            AirspaceEnvironmentType.RURAL: 0,
            AirspaceEnvironmentType.OUTDOOR: 1,
            AirspaceEnvironmentType.SUBURBAN: -5,
            AirspaceEnvironmentType.OFFICE: -7,
            AirspaceEnvironmentType.URBAN: -10,
            AirspaceEnvironmentType.INDUSTRIAL: -15,
            AirspaceEnvironmentType.TRANSPORT: -12,
            AirspaceEnvironmentType.DENSE_URBAN: -20,
            AirspaceEnvironmentType.JAMMING_ZONE: -40,
            AirspaceEnvironmentType.BLOCKED: -100,
        }
        return impacts[self]

    def __str__(self) -> str:
        return f"{self.value.title()} Environment (SNR Impact: {self.snr_impact})"


def estimate_snr(
    frequency: AirSpaceFrequency, environment_type: AirspaceEnvironmentType, channel_width: ChannelWidth
) -> float:
    """
    Estimate the Signal-to-Noise Ratio (SNR) based on the communication frequency, environment, and channel width.

    This function considers both the base SNR value dependent on the frequency and the impact of environmental
    factors and channel width on the SNR.

    The SNR is adjusted by reducing it for wider channels, reflecting the increased noise floor from a broader
    frequency range.

    :param frequency: The operating frequency as defined by AirSpaceFrequency enum, influencing the base SNR. Higher
        frequencies like 5 GHz generally start with a higher base SNR due to less noise.
    :param environment_type: The type of environment from AirspaceEnvironmentType enum, which adjusts the SNR based on
        expected environmental noise and interference levels.
    :param channel_width: The channel width from ChannelWidth enum, where wider channels (80 MHz and 160 MHz) decrease
        the SNR slightly due to an increased noise floor.
    :return: Estimated SNR in dB, calculated as the base SNR modified by environmental and channel width impacts.
    """
    base_snr = 40 if frequency == AirSpaceFrequency.WIFI_5 else 30
    snr_impact = environment_type.snr_impact

    # Adjust SNR impact based on channel width
    if channel_width == ChannelWidth.WIDTH_80_MHZ or channel_width == ChannelWidth.WIDTH_160_MHZ:
        snr_impact -= 3  # Assume wider channels have slightly lower SNR due to increased noise floor

    return base_snr + snr_impact


def calculate_total_channel_capacity(
    channel_width: ChannelWidth, frequency: AirSpaceFrequency, environment_type: AirspaceEnvironmentType
) -> float:
    """
    Calculate the total theoretical data rate for the channel using the Shannon-Hartley theorem.

    This function determines the channel's capacity by considering the bandwidth (derived from channel width),
    and the signal-to-noise ratio (SNR) adjusted by frequency and environmental conditions.

    The Shannon-Hartley theorem states that channel capacity C (in bits per second) can be calculated as:
    ``C = B * log2(1 + SNR)`` where B is the bandwidth in Hertz and SNR is the signal-to-noise ratio.

    :param channel_width: The width of the channel as defined by ChannelWidth enum, converted to Hz for calculation.
    :param frequency: The operating frequency as defined by AirSpaceFrequency enum, influencing the base SNR and part
        of the SNR estimation.
    :param environment_type: The type of environment as defined by AirspaceEnvironmentType enum, used in SNR estimation.
    :return: Theoretical total data rate in Mbps for the entire channel.
    """
    bandwidth_hz = channel_width.value * 1_000_000  # Convert MHz to Hz
    snr_db = estimate_snr(frequency, environment_type, channel_width)
    snr_linear = 10 ** (snr_db / 10)

    total_capacity_bps = bandwidth_hz * np.log2(1 + snr_linear)
    total_capacity_mbps = total_capacity_bps / 1_000_000

    return total_capacity_mbps


def calculate_individual_device_rate(
    channel_width: ChannelWidth,
    frequency: AirSpaceFrequency,
    environment_type: AirspaceEnvironmentType,
    device_count: int,
) -> float:
    """
    Calculate the theoretical data rate available to each individual device on the channel.

    This function first calculates the total channel capacity and then divides this capacity by the number
    of active devices to estimate each device's share of the bandwidth. This reflects the practical limitation
    that multiple devices must share the same channel resources.

    :param channel_width: The channel width as defined by ChannelWidth enum, used in total capacity calculation.
    :param frequency: The operating frequency as defined by AirSpaceFrequency enum, used in total capacity calculation.
    :param environment_type: The environment type as defined by AirspaceEnvironmentType enum, impacting SNR and
        capacity.
    :param device_count: The number of devices sharing the channel. If zero, returns zero to avoid division by zero.
    :return: Theoretical data rate in Mbps available per device, based on shared channel capacity.
    """
    total_capacity_mbps = calculate_total_channel_capacity(channel_width, frequency, environment_type)
    if device_count == 0:
        return 0  # Avoid division by zero
    individual_device_rate_mbps = total_capacity_mbps / device_count

    return individual_device_rate_mbps


class AirSpace(BaseModel):
    """
    Represents a wireless airspace, managing wireless network interfaces and handling wireless transmission.

    This class provides functionalities to manage a collection of wireless network interfaces, each associated with
    specific frequencies and channel widths. It includes methods to calculate and manage bandwidth loads, add and
    remove wireless interfaces, and handle data transmission across these interfaces.
    """

    airspace_environment_type_: AirspaceEnvironmentType = AirspaceEnvironmentType.URBAN
    wireless_interfaces: Dict[str, WirelessNetworkInterface] = Field(default_factory=lambda: {})
    wireless_interfaces_by_frequency_channel_width: Dict[AirSpaceKeyType, List[WirelessNetworkInterface]] = Field(
        default_factory=lambda: {}
    )
    bandwidth_load: Dict[AirSpaceKeyType, float] = Field(default_factory=lambda: {})
    frequency_channel_width_max_capacity_mbps: Dict[AirSpaceKeyType, float] = Field(default_factory=lambda: {})

    def model_post_init(self, __context: Any) -> None:
        """
        Initialize the airspace metadata after instantiation.

        This method is called to set up initial configurations like the maximum capacity of each channel width and
        frequency based on the current environment setting.

        :param __context: Contextual data or settings, typically used for further initializations beyond
                          the basic constructor.
        """
        self._set_frequency_channel_width_max_capacity_mbps()

    def _set_frequency_channel_width_max_capacity_mbps(self):
        """
        Private method to compute and set the maximum channel capacity in Mbps for each frequency and channel width.

        Based on the airspace environment type, this method calculates the maximum possible data transmission
        capacity for each combination of frequency and channel width available and stores these values.
        These capacities are critical for managing and limiting bandwidth load during operations.
        """
        print(
            f"Rebuilding the frequency channel width maximum capacity dictionary based on "
            f"airspace environment type {self.airspace_environment_type_}"
        )
        for frequency in AirSpaceFrequency:
            for channel_width in ChannelWidth:
                max_capacity = calculate_total_channel_capacity(
                    frequency=frequency, channel_width=channel_width, environment_type=self.airspace_environment_type
                )
                self.frequency_channel_width_max_capacity_mbps[frequency, channel_width] = max_capacity

    @computed_field
    @property
    def airspace_environment_type(self) -> AirspaceEnvironmentType:
        """
        Gets the current environment type of the airspace.

        :return: The AirspaceEnvironmentType representing the current environment type.
        """
        return self.airspace_environment_type_

    @airspace_environment_type.setter
    def airspace_environment_type(self, value: AirspaceEnvironmentType) -> None:
        """
        Sets a new environment type for the airspace and updates related configurations.

        Changing the environment type triggers a re-calculation of the maximum channel capacities and
        adjustments to the current setup of wireless interfaces to ensure they are aligned with the
        new environment settings.

        :param value: The new environment type as an AirspaceEnvironmentType.
        """
        if value != self.airspace_environment_type_:
            print(f"Setting airspace_environment_type to {value}")
            self.airspace_environment_type_ = value
            self._set_frequency_channel_width_max_capacity_mbps()
            wireless_interface_keys = list(self.wireless_interfaces.keys())
            for wireless_interface_key in wireless_interface_keys:
                wireless_interface = self.wireless_interfaces[wireless_interface_key]
                self.remove_wireless_interface(wireless_interface)
                self.add_wireless_interface(wireless_interface)

    def show_bandwidth_load(self, markdown: bool = False):
        """
        Prints a table of the current bandwidth load for each frequency and channel width combination on the airspace.

        This method prints a tabulated view showing the utilisation of available bandwidth capacities for all configured
        frequency and channel width pairings. The table includes the current capacity usage as a percentage of the
        maximum capacity, alongside the absolute maximum capacity values in Mbps.

        :param markdown: Flag indicating if output should be in markdown format.
        """
        headers = ["Frequency", "Channel  Width", "Current Capacity (%)", "Maximum Capacity (Mbit)"]
        table = PrettyTable(headers)
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = "Airspace Frequency Channel Loads"
        for key, load in self.bandwidth_load.items():
            frequency, channel_width = key
            maximum_capacity = self.frequency_channel_width_max_capacity_mbps[key]
            load_percent = load / maximum_capacity
            if load_percent > 1.0:
                load_percent = 1.0
            table.add_row(
                [format_hertz(frequency.value), str(channel_width), f"{load_percent:.0%}", f"{maximum_capacity:.3f}"]
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
            "Channel Width",
            "Speed (Mbps)",
            "Status",
        ]
        table = PrettyTable(headers)
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"Devices on Air Space - {self.airspace_environment_type}"

        for interface in self.wireless_interfaces.values():
            status = "Enabled" if interface.enabled else "Disabled"
            table.add_row(
                [
                    interface._connected_node.hostname,  # noqa
                    interface.mac_address,
                    interface.ip_address if hasattr(interface, "ip_address") else None,
                    interface.subnet_mask if hasattr(interface, "subnet_mask") else None,
                    format_hertz(interface.frequency.value),
                    str(interface.channel_width),
                    f"{interface.speed:.3f}",
                    status,
                ]
            )
        print(table.get_string(sortby="Frequency"))

    def show(self, markdown: bool = False):
        """
        Prints a summary of the current state of the airspace, including both wireless interfaces and bandwidth loads.

        This method is a convenient wrapper that calls two separate methods to display detailed tables: one for
        wireless interfaces and another for bandwidth load across all frequencies and channel widths managed within the
        airspace. It provides a holistic view of the operational status and performance metrics of the airspace.

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
            if wireless_interface.airspace_key not in self.wireless_interfaces_by_frequency_channel_width:
                self.wireless_interfaces_by_frequency_channel_width[wireless_interface.airspace_key] = []
            self.wireless_interfaces_by_frequency_channel_width[wireless_interface.airspace_key].append(
                wireless_interface
            )
            speed = calculate_total_channel_capacity(
                wireless_interface.channel_width, wireless_interface.frequency, self.airspace_environment_type
            )
            wireless_interface.set_speed(speed)

    def remove_wireless_interface(self, wireless_interface: WirelessNetworkInterface):
        """
        Removes a wireless network interface from the airspace if it's present.

        :param wireless_interface: The wireless network interface to be removed.
        """
        if wireless_interface.mac_address in self.wireless_interfaces:
            self.wireless_interfaces.pop(wireless_interface.mac_address)
            self.wireless_interfaces_by_frequency_channel_width[wireless_interface.airspace_key].remove(
                wireless_interface
            )

    def clear(self):
        """
        Clears all wireless network interfaces and their frequency associations from the airspace.

        After calling this method, the airspace will contain no wireless network interfaces, and transmissions cannot
        occur until new interfaces are added again.
        """
        self.wireless_interfaces.clear()
        self.wireless_interfaces_by_frequency_channel_width.clear()

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
        if sender_network_interface.airspace_key not in self.bandwidth_load:
            self.bandwidth_load[sender_network_interface.airspace_key] = 0.0
        return (
            self.bandwidth_load[sender_network_interface.airspace_key] + frame.size_Mbits
            <= self.frequency_channel_width_max_capacity_mbps[sender_network_interface.airspace_key]
        )

    def transmit(self, frame: Frame, sender_network_interface: WirelessNetworkInterface):
        """
        Transmits a frame to all enabled wireless network interfaces on a specific frequency within the airspace.

        This ensures that a wireless interface does not receive its own transmission.

        :param frame: The frame to be transmitted.
        :param sender_network_interface: The wireless network interface sending the frame. This interface will be
            excluded from the list of receivers to prevent it from receiving its own transmission.
        """
        self.bandwidth_load[sender_network_interface.airspace_key] += frame.size_Mbits
        for wireless_interface in self.wireless_interfaces_by_frequency_channel_width.get(
            sender_network_interface.airspace_key, []
        ):
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
    frequency_: AirSpaceFrequency = AirSpaceFrequency.WIFI_2_4
    channel_width_: ChannelWidth = ChannelWidth.WIDTH_40_MHZ

    @model_validator(mode="after")  # noqa
    def validate_channel_width_for_2_4_ghz(self) -> "WirelessNetworkInterface":
        """
        Validate the wireless interface's channel width settings after model changes.

        This method serves as a model validator to ensure that the channel width settings for the 2.4 GHz frequency
        comply with accepted standards (either 20 MHz or 40 MHz). It's triggered after model instantiation.

        Ensures that the channel width is appropriate for the current frequency setting, particularly checking
        and adjusting the settings for the 2.4 GHz frequency band to not exceed 40 MHz. This is crucial for
        avoiding interference and ensuring optimal performance in densely populated wireless environments.
        """
        self._check_wifi_24_channel_width()
        return self

    def model_post_init(self, __context: Any) -> None:
        """Initialise the model after its creation, setting the speed based on the calculated channel capacity."""
        speed = calculate_total_channel_capacity(
            channel_width=self.channel_width,
            frequency=self.frequency,
            environment_type=self.airspace.airspace_environment_type,
        )
        self.set_speed(speed)

    def _check_wifi_24_channel_width(self) -> None:
        """
        Ensures that the channel width for 2.4 GHz frequency does not exceed 40 MHz.

        This method checks the current frequency and channel width settings and adjusts the channel width
        to 40 MHz if the frequency is set to 2.4 GHz and the channel width exceeds 40 MHz. This is done to
        comply with typical Wi-Fi standards for 2.4 GHz frequencies, which commonly support up to 40 MHz.

        Logs a SysLog warning if the channel width had to be adjusted, logging this change either to the connected
        node's system log or the global logger, depending on whether the interface is connected to a node.
        """
        if self.frequency_ == AirSpaceFrequency.WIFI_2_4 and self.channel_width_.value > 40:
            self.channel_width_ = ChannelWidth.WIDTH_40_MHZ
            msg = (
                f"Channel width must be either 20 Mhz or 40 Mhz when using {AirSpaceFrequency.WIFI_2_4}. "
                f"Overriding value to use {ChannelWidth.WIDTH_40_MHZ}."
            )
            if self._connected_node:
                self._connected_node.sys_log.warning(f"Wireless Interface {self.port_num}: {msg}")
            else:
                _LOGGER.warning(msg)

    @computed_field
    @property
    def frequency(self) -> AirSpaceFrequency:
        """
        Get the current operating frequency of the wireless interface.

        :return: The current frequency as an AirSpaceFrequency enum value.
        """
        return self.frequency_

    @frequency.setter
    def frequency(self, value: AirSpaceFrequency) -> None:
        """
        Set the operating frequency of the wireless interface and update the network configuration.

        This setter updates the frequency of the wireless interface if the new value differs from the current setting.
        It handles the update by first removing the interface from the current airspace management to avoid conflicts,
        setting the new frequency, ensuring the channel width remains compliant, and then re-adding the interface
        to the airspace with the new settings.

        :param value: The new frequency to set, as an AirSpaceFrequency enum value.
        """
        if value != self.frequency_:
            self.airspace.remove_wireless_interface(self)
            self.frequency_ = value
            self._check_wifi_24_channel_width()
            self.airspace.add_wireless_interface(self)

    @computed_field
    @property
    def channel_width(self) -> ChannelWidth:
        """
        Get the current channel width setting of the wireless interface.

        :return: The current channel width as a ChannelWidth enum value.
        """
        return self.channel_width_

    @channel_width.setter
    def channel_width(self, value: ChannelWidth) -> None:
        """
        Set the channel width of the wireless interface and manage configuration compliance.

        Updates the channel width of the wireless interface. If the new channel width is different from the existing
        one, it first removes the interface from the airspace to prevent configuration conflicts, sets the new channel
        width, checks and adjusts it if necessary (especially for 2.4 GHz frequency to comply with typical standards),
        and then re-registers the interface in the airspace with updated settings.

        :param value: The new channel width to set, as a ChannelWidth enum value.
        """
        if value != self.channel_width_:
            self.airspace.remove_wireless_interface(self)
            self.channel_width_ = value
            self._check_wifi_24_channel_width()
            self.airspace.add_wireless_interface(self)

    @property
    def airspace_key(self) -> tuple:
        """
        The airspace bandwidth/channel identifier for the wireless interface based on its frequency and channel width.

        :return: A tuple containing the frequency and channel width, serving as a bandwidth/channel key.
        """
        return self.frequency_, self.channel_width_

    def set_speed(self, speed: float):
        """
        Sets the network interface speed to the specified value and logs this action.

        This method updates the speed attribute of the network interface to the given value, reflecting
        the theoretical maximum data rate that the interface can support based on the current settings.
        It logs the new speed to the system log of the connected node if available.

        :param speed: The speed in Mbps to be set for the network interface.
        """
        self.speed = speed
        if self._connected_node:
            self._connected_node.sys_log.info(
                f"Wireless Interface {self.port_num}: Setting theoretical maximum data rate to {speed:.3f} Mbps."
            )

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
        if self.enabled:
            frame.set_sent_timestamp()
            self.pcap.capture_outbound(frame)
            if self.airspace.can_transmit_frame(frame, self):
                self.airspace.transmit(frame, self)
                return True
            else:
                # Cannot send Frame as the frequency bandwidth is at capacity
                return False
        # Cannot send Frame as the network interface is not enabled
        return False

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

        state["frequency"] = self.frequency.value

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
