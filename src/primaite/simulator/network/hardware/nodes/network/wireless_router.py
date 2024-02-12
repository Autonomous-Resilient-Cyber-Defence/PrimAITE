from typing import Any, Dict, Union

from pydantic import validate_call

from primaite.simulator.network.airspace import AirSpaceFrequency, IPWirelessNetworkInterface
from primaite.simulator.network.hardware.nodes.network.router import Router, RouterInterface
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.utils.validators import IPV4Address


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
        return super().describe_state()

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        if self.enabled:
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self._connected_node.sys_log.info("Frame discarded as TTL limit reached")
                return False
            frame.set_received_timestamp()
            self.pcap.capture_inbound(frame)
            # If this destination or is broadcast
            if frame.ethernet.dst_mac_addr == self.mac_address or frame.ethernet.dst_mac_addr == "ff:ff:ff:ff:ff:ff":
                self._connected_node.receive_frame(frame=frame, from_network_interface=self)
                return True
        return False

    def __str__(self) -> str:
        """
        String representation of the NIC.

        :return: A string combining the port number, MAC address and IP address of the NIC.
        """
        return f"Port {self.port_num}: {self.mac_address}/{self.ip_address} ({self.frequency})"


class WirelessRouter(Router):
    """
    A WirelessRouter class that extends the functionality of a standard Router to include wireless capabilities.

    This class represents a network device that performs routing functions similar to a traditional router but also
    includes the functionality of a wireless access point. This allows the WirelessRouter to not only direct traffic
    between wired networks but also to manage and facilitate wireless network connections.

    A WirelessRouter is instantiated and configured with both wired and wireless interfaces. The wired interfaces are
    managed similarly to those in a standard Router, while the wireless interfaces require additional configuration
    specific to wireless settings, such as setting the frequency band (e.g., 2.4 GHz or 5 GHz for Wi-Fi).

    The WirelessRouter facilitates creating a network environment where devices can be interconnected via both
    Ethernet (wired) and Wi-Fi (wireless), making it an essential component for simulating more complex and realistic
    network topologies within PrimAITE.

    Example:
        >>> wireless_router = WirelessRouter(hostname="wireless_router_1")
        >>> wireless_router.configure_router_interface(
        ...     ip_address="192.168.1.1",
        ...     subnet_mask="255.255.255.0"
        ... )
        >>> wireless_router.configure_wireless_access_point(
        ...     ip_address="10.10.10.1",
        ...     subnet_mask="255.255.255.0"
        ...     frequency=AirSpaceFrequency.WIFI_2_4
        ... )
    """

    network_interfaces: Dict[str, Union[RouterInterface, WirelessAccessPoint]] = {}
    network_interface: Dict[int, Union[RouterInterface, WirelessAccessPoint]] = {}

    def __init__(self, hostname: str, **kwargs):
        super().__init__(hostname=hostname, num_ports=0, **kwargs)

        self.connect_nic(WirelessAccessPoint(ip_address="127.0.0.1", subnet_mask="255.0.0.0", gateway="0.0.0.0"))

        self.connect_nic(RouterInterface(ip_address="127.0.0.1", subnet_mask="255.0.0.0", gateway="0.0.0.0"))

        self.set_original_state()

    @property
    def wireless_access_point(self) -> WirelessAccessPoint:
        """
        Retrieves the wireless access point interface associated with this wireless router.

        This property provides direct access to the WirelessAccessPoint interface of the router, facilitating wireless
        communications. Specifically, it returns the interface configured on port 1, dedicated to establishing and
        managing wireless network connections. This interface is essential for enabling wireless connectivity,
        allowing devices within connect to the network wirelessly.

        :return: The WirelessAccessPoint instance representing the wireless connection interface on port 1 of the
            wireless router.
        """
        return self.network_interface[1]

    @validate_call()
    def configure_wireless_access_point(
        self,
        ip_address: IPV4Address,
        subnet_mask: IPV4Address,
        frequency: AirSpaceFrequency = AirSpaceFrequency.WIFI_2_4,
    ):
        """
        Configures a wireless access point (WAP).

        Sets its IP address, subnet mask, and operating frequency. This method ensures the wireless access point is
        properly set up to manage wireless communication over the specified frequency band.

        The method first disables the WAP to safely apply configuration changes. After configuring the IP settings,
        it sets the WAP to operate on the specified frequency band and then re-enables the WAP for operation.

        :param ip_address: The IP address to be assigned to the wireless access point.
        :param subnet_mask: The subnet mask associated with the IP address
        :param frequency: The operating frequency of the wireless access point, defined by the AirSpaceFrequency
            enum. This determines the frequency band (e.g., 2.4 GHz or 5 GHz) the access point will use for wireless
            communication. Default is AirSpaceFrequency.WIFI_2_4.
        """
        self.wireless_access_point.disable()  # Temporarily disable the WAP for reconfiguration
        network_interface = self.network_interface[1]
        network_interface.ip_address = ip_address
        network_interface.subnet_mask = subnet_mask
        self.sys_log.info(f"Configured WAP {network_interface}")
        self.set_original_state()
        self.wireless_access_point.frequency = frequency  # Set operating frequency
        self.wireless_access_point.enable()  # Re-enable the WAP with new settings

    @property
    def router_interface(self) -> RouterInterface:
        """
        Retrieves the router interface associated with this wireless router.

        This property provides access to the router interface configured for wired connections. It specifically
        returns the interface configured on port 2, which is reserved for wired LAN/WAN connections.

        :return: The RouterInterface instance representing the wired LAN/WAN connection on port 2 of the wireless
            router.
        """
        return self.network_interface[2]

    @validate_call()
    def configure_router_interface(
        self,
        ip_address: IPV4Address,
        subnet_mask: IPV4Address,
    ):
        """
        Configures a router interface.

        Sets its IP address and subnet mask.

        The method first disables the router interface to safely apply configuration changes. After configuring the IP
        settings, it re-enables the router interface for operation.

        :param ip_address: The IP address to be assigned to the router interface.
        :param subnet_mask: The subnet mask associated with the IP address
        """
        self.router_interface.disable()  # Temporarily disable the router interface for reconfiguration
        super().configure_port(port=2, ip_address=ip_address, subnet_mask=subnet_mask)  # Set IP configuration
        self.router_interface.enable()  # Re-enable the router interface with new settings

    def configure_port(self, port: int, ip_address: Union[IPV4Address, str], subnet_mask: Union[IPV4Address, str]):
        """Not Implemented."""
        raise NotImplementedError(
            "Please use the 'configure_wireless_access_point' and 'configure_router_interface' functions."
        )
