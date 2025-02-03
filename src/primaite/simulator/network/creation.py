# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from abc import ABC, abstractmethod
from ipaddress import IPv4Address
from typing import Any, ClassVar, Dict, Literal, Optional, Type

from pydantic import BaseModel, ConfigDict, model_validator

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


class NetworkNodeAdder(BaseModel):
    """
    Base class for adding a set of related nodes to a network in a standardised way.

    Child classes should define a ConfigSchema nested class that subclasses NetworkNodeAdder.ConfigSchema and a __call__
    method which performs the node addition to the network.

    Here is a template that users can use to define custom node adders:
    ```
    class YourNodeAdder(NetworkNodeAdder, identifier="your_name"):
        class ConfigSchema(NetworkNodeAdder.ConfigSchema):
            property_1 : str
            property_2 : int

        @classmethod
        def add_nodes_to_net(cls, config: ConfigSchema, network: Network) -> None:
            node_1 = Node(property_1, ...)
            node_2 = Node(...)
            network.connect(node_1.network_interface[1], node_2.network_interface[1])
            ...
    ```
    """

    class ConfigSchema(BaseModel, ABC):
        """
        Base schema for node adders.

        Child classes of NetworkNodeAdder must define a schema which inherits from this schema. The identifier is used
        by the from_config method to select the correct node adder at runtime.
        """

        model_config = ConfigDict(extra="forbid")
        type: str
        """Uniquely identifies the node adder class to use for adding nodes to network."""

    _registry: ClassVar[Dict[str, Type["NetworkNodeAdder"]]] = {}

    def __init_subclass__(cls, identifier: Optional[str], **kwargs: Any) -> None:
        """
        Register a network node adder class.

        :param identifier: Unique name for the node adder to use for matching against primaite config entries.
        :type identifier: str
        :raises ValueError: When attempting to register a name that is already reserved.
        """
        super().__init_subclass__(**kwargs)
        if identifier is None:
            return
        if identifier in cls._registry:
            raise ValueError(f"Duplicate node adder {identifier}")
        cls._registry[identifier] = cls

    @classmethod
    @abstractmethod
    def add_nodes_to_net(cls, config: ConfigSchema, network: Network) -> None:
        """
        Add nodes to the network.

        Abstract method that must be overwritten by child classes. Use the config definition to create nodes and add
        them to the network that is passed in.

        :param config: Config object that defines how to create and add nodes to the network
        :type config: ConfigSchema
        :param network: PrimAITE network object to which to add nodes.
        :type network: Network
        """
        pass

    @classmethod
    def from_config(cls, config: Dict, network: Network) -> None:
        """
        Accept a config, find the relevant node adder class, and call it to add nodes to the network.

        Child classes do not need to define this method.

        :param config: Configuration object for the child adder class
        :type config: Dict
        :param network: The Network object to which to add nodes
        :type network: Network
        """
        if config["type"] not in cls._registry:
            raise ValueError(f"Invalid node adder type {config['type']}")
        adder_class = cls._registry[config["type"]]
        adder_class.add_nodes_to_net(config=adder_class.ConfigSchema(**config), network=network)


class OfficeLANAdder(NetworkNodeAdder, identifier="office_lan"):
    """Creates an office LAN."""

    class ConfigSchema(NetworkNodeAdder.ConfigSchema):
        """Configuration schema for OfficeLANAdder."""

        type: Literal["office_lan"] = "office_lan"
        lan_name: str
        """Name of lan used for generating hostnames for new nodes."""
        subnet_base: int
        """Used as the third octet of IP addresses for nodes in the network."""
        pcs_ip_block_start: int
        """Starting point for the fourth octet of IP addresses of nodes in the network."""
        num_pcs: int
        """The number of hosts to generate."""
        include_router: bool = True
        """Whether to include a router in the new office LAN."""
        bandwidth: int = 100
        """Data bandwidth to the LAN measured in Mbps."""

        @model_validator(mode="after")
        def check_ip_range(self) -> "OfficeLANAdder.ConfigSchema":
            """Make sure the ip addresses of hosts don't exceed the maximum possible ip address."""
            if self.pcs_ip_block_start + self.num_pcs >= 254:
                raise ValueError(
                    f"Cannot create {self.num_pcs} pcs starting at ip block {self.pcs_ip_block_start} "
                    f"because ip address octets cannot exceed 254."
                )
            return self

    @classmethod
    def add_nodes_to_net(cls, config: ConfigSchema, network: Network) -> None:
        """
        Add an office lan to the network according to the config definition.

        This method creates a number of hosts and enough switches such that all hosts can be connected to a switch.
        Optionally, a router is added to connect the switches together. All the nodes and networking devices are added
        to the provided network.

        :param config: Configuration object specifying office LAN parameters
        :type config: OfficeLANAdder.ConfigSchema
        :param network: The PrimAITE network to which to add the office LAN.
        :type network: Network
        :raises ValueError: upon invalid configuration
        """
        # Calculate the required number of switches
        num_of_switches = num_of_switches_required(num_nodes=config.num_pcs)
        effective_network_interface = 23  # One port less for router connection
        if config.pcs_ip_block_start <= num_of_switches:
            raise ValueError(
                f"pcs_ip_block_start must be greater than the number of required switches {num_of_switches}"
            )

        # Create a core switch if more than one edge switch is needed
        if num_of_switches > 1:
            core_switch = Switch(hostname=f"switch_core_{config.lan_name}", start_up_duration=0)
            core_switch.power_on()
            network.add_node(core_switch)
            core_switch_port = 1

        # Initialise the default gateway to None
        default_gateway = None

        # Optionally include a router in the LAN
        if config.include_router:
            default_gateway = IPv4Address(f"192.168.{config.subnet_base}.1")
            router = Router(hostname=f"router_{config.lan_name}", start_up_duration=0)
            router.power_on()
            router.acl.add_rule(
                action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
            )
            router.acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)
            network.add_node(router)
            router.configure_port(port=1, ip_address=default_gateway, subnet_mask="255.255.255.0")
            router.enable_port(1)

        # Initialise the first edge switch and connect to the router or core switch
        switch_port = 0
        switch_n = 1
        switch = Switch(hostname=f"switch_edge_{switch_n}_{config.lan_name}", start_up_duration=0)
        switch.power_on()
        network.add_node(switch)
        if num_of_switches > 1:
            network.connect(
                core_switch.network_interface[core_switch_port],
                switch.network_interface[24],
                bandwidth=config.bandwidth,
            )
        else:
            network.connect(router.network_interface[1], switch.network_interface[24], bandwidth=config.bandwidth)

        # Add PCs to the LAN and connect them to switches
        for i in range(1, config.num_pcs + 1):
            # Add a new edge switch if the current one is full
            if switch_port == effective_network_interface:
                switch_n += 1
                switch_port = 0
                switch = Switch(hostname=f"switch_edge_{switch_n}_{config.lan_name}", start_up_duration=0)
                switch.power_on()
                network.add_node(switch)
                # Connect the new switch to the router or core switch
                if num_of_switches > 1:
                    core_switch_port += 1
                    network.connect(
                        core_switch.network_interface[core_switch_port],
                        switch.network_interface[24],
                        bandwidth=config.bandwidth,
                    )
                else:
                    network.connect(
                        router.network_interface[1], switch.network_interface[24], bandwidth=config.bandwidth
                    )

            # Create and add a PC to the network
            pc = Computer(
                hostname=f"pc_{i}_{config.lan_name}",
                ip_address=f"192.168.{config.subnet_base}.{i+config.pcs_ip_block_start-1}",
                subnet_mask="255.255.255.0",
                default_gateway=default_gateway,
                start_up_duration=0,
            )
            pc.power_on()
            network.add_node(pc)

            # Connect the PC to the switch
            switch_port += 1
            network.connect(switch.network_interface[switch_port], pc.network_interface[1], bandwidth=config.bandwidth)
            switch.network_interface[switch_port].enable()


def num_of_switches_required(num_nodes: int, max_network_interface: int = 24) -> int:
    """
    Calculate the minimum number of network switches required to connect a given number of nodes.

    Each switch is assumed to have one port reserved for connecting to a router, reducing the effective
    number of ports available for PCs. The function calculates the total number of switches needed
    to accommodate all nodes under this constraint.

    :param num_nodes: The total number of nodes that need to be connected in the network.
    :param max_network_interface: The maximum number of ports available on each switch. Defaults to 24.

    :return: The minimum number of switches required to connect all PCs.

    Example:
    >>> num_of_switches_required(5)
    1
    >>> num_of_switches_required(24,24)
    2
    >>> num_of_switches_required(48,24)
    3
    >>> num_of_switches_required(25,10)
    3
    """
    # Reduce the effective number of switch ports by 1 to leave space for the router
    effective_network_interface = max_network_interface - 1

    # Calculate the number of fully utilised switches and any additional switch for remaining PCs
    full_switches = num_nodes // effective_network_interface
    extra_pcs = num_nodes % effective_network_interface

    # Return the total number of switches required
    return full_switches + (1 if extra_pcs > 0 else 0)
