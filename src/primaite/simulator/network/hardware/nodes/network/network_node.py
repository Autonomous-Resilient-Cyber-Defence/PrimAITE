# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from typing import Any, Optional

from primaite.simulator.network.hardware.base import NetworkInterface, Node
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.system.services.arp.arp import ARP


class NetworkNode(Node, discriminator="network-node"):
    """
    Represents an abstract base class for a network node that can receive and process network frames.

    This class provides a common interface for network nodes such as routers and switches, defining the essential
    behavior that allows these devices to handle incoming network traffic. Implementations of this class must
    provide functionality for receiving and processing frames received on their network interfaces.
    """

    class ConfigSchema(Node.ConfigSchema):
        """Config schema for Node baseclass."""

        num_ports: Any = None  # temporarily unset to appease extra="forbid"

    @abstractmethod
    def receive_frame(self, frame: Frame, from_network_interface: NetworkInterface):
        """
        Abstract method that must be implemented by subclasses to define how to receive and process frames.

        This method is called when a frame is received by a network interface belonging to this node. Subclasses
        should implement the logic to process the frame, including examining its contents, making forwarding decisions,
        or performing any necessary actions based on the frame's protocol and destination.

        :param frame: The network frame that has been received.
        :type frame: Frame
        :param from_network_interface: The network interface on which the frame was received.
        :type from_network_interface: NetworkInterface
        """
        pass

    @property
    def arp(self) -> Optional[ARP]:
        """
        Return the ARP Cache of the NetworkNode.

        :return: ARP Cache for given NetworkNode
        :rtype: Optional[ARP]
        """
        return self.software_manager.software.get("arp")
