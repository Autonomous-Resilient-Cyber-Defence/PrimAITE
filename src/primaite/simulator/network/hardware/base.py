from __future__ import annotations

import re
import secrets
from abc import ABC, abstractmethod
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from typing import Any, Dict, Optional, Union

from prettytable import MARKDOWN, PrettyTable
from pydantic import BaseModel, Field

from primaite import getLogger
from primaite.exceptions import NetworkError
from primaite.simulator import SIM_OUTPUT
from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.domain.account import Account
from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.packet_capture import PacketCapture
from primaite.simulator.system.core.session_manager import SessionManager
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.processes.process import Process
from primaite.simulator.system.services.service import Service
from primaite.utils.validators import IPV4Address

_LOGGER = getLogger(__name__)


def generate_mac_address(oui: Optional[str] = None) -> str:
    """
    Generate a random MAC Address.

    :param oui: The Organizationally Unique Identifier (OUI) portion of the MAC address. It should be a string with
        the first 3 bytes (24 bits) in the format "XX:XX:XX".
    :raises ValueError: If the 'oui' is not in the correct format (hexadecimal and 6 characters).
    """
    random_bytes = [secrets.randbits(8) for _ in range(6)]

    if oui:
        oui_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){2}[0-9A-Fa-f]{2}$")
        if not oui_pattern.match(oui):
            msg = f"Invalid oui. The oui should be in the format xx:xx:xx, where x is a hexadecimal digit, got '{oui}'"
            _LOGGER.error(msg)
            raise ValueError(msg)
        oui_bytes = [int(chunk, 16) for chunk in oui.split(":")]
        mac = oui_bytes + random_bytes[len(oui_bytes) :]
    else:
        mac = random_bytes

    return ":".join(f"{b:02x}" for b in mac)


class NetworkInterface(SimComponent, ABC):
    """
    A generic Network Interface in a Node on a Network.

    This is a base class for specific types of network interfaces, providing common attributes and methods required
    for network communication. It defines the fundamental properties that all network interfaces share, such as
    MAC address, speed, MTU (maximum transmission unit), and the ability to enable or disable the interface.

    :ivar str mac_address: The MAC address of the network interface. Default to a randomly generated MAC address.
    :ivar int speed: The speed of the interface in Mbps. Default is 100 Mbps.
    :ivar int mtu: The Maximum Transmission Unit (MTU) of the interface in Bytes. Default is 1500 B.
    """

    mac_address: str = Field(default_factory=generate_mac_address)
    "The MAC address of the interface."

    speed: int = 100
    "The speed of the interface in Mbps. Default is 100 Mbps."

    mtu: int = 1500
    "The Maximum Transmission Unit (MTU) of the interface in Bytes. Default is 1500 B"

    enabled: bool = False
    "Indicates whether the interface is enabled."

    _connected_node: Optional[Node] = None
    "The Node to which the interface is connected."

    port_num: Optional[int] = None
    "The port number assigned to this interface on the connected node."

    pcap: Optional[PacketCapture] = None
    "A PacketCapture instance for capturing and analysing packets passing through this interface."

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()

        rm.add_request("enable", RequestType(func=lambda request, context: self.enable()))
        rm.add_request("disable", RequestType(func=lambda request, context: self.disable()))

        return rm

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = super().describe_state()
        state.update(
            {
                "mac_address": self.mac_address,
                "speed": self.speed,
                "mtu": self.mtu,
                "enabled": self.enabled,
            }
        )
        return state

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        super().reset_component_for_episode(episode)
        if episode and self.pcap:
            self.pcap.current_episode = episode
            self.pcap.setup_logger()
        self.enable()

    @abstractmethod
    def enable(self):
        """Enable the interface."""
        pass

    @abstractmethod
    def disable(self):
        """Disable the interface."""
        pass

    @abstractmethod
    def send_frame(self, frame: Frame) -> bool:
        """
        Attempts to send a network frame through the interface.

        :param frame: The network frame to be sent.
        :return: A boolean indicating whether the frame was successfully sent.
        """
        pass

    @abstractmethod
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

        :return: A string combining the port number and the mac address
        """
        return f"Port {self.port_num}: {self.mac_address}"


class WiredNetworkInterface(NetworkInterface, ABC):
    """
    Represents a wired network interface in a network device.

    This abstract base class serves as a foundational blueprint for wired network interfaces, offering core
    functionalities and enforcing the implementation of key operational methods such as enabling and disabling the
    interface. It encapsulates common attributes and behaviors intrinsic to wired interfaces, including the
    management of physical or logical connections to network links and the provision of methods for connecting to and
    disconnecting from these links.

    Inherits from:
    - NetworkInterface: Provides basic network interface properties and methods.


    Subclasses of this class are expected to provide concrete implementations for the abstract methods defined here,
    tailoring the functionality to the specific requirements of the wired interface types they represent.
    """

    _connected_link: Optional[Link] = None
    "The network link to which the network interface is connected."

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

        if not self._connected_link:
            self._connected_node.sys_log.info(f"Interface {self} cannot be enabled as there is no Link connected.")
            return

        self.enabled = True
        self._connected_node.sys_log.info(f"Network Interface {self} enabled")
        self.pcap = PacketCapture(hostname=self._connected_node.hostname, interface_num=self.port_num)
        if self._connected_link:
            self._connected_link.endpoint_up()

    def disable(self):
        """Disable the network interface."""
        if not self.enabled:
            return
        self.enabled = False
        if self._connected_node:
            self._connected_node.sys_log.info(f"Network Interface {self} disabled")
        else:
            _LOGGER.debug(f"Interface {self} disabled")
        if self._connected_link:
            self._connected_link.endpoint_down()

    def connect_link(self, link: Link):
        """
        Connect this network interface to a specified link.

        This method establishes a connection between the network interface and a network link if the network interface
        is not already connected. If the network interface is already connected to a link, it logs an error and does
        not change the existing connection.

        :param link: The Link instance to connect to this network interface.
        """
        if self._connected_link:
            _LOGGER.error(f"Cannot connect Link to network interface {self} as it already has a connection")
            return

        if self._connected_link == link:
            _LOGGER.error(f"Cannot connect Link to network interface {self} as it is already connected")
            return

        self._connected_link = link
        self.enable()

    def disconnect_link(self):
        """
        Disconnect the network interface from its connected Link, if any.

        This method removes the association between the network interface and its connected Link. It updates the
        connected Link's endpoints to reflect the disconnection.
        """
        if self._connected_link.endpoint_a == self:
            self._connected_link.endpoint_a = None
        if self._connected_link.endpoint_b == self:
            self._connected_link.endpoint_b = None
        self._connected_link = None

    def send_frame(self, frame: Frame) -> bool:
        """
        Attempt to send a network frame through the connected Link.

        This method sends a frame if the NIC is enabled and connected to a link. It captures the frame using PCAP
        (if available) and transmits it through the connected link. Returns True if the frame is successfully sent,
        False otherwise (e.g., if the Network Interface is disabled).

        :param frame: The network frame to be sent.
        :return: True if the frame is sent, False if the Network Interface is disabled or not connected to a link.
        """
        if self.enabled:
            frame.set_sent_timestamp()
            self.pcap.capture_outbound(frame)
            self._connected_link.transmit_frame(sender_nic=self, frame=frame)
            return True
        # Cannot send Frame as the NIC is not enabled
        return False

    @abstractmethod
    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the network interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        pass


class Layer3Interface(BaseModel, ABC):
    """
    Represents a Layer 3 (Network Layer) interface in a network device.

    This class serves as a base for network interfaces that operate at Layer 3 of the OSI model, providing IP
    connectivity and subnetting capabilities. It's not meant to be instantiated directly but to be subclassed by
    specific types of network interfaces that require IP addressing capabilities.

    :ivar IPV4Address ip_address: The IP address assigned to the interface. This address enables the interface to
        participate in IP-based networking, allowing it to send and receive IP packets.
    :ivar IPv4Address subnet_mask: The subnet mask assigned to the interface. This mask helps in determining the
        network segment that the interface belongs to and is used in IP routing decisions.
    """

    ip_address: IPV4Address
    "The IP address assigned to the interface for communication on an IP-based network."

    subnet_mask: IPV4Address
    "The subnet mask assigned to the interface, defining the network portion and the host portion of the IP address."

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        state = {
            "ip_address": str(self.ip_address),
            "subnet_mask": str(self.subnet_mask),
        }

        return state

    @property
    def ip_network(self) -> IPv4Network:
        """
        Calculate and return the IPv4Network derived from the NIC's IP address and subnet mask.

        This property constructs an IPv4Network object which represents the whole network that the NIC's IP address
        belongs to, based on its subnet mask. It's useful for determining the network range and broadcast address.

        :return: An IPv4Network instance representing the network of this NIC.
        """
        return IPv4Network(f"{self.ip_address}/{self.subnet_mask}", strict=False)


class IPWiredNetworkInterface(WiredNetworkInterface, Layer3Interface, ABC):
    """
    Represents an IP wired network interface.

    This interface operates at both the data link layer (Layer 2) and the network layer (Layer 3) of the OSI model,
    specifically tailored for IP-based communication. This abstract class serves as a template for creating specific
    wired network interfaces that support Internet Protocol (IP) functionalities.

    As this class is an amalgamation of its parent classes without additional attributes or methods, it is recommended
    to refer to the documentation of `WiredNetworkInterface` and `Layer3Interface` for detailed information on the
    supported operations and functionalities.

    The class inherits from:
    - `WiredNetworkInterface`: Provides the functionalities and characteristics of a wired connection, such as
        physical link establishment and data transmission over a cable.
    - `Layer3Interface`: Enables network layer capabilities, including IP address assignment, routing, and
        potentially, Layer 3 protocols like IPsec.

    As an abstract class, `IPWiredNetworkInterface` does not implement specific methods but mandates that any derived
    class provides implementations for the functionalities of both `WiredNetworkInterface` and `Layer3Interface`.
    This structure is ideal for representing network interfaces in devices that require wired connections and are
    capable of IP routing and addressing, such as routers, switches, as well as end-host devices like computers and
    servers.

    Derived classes should define specific behaviors and properties of an IP-capable wired network interface,
    customizing it for their specific use cases.
    """

    _connected_link: Optional[Link] = None
    "The network link to which the network interface is connected."

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
            pass
            self._connected_node.default_gateway_hello()
        except AttributeError:
            pass

    # @abstractmethod
    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the network interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        pass


class WirelessNetworkInterface(NetworkInterface, ABC):
    """
    Represents a wireless network interface in a network device.

    This abstract base class models wireless network interfaces, encapsulating properties and behaviors specific to
    wireless connectivity. It provides a framework for managing wireless connections, including signal strength,
    security protocols, and other wireless-specific attributes and methods.

    Wireless network interfaces differ from wired ones in their medium of communication, relying on radio frequencies
    for data transmission and reception. This class serves as a base for more specific types of wireless interfaces,
    such as Wi-Fi adapters or radio network interfaces, ensuring that essential wireless functionality is defined
    and standardised.

    Inherits from:
    - NetworkInterface: Provides basic network interface properties and methods.

    As an abstract base class, it requires subclasses to implement specific methods related to wireless communication
    and may define additional properties and methods specific to wireless technology.
    """


class IPWirelessNetworkInterface(WiredNetworkInterface, Layer3Interface, ABC):
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

    @abstractmethod
    def enable(self):
        """Enable the interface."""
        pass

    @abstractmethod
    def disable(self):
        """Disable the interface."""
        pass

    @abstractmethod
    def send_frame(self, frame: Frame) -> bool:
        """
        Attempts to send a network frame through the interface.

        :param frame: The network frame to be sent.
        :return: A boolean indicating whether the frame was successfully sent.
        """
        pass

    @abstractmethod
    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        pass


class Link(SimComponent):
    """
    Represents a network link between NIC<-->NIC, NIC<-->SwitchPort, or SwitchPort<-->SwitchPort.

    :param endpoint_a: The first NIC or SwitchPort connected to the Link.
    :param endpoint_b: The second NIC or SwitchPort connected to the Link.
    :param bandwidth: The bandwidth of the Link in Mbps (default is 100 Mbps).
    """

    endpoint_a: Union[WiredNetworkInterface]
    "The first WiredNetworkInterface connected to the Link."
    endpoint_b: Union[WiredNetworkInterface]
    "The second WiredNetworkInterface connected to the Link."
    bandwidth: float = 100.0
    "The bandwidth of the Link in Mbps (default is 100 Mbps)."
    current_load: float = 0.0
    "The current load on the link in Mbps."

    def __init__(self, **kwargs):
        """
        Ensure that endpoint_a and endpoint_b are not the same NIC.

        Connect the link to the NICs after creation.

        :raises ValueError: If endpoint_a and endpoint_b are the same NIC.
        """
        if kwargs["endpoint_a"] == kwargs["endpoint_b"]:
            msg = "endpoint_a and endpoint_b cannot be the same NIC or SwitchPort"
            _LOGGER.error(msg)
            raise ValueError(msg)
        super().__init__(**kwargs)
        self.endpoint_a.connect_link(self)
        self.endpoint_b.connect_link(self)
        self.endpoint_up()

        self.set_original_state()

    def set_original_state(self):
        """Sets the original state."""
        vals_to_include = {"bandwidth", "current_load"}
        self._original_state = self.model_dump(include=vals_to_include)
        super().set_original_state()

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "endpoint_a": self.endpoint_a.uuid,  # TODO: consider if using UUID is the best way to do this
                "endpoint_b": self.endpoint_b.uuid,  # TODO: consider if using UUID is the best way to do this
                "bandwidth": self.bandwidth,
                "current_load": self.current_load,
            }
        )
        return state

    @property
    def current_load_percent(self) -> str:
        """Get the current load formatted as a percentage string."""
        return f"{self.current_load / self.bandwidth:.5f}%"

    def endpoint_up(self):
        """Let the Link know and endpoint has been brought up."""
        if self.is_up:
            _LOGGER.debug(f"Link {self} up")

    def endpoint_down(self):
        """Let the Link know and endpoint has been brought down."""
        if not self.is_up:
            self.current_load = 0.0
            _LOGGER.debug(f"Link {self} down")

    @property
    def is_up(self) -> bool:
        """
        Informs whether the link is up.

        This is based upon both NIC endpoints being enabled.
        """
        return self.endpoint_a.enabled and self.endpoint_b.enabled

    def _can_transmit(self, frame: Frame) -> bool:
        if self.is_up:
            frame_size_Mbits = frame.size_Mbits  # noqa - Leaving it as Mbits as this is how they're expressed
            # return self.current_load + frame_size_Mbits <= self.bandwidth
            # TODO: re add this check once packet size limiting and MTU checks are implemented
            return True
        return False

    def transmit_frame(self, sender_nic: Union[WiredNetworkInterface], frame: Frame) -> bool:
        """
        Send a network frame from one NIC or SwitchPort to another connected NIC or SwitchPort.

        :param sender_nic: The NIC or SwitchPort sending the frame.
        :param frame: The network frame to be sent.
        :return: True if the Frame can be sent, otherwise False.
        """
        can_transmit = self._can_transmit(frame)
        if not can_transmit:
            _LOGGER.debug(f"Cannot transmit frame as {self} is at capacity")
            return False

        receiver = self.endpoint_a
        if receiver == sender_nic:
            receiver = self.endpoint_b
        frame_size = frame.size_Mbits

        if receiver.receive_frame(frame):
            # Frame transmitted successfully
            # Load the frame size on the link
            self.current_load += frame_size
            _LOGGER.debug(
                f"Added {frame_size:.3f} Mbits to {self}, current load {self.current_load:.3f} Mbits "
                f"({self.current_load_percent})"
            )
            return True
        return False

    def __str__(self) -> str:
        return f"{self.endpoint_a}<-->{self.endpoint_b}"


class Node(SimComponent):
    """
    A basic Node class that represents a node on the network.

    This class manages the state of the node, including the NICs (Network Interface Cards), accounts, applications,
    services, processes, file system, and various managers like ARP, ICMP, SessionManager, and SoftwareManager.

    :param hostname: The node hostname on the network.
    :param operating_state: The node operating state, either ON or OFF.
    """

    hostname: str
    "The node hostname on the network."
    default_gateway: Optional[IPV4Address] = None
    "The default gateway IP address for forwarding network traffic to other networks."
    operating_state: NodeOperatingState = NodeOperatingState.OFF
    "The hardware state of the node."
    network_interfaces: Dict[str, NetworkInterface] = {}
    "The Network Interfaces on the node."
    network_interface: Dict[int, NetworkInterface] = {}
    "The Network Interfaces on the node by port id."
    dns_server: Optional[IPv4Address] = None
    "List of IP addresses of DNS servers used for name resolution."

    accounts: Dict[str, Account] = {}
    "All accounts on the node."
    applications: Dict[str, Application] = {}
    "All applications on the node."
    services: Dict[str, Service] = {}
    "All services on the node."
    processes: Dict[str, Process] = {}
    "All processes on the node."
    file_system: FileSystem
    "The nodes file system."
    root: Path
    "Root directory for simulation output."
    sys_log: SysLog
    session_manager: SessionManager
    software_manager: SoftwareManager

    revealed_to_red: bool = False
    "Informs whether the node has been revealed to a red agent."

    start_up_duration: int = 3
    "Time steps needed for the node to start up."

    start_up_countdown: int = 0
    "Time steps needed until node is booted up."

    shut_down_duration: int = 3
    "Time steps needed for the node to shut down."

    shut_down_countdown: int = 0
    "Time steps needed until node is shut down."

    is_resetting: bool = False
    "If true, the node will try turning itself off then back on again."

    node_scan_duration: int = 10
    "How many timesteps until the whole node is scanned. Default 10 time steps."

    node_scan_countdown: int = 0
    "Time steps until scan is complete"

    red_scan_countdown: int = 0
    "Time steps until reveal to red scan is complete."

    def __init__(self, **kwargs):
        """
        Initialize the Node with various components and managers.

        This method initializes the ARP cache, ICMP handler, session manager, and software manager if they are not
        provided.
        """
        if not kwargs.get("sys_log"):
            kwargs["sys_log"] = SysLog(kwargs["hostname"])
        if not kwargs.get("session_manager"):
            kwargs["session_manager"] = SessionManager(sys_log=kwargs.get("sys_log"))
        if not kwargs.get("root"):
            kwargs["root"] = SIM_OUTPUT.path / kwargs["hostname"]
        if not kwargs.get("file_system"):
            kwargs["file_system"] = FileSystem(sys_log=kwargs["sys_log"], sim_root=kwargs["root"] / "fs")
        if not kwargs.get("software_manager"):
            kwargs["software_manager"] = SoftwareManager(
                parent_node=self,
                sys_log=kwargs.get("sys_log"),
                session_manager=kwargs.get("session_manager"),
                file_system=kwargs.get("file_system"),
                dns_server=kwargs.get("dns_server"),
            )
        super().__init__(**kwargs)
        self.session_manager.node = self
        self.session_manager.software_manager = self.software_manager
        self._install_system_software()
        self.set_original_state()

    # def model_post_init(self, __context: Any) -> None:
    #     self._install_system_software()
    #     self.set_original_state()

    def set_original_state(self):
        """Sets the original state."""
        for software in self.software_manager.software.values():
            software.set_original_state()

        self.file_system.set_original_state()

        for network_interface in self.network_interfaces.values():
            network_interface.set_original_state()

        vals_to_include = {
            "hostname",
            "default_gateway",
            "operating_state",
            "revealed_to_red",
            "start_up_duration",
            "start_up_countdown",
            "shut_down_duration",
            "shut_down_countdown",
            "is_resetting",
            "node_scan_duration",
            "node_scan_countdown",
            "red_scan_countdown",
        }
        self._original_state = self.model_dump(include=vals_to_include)

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        super().reset_component_for_episode(episode)

        # Reset Session Manager
        self.session_manager.clear()

        # Reset File System
        self.file_system.reset_component_for_episode(episode)

        # Reset all Nics
        for network_interface in self.network_interfaces.values():
            network_interface.reset_component_for_episode(episode)

        for software in self.software_manager.software.values():
            software.reset_component_for_episode(episode)

        if episode and self.sys_log:
            self.sys_log.current_episode = episode
            self.sys_log.setup_logger()

    def _init_request_manager(self) -> RequestManager:
        # TODO: I see that this code is really confusing and hard to read right now... I think some of these things will
        # need a better name and better documentation.
        rm = super()._init_request_manager()
        # since there are potentially many services, create an request manager that can map service name
        self._service_request_manager = RequestManager()
        rm.add_request("service", RequestType(func=self._service_request_manager))
        self._nic_request_manager = RequestManager()
        rm.add_request("network_interface", RequestType(func=self._nic_request_manager))

        rm.add_request("file_system", RequestType(func=self.file_system._request_manager))

        # currently we don't have any applications nor processes, so these will be empty
        self._process_request_manager = RequestManager()
        rm.add_request("process", RequestType(func=self._process_request_manager))
        self._application_request_manager = RequestManager()
        rm.add_request("application", RequestType(func=self._application_request_manager))

        rm.add_request("scan", RequestType(func=lambda request, context: self.reveal_to_red()))

        rm.add_request("shutdown", RequestType(func=lambda request, context: self.power_off()))
        rm.add_request("startup", RequestType(func=lambda request, context: self.power_on()))
        rm.add_request("reset", RequestType(func=lambda request, context: self.reset()))  # TODO implement node reset
        rm.add_request("logon", RequestType(func=lambda request, context: ...))  # TODO implement logon request
        rm.add_request("logoff", RequestType(func=lambda request, context: ...))  # TODO implement logoff request

        self._os_request_manager = RequestManager()
        self._os_request_manager.add_request("scan", RequestType(func=lambda request, context: self.scan()))
        rm.add_request("os", RequestType(func=self._os_request_manager))

        return rm

    def _install_system_software(self):
        """Install System Software - software that is usually provided with the OS."""
        pass

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "hostname": self.hostname,
                "operating_state": self.operating_state.value,
                "NICs": {
                    eth_num: network_interface.describe_state()
                    for eth_num, network_interface in self.network_interface.items()
                },
                "file_system": self.file_system.describe_state(),
                "applications": {app.name: app.describe_state() for app in self.applications.values()},
                "services": {svc.name: svc.describe_state() for svc in self.services.values()},
                "process": {proc.name: proc.describe_state() for proc in self.processes.values()},
                "revealed_to_red": self.revealed_to_red,
            }
        )
        return state

    def show(self, markdown: bool = False):
        """Show function that calls both show NIC and show open ports."""
        self.show_nic(markdown)
        self.show_open_ports(markdown)

    def show_open_ports(self, markdown: bool = False):
        """Prints a table of the open ports on the Node."""
        table = PrettyTable(["Port", "Name"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.hostname} Open Ports"
        for port in self.software_manager.get_open_ports():
            table.add_row([port.value, port.name])
        print(table)

    @property
    def has_enabled_network_interface(self) -> bool:
        """
        Checks if the node has at least one enabled network interface.

        Iterates through all network interfaces associated with the node to determine if at least one is enabled. This
        property is essential for determining the node's ability to communicate within the network.

        :return: True if there is at least one enabled network interface; otherwise, False.
        """
        for network_interface in self.network_interfaces.values():
            if network_interface.enabled:
                return True
        return False

    def show_nic(self, markdown: bool = False):
        """Prints a table of the NICs on the Node."""
        table = PrettyTable(["Port", "Type", "MAC Address", "Address", "Speed", "Status"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.hostname} Network Interface Cards"
        for port, network_interface in self.network_interface.items():
            table.add_row(
                [
                    port,
                    type(network_interface),
                    network_interface.mac_address,
                    f"{network_interface.ip_address}/{network_interface.ip_network.prefixlen}",
                    network_interface.speed,
                    "Enabled" if network_interface.enabled else "Disabled",
                ]
            )
        print(table)

    def apply_timestep(self, timestep: int):
        """
        Apply a single timestep of simulation dynamics to this node.

        In this instance, if any multi-timestep processes are currently occurring
        (such as starting up or shutting down), then they are brought one step closer to
        being finished.

        :param timestep: The current timestep number. (Amount of time since simulation episode began)
        :type timestep: int
        """
        super().apply_timestep(timestep=timestep)

        # count down to boot up
        if self.start_up_countdown > 0:
            self.start_up_countdown -= 1
        else:
            if self.operating_state == NodeOperatingState.BOOTING:
                self.operating_state = NodeOperatingState.ON
                self.sys_log.info(f"{self.hostname}: Turned on")
                for network_interface in self.network_interfaces.values():
                    network_interface.enable()

                self._start_up_actions()

        # count down to shut down
        if self.shut_down_countdown > 0:
            self.shut_down_countdown -= 1
        else:
            if self.operating_state == NodeOperatingState.SHUTTING_DOWN:
                self.operating_state = NodeOperatingState.OFF
                self.sys_log.info(f"{self.hostname}: Turned off")
                self._shut_down_actions()

                # if resetting turn back on
                if self.is_resetting:
                    self.is_resetting = False
                    self.power_on()

        # time steps which require the node to be on
        if self.operating_state == NodeOperatingState.ON:
            # node scanning
            if self.node_scan_countdown > 0:
                self.node_scan_countdown -= 1

                if self.node_scan_countdown == 0:
                    # scan everything!
                    for process_id in self.processes:
                        self.processes[process_id].scan()

                    # scan services
                    for service_id in self.services:
                        self.services[service_id].scan()

                    # scan applications
                    for application_id in self.applications:
                        self.applications[application_id].scan()

                    # scan file system
                    self.file_system.scan(instant_scan=True)

            if self.red_scan_countdown > 0:
                self.red_scan_countdown -= 1

                if self.red_scan_countdown == 0:
                    # scan processes
                    for process_id in self.processes:
                        self.processes[process_id].reveal_to_red()

                    # scan services
                    for service_id in self.services:
                        self.services[service_id].reveal_to_red()

                    # scan applications
                    for application_id in self.applications:
                        self.applications[application_id].reveal_to_red()

                    # scan file system
                    self.file_system.reveal_to_red(instant_scan=True)

            for process_id in self.processes:
                self.processes[process_id].apply_timestep(timestep=timestep)

            for service_id in self.services:
                self.services[service_id].apply_timestep(timestep=timestep)

            for application_id in self.applications:
                self.applications[application_id].apply_timestep(timestep=timestep)

            self.file_system.apply_timestep(timestep=timestep)

    def scan(self) -> None:
        """
        Scan the node and all the items within it.

        Scans the:
            - Processes
            - Services
            - Applications
            - Folders
            - Files

        to the red agent.
        """
        self.node_scan_countdown = self.node_scan_duration

    def reveal_to_red(self) -> None:
        """
        Reveals the node and all the items within it to the red agent.

        Set all the:
            - Processes
            - Services
            - Applications
            - Folders
            - Files

        `revealed_to_red` to `True`.
        """
        self.red_scan_countdown = self.node_scan_duration

    def power_on(self):
        """Power on the Node, enabling its NICs if it is in the OFF state."""
        if self.operating_state == NodeOperatingState.OFF:
            self.operating_state = NodeOperatingState.BOOTING
            self.start_up_countdown = self.start_up_duration

        if self.start_up_duration <= 0:
            self.operating_state = NodeOperatingState.ON
            self._start_up_actions()
            self.sys_log.info("Power on")
            for network_interface in self.network_interfaces.values():
                network_interface.enable()

    def power_off(self):
        """Power off the Node, disabling its NICs if it is in the ON state."""
        if self.operating_state == NodeOperatingState.ON:
            for network_interface in self.network_interfaces.values():
                network_interface.disable()
            self.operating_state = NodeOperatingState.SHUTTING_DOWN
            self.shut_down_countdown = self.shut_down_duration

        if self.shut_down_duration <= 0:
            self._shut_down_actions()
            self.operating_state = NodeOperatingState.OFF
            self.sys_log.info("Power off")

    def reset(self):
        """
        Resets the node.

        Powers off the node and sets is_resetting to True.
        Applying more timesteps will eventually turn the node back on.
        """
        if self.operating_state.ON:
            self.is_resetting = True
            self.sys_log.info("Resetting")
            self.power_off()

    def connect_nic(self, network_interface: NetworkInterface):
        """
        Connect a Network Interface to the node.

        :param network_interface: The NIC to connect.
        :raise NetworkError: If the NIC is already connected.
        """
        if network_interface.uuid not in self.network_interfaces:
            self.network_interfaces[network_interface.uuid] = network_interface
            self.network_interface[len(self.network_interfaces)] = network_interface
            network_interface._connected_node = self
            network_interface.port_num = len(self.network_interfaces)
            network_interface.parent = self
            self.sys_log.info(f"Connected Network Interface {network_interface}")
            if self.operating_state == NodeOperatingState.ON:
                network_interface.enable()
            self._nic_request_manager.add_request(
                network_interface.uuid, RequestType(func=network_interface._request_manager)
            )
        else:
            msg = f"Cannot connect NIC {network_interface} as it is already connected"
            self.sys_log.logger.error(msg)
            raise NetworkError(msg)

    def disconnect_nic(self, network_interface: Union[NetworkInterface, str]):
        """
        Disconnect a NIC (Network Interface Card) from the node.

        :param network_interface: The NIC to Disconnect, or its UUID.
        :raise NetworkError: If the NIC is not connected.
        """
        if isinstance(network_interface, str):
            network_interface = self.network_interfaces.get(network_interface)
        if network_interface or network_interface.uuid in self.network_interfaces:
            for port, _nic in self.network_interface.items():
                if network_interface == _nic:
                    self.network_interface.pop(port)
                    break
            self.network_interfaces.pop(network_interface.uuid)
            network_interface.parent = None
            network_interface.disable()
            self.sys_log.info(f"Disconnected Network Interface {network_interface}")
            self._nic_request_manager.remove_request(network_interface.uuid)
        else:
            msg = f"Cannot disconnect NIC {network_interface} as it is not connected"
            self.sys_log.logger.error(msg)
            raise NetworkError(msg)

    def ping(self, target_ip_address: Union[IPv4Address, str], pings: int = 4) -> bool:
        """
        Ping an IP address, performing a standard ICMP echo request/response.

        :param target_ip_address: The target IP address to ping.
        :param pings: The number of pings to attempt, default is 4.
        :return: True if the ping is successful, otherwise False.
        """
        if not isinstance(target_ip_address, IPv4Address):
            target_ip_address = IPv4Address(target_ip_address)
        if self.software_manager.icmp:
            return self.software_manager.icmp.ping(target_ip_address, pings)
        return False

    @abstractmethod
    def receive_frame(self, frame: Frame, from_network_interface: NetworkInterface):
        """
        Receive a Frame from the connected NIC and process it.

        This is an abstract implementation of receive_frame with some very basic functionality (ARP population). All
        Node subclasses should have their own implementation of receive_frame that first calls super().receive_frame(
        ) before implementing its own internal receive_frame logic.

        :param frame: The Frame being received.
        :param from_network_interface: The Network Interface that received the frame.
        """
        if self.operating_state == NodeOperatingState.ON:
            if frame.ip:
                if self.software_manager.arp:
                    self.software_manager.arp.add_arp_cache_entry(
                        ip_address=frame.ip.src_ip_address,
                        mac_address=frame.ethernet.src_mac_addr,
                        network_interface=from_network_interface,
                    )
        else:
            return

    def install_service(self, service: Service) -> None:
        """
        Install a service on this node.

        :param service: Service instance that has not been installed on any node yet.
        :type service: Service
        """
        if service in self:
            _LOGGER.warning(f"Can't add service {service.uuid} to node {self.uuid}. It's already installed.")
            return
        self.services[service.uuid] = service
        service.parent = self
        service.install()  # Perform any additional setup, such as creating files for this service on the node.
        self._service_request_manager.add_request(service.uuid, RequestType(func=service._request_manager))

    def uninstall_service(self, service: Service) -> None:
        """
        Uninstall and completely remove service from this node.

        :param service: Service object that is currently associated with this node.
        :type service: Service
        """
        if service not in self:
            _LOGGER.warning(f"Can't remove service {service.uuid} from node {self.uuid}. It's not installed.")
            return
        service.uninstall()  # Perform additional teardown, such as removing files or restarting the machine.
        self.services.pop(service.uuid)
        service.parent = None
        self.sys_log.info(f"Uninstalled service {service.name}")
        _LOGGER.info(f"Removed service {service.uuid} from node {self.uuid}")
        self._service_request_manager.remove_request(service.uuid)

    def install_application(self, application: Application) -> None:
        """
        Install an application on this node.

        :param application: Application instance that has not been installed on any node yet.
        :type application: Application
        """
        if application in self:
            _LOGGER.warning(f"Can't add application {application.uuid} to node {self.uuid}. It's already installed.")
            return
        self.applications[application.uuid] = application
        application.parent = self
        self._application_request_manager.add_request(application.uuid, RequestType(func=application._request_manager))

    def uninstall_application(self, application: Application) -> None:
        """
        Uninstall and completely remove application from this node.

        :param application: Application object that is currently associated with this node.
        :type application: Application
        """
        if application not in self:
            _LOGGER.warning(f"Can't remove application {application.uuid} from node {self.uuid}. It's not installed.")
            return
        self.applications.pop(application.uuid)
        application.parent = None
        self.sys_log.info(f"Uninstalled application {application.name}")
        _LOGGER.info(f"Removed application {application.uuid} from node {self.uuid}")
        self._application_request_manager.remove_request(application.uuid)

    def _shut_down_actions(self):
        """Actions to perform when the node is shut down."""
        # Turn off all the services in the node
        for service_id in self.services:
            self.services[service_id].stop()

        # Turn off all the applications in the node
        for app_id in self.applications:
            self.applications[app_id].close()

        # Turn off all processes in the node
        # for process_id in self.processes:
        #     self.processes[process_id]

    def _start_up_actions(self):
        """Actions to perform when the node is starting up."""
        # Turn on all the services in the node
        for service_id in self.services:
            self.services[service_id].start()

        # Turn on all the applications in the node
        for app_id in self.applications:
            self.applications[app_id].run()

        # Turn off all processes in the node
        # for process_id in self.processes:
        #     self.processes[process_id]

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Service):
            return item.uuid in self.services
        return None
