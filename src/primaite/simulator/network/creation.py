from ipaddress import IPv4Address
from typing import Optional

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port


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


def create_office_lan(
    lan_name: str,
    subnet_base: int,
    pcs_ip_block_start: int,
    num_pcs: int,
    network: Optional[Network] = None,
    include_router: bool = True,
) -> Network:
    """
    Creates a 2-Tier or 3-Tier office local area network (LAN).

    The LAN is configured with a specified number of personal computers (PCs), optionally including a router,
    and multiple edge switches to connect them. A core switch is added only if more than one edge switch is required.
    The network topology involves edge switches connected either directly to the router in a 2-Tier setup or
    to a core switch in a 3-Tier setup. If a router is included, it is connected to the core switch (if present)
    and configured with basic access control list (ACL) rules. PCs are distributed across the edge switches.


    :param str lan_name: The name to be assigned to the LAN.
    :param int subnet_base: The subnet base number to be used in the IP addresses.
    :param int pcs_ip_block_start: The starting block for assigning IP addresses to PCs.
    :param int num_pcs: The number of PCs to be added to the LAN.
    :param Optional[Network] network: The network to which the LAN components will be added. If None, a new network is
        created.
    :param bool include_router: Flag to determine if a router should be included in the LAN. Defaults to True.
    :return: The network object with the LAN components added.
    :raises ValueError: If pcs_ip_block_start is less than or equal to the number of required switches.
    """
    # Initialise the network if not provided
    if not network:
        network = Network()

    # Calculate the required number of switches
    num_of_switches = num_of_switches_required(num_nodes=num_pcs)
    effective_network_interface = 23  # One port less for router connection
    if pcs_ip_block_start <= num_of_switches:
        raise ValueError(f"pcs_ip_block_start must be greater than the number of required switches {num_of_switches}")

    # Create a core switch if more than one edge switch is needed
    if num_of_switches > 1:
        core_switch = Switch(hostname=f"switch_core_{lan_name}", start_up_duration=0)
        core_switch.power_on()
        network.add_node(core_switch)
        core_switch_port = 1

    # Initialise the default gateway to None
    default_gateway = None

    # Optionally include a router in the LAN
    if include_router:
        default_gateway = IPv4Address(f"192.168.{subnet_base}.1")
        router = Router(hostname=f"router_{lan_name}", start_up_duration=0)
        router.power_on()
        router.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)
        router.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)
        network.add_node(router)
        router.configure_port(port=1, ip_address=default_gateway, subnet_mask="255.255.255.0")
        router.enable_port(1)

    # Initialise the first edge switch and connect to the router or core switch
    switch_port = 0
    switch_n = 1
    switch = Switch(hostname=f"switch_edge_{switch_n}_{lan_name}", start_up_duration=0)
    switch.power_on()
    network.add_node(switch)
    if num_of_switches > 1:
        network.connect(core_switch.network_interface[core_switch_port], switch.network_interface[24])
    else:
        network.connect(router.network_interface[1], switch.network_interface[24])

    # Add PCs to the LAN and connect them to switches
    for i in range(1, num_pcs + 1):
        # Add a new edge switch if the current one is full
        if switch_port == effective_network_interface:
            switch_n += 1
            switch_port = 0
            switch = Switch(hostname=f"switch_edge_{switch_n}_{lan_name}", start_up_duration=0)
            switch.power_on()
            network.add_node(switch)
            # Connect the new switch to the router or core switch
            if num_of_switches > 1:
                core_switch_port += 1
                network.connect(core_switch.network_interface[core_switch_port], switch.network_interface[24])
            else:
                network.connect(router.network_interface[1], switch.network_interface[24])

        # Create and add a PC to the network
        pc = Computer(
            hostname=f"pc_{i}_{lan_name}",
            ip_address=f"192.168.{subnet_base}.{i+pcs_ip_block_start-1}",
            subnet_mask="255.255.255.0",
            default_gateway=default_gateway,
            start_up_duration=0,
        )
        pc.power_on()
        network.add_node(pc)

        # Connect the PC to the switch
        switch_port += 1
        network.connect(switch.network_interface[switch_port], pc.network_interface[1])
        switch.network_interface[switch_port].enable()

    return network
