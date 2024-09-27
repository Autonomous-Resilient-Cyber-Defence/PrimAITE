# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from typing import Any, ClassVar, Dict, Optional, Type

from primaite.simulator.network.hardware.base import NetworkInterface, Node
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.system.services.arp.arp import ARP


class NetworkNode(Node):
    """
    Represents an abstract base class for a network node that can receive and process network frames.

    This class provides a common interface for network nodes such as routers and switches, defining the essential
    behavior that allows these devices to handle incoming network traffic. Implementations of this class must
    provide functionality for receiving and processing frames received on their network interfaces.
    """

    _registry: ClassVar[Dict[str, Type["NetworkNode"]]] = {}
    """Registry of application types. Automatically populated when subclasses are defined."""

    def __init_subclass__(cls, identifier: str = "default", **kwargs: Any) -> None:
        """
        Register a networknode type.

        :param identifier: Uniquely specifies an networknode class by name. Used for finding items by config.
        :type identifier: str
        :raises ValueError: When attempting to register an networknode with a name that is already allocated.
        """
        if identifier == "default":
            return
        identifier = identifier.lower()
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Tried to define new networknode {identifier}, but this name is already reserved.")
        cls._registry[identifier] = cls

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
        return self.software_manager.software.get("ARP")
