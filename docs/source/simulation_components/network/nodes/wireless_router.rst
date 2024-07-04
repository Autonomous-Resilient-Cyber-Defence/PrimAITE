.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

######
Router
######

The ``WirelessRouter`` class extends the functionality of the standard ``Router`` class within PrimAITE,
integrating wireless networking capabilities. This class enables the simulation of a router that supports both wired
and wireless connections, allowing for a more comprehensive network simulation environment.

Overview
--------

The ``WirelessRouter`` class is designed to simulate the operations of a real-world wireless router, offering both
Ethernet and Wi-Fi connectivity. This includes managing wireless access points, configuring network interfaces for
different frequencies, and handling wireless frames transmission.

Features
--------

- **Dual Interface Support:** Supports both wired (Ethernet) and wireless network interfaces.
- **Wireless Access Point Configuration:** Allows configuring a wireless access point, including setting its IP
  address, subnet mask, and operating frequency.
- **Frequency Management:** Utilises the ``AirSpaceFrequency`` enum to set the operating frequency of wireless
  interfaces, supporting common Wi-Fi bands like 2.4 GHz and 5 GHz.
- **Seamless Wireless Communication:** Integrates with the ``AirSpace`` class to manage wireless transmissions across
  different frequencies, ensuring that wireless communication is realistically simulated.

Usage
-----

To use the ``WirelessRouter`` class in a network simulation, instantiate it similarly to a regular router but with
additional steps to configure wireless settings:

.. code-block:: python

    from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
    from primaite.simulator.network.airspace import AirSpaceFrequency, ChannelWidth

    # Instantiate the WirelessRouter
    wireless_router = WirelessRouter(hostname="MyWirelessRouter")

    # Configure a wired Ethernet interface
    wireless_router.configure_port(port=2, ip_address="192.168.1.1", subnet_mask="255.255.255.0")

    # Configure a wireless access point
    wireless_router.configure_wireless_access_point(
        port=1, ip_address="192.168.2.1",
        subnet_mask="255.255.255.0",
        frequency=AirSpaceFrequency.WIFI_2_4,
        channel_width=ChannelWidth.ChannelWidth.WIDTH_40_MHZ
    )



Integration with AirSpace
-------------------------

The ``WirelessRouter`` class works closely with the ``AirSpace`` class to simulate the transmission of wireless frames.
Frames sent from wireless interfaces are transmitted across the simulated airspace, allowing for interactions with
other wireless devices within the same frequency band.

Example Scenario
----------------

This example sets up a network with two PCs (PC A and PC B), each connected to their own `WirelessRouter`
(Router 1 and Router 2). These routers are then wirelessly connected to each other, enabling communication between the
PCs through the routers over the airspace. Access Control Lists (ACLs) are configured on the routers to permit ARP and
ICMP traffic, ensuring basic network connectivity and ping functionality.

.. code-block:: python

    from primaite.simulator.network.airspace import AirSpaceFrequency, ChannelWidth
    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.network.hardware.nodes.network.router import ACLAction
    from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
    from primaite.simulator.network.transmission.network_layer import IPProtocol
    from primaite.simulator.network.transmission.transport_layer import Port

    network = Network()

    # Configure PC A
    pc_a = Computer(
        hostname="pc_a",
        ip_address="192.168.0.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.0.1",
        start_up_duration=0,
    )
    pc_a.power_on()
    network.add_node(pc_a)

    # Configure Router 1
    router_1 = WirelessRouter(hostname="router_1", start_up_duration=0)
    router_1.power_on()
    network.add_node(router_1)

    # Configure the connection between PC A and Router 1 port 2
    router_1.configure_router_interface("192.168.0.1", "255.255.255.0")
    network.connect(pc_a.network_interface[1], router_1.router_interface)

    # Configure Router 1 ACLs
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)
    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)

    # Configure PC B
    pc_b = Computer(
        hostname="pc_b",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.2.1",
        start_up_duration=0,
    )
    pc_b.power_on()
    network.add_node(pc_b)

    # Configure Router 2
    router_2 = WirelessRouter(hostname="router_2", start_up_duration=0)
    router_2.power_on()
    network.add_node(router_2)

    # Configure the connection between PC B and Router 2 port 2
    router_2.configure_router_interface("192.168.2.1", "255.255.255.0")
    network.connect(pc_b.network_interface[1], router_2.router_interface)

    # Configure the wireless connection between Router 1 and Router 2
    router_1.configure_wireless_access_point(
        port=1,
        ip_address="192.168.1.1",
        subnet_mask="255.255.255.0",
        frequency=AirSpaceFrequency.WIFI_2_4,
        channel_width=ChannelWidth.ChannelWidth.WIDTH_40_MHZ
    )
    router_2.configure_wireless_access_point(
        port=1,
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        frequency=AirSpaceFrequency.WIFI_2_4,
        channel_width=ChannelWidth.ChannelWidth.WIDTH_40_MHZ
    )

    # Configure routes for inter-router communication
    router_1.route_table.add_route(
        address="192.168.2.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.2"
    )

    router_2.route_table.add_route(
        address="192.168.0.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.1"
    )

    # Test connectivity
    print(pc_a.ping(pc_b.network_interface[1].ip_address))
    print(pc_b.ping(pc_a.network_interface[1].ip_address))

This setup demonstrates the `WirelessRouter` class's capability to manage both wired and wireless connections within a
simulated network environment. By configuring the wireless access points and enabling the appropriate ACL rules, the
example facilitates basic network operations such as ARP resolution and ICMP pinging between devices across different
network segments.

Viewing Wireless Network Configuration
--------------------------------------

The `AirSpace.show()` function is an invaluable tool for inspecting the current wireless network configuration within
the PrimAITE environment. It presents a table summarising all wireless interfaces, including routers and access points,
that are active within the airspace. The table outlines each device's connected node name, MAC address, IP address,
subnet mask, operating frequency, and status, providing a comprehensive view of the wireless network topology.

Example Output
^^^^^^^^^^^^^^^

Below is an example output of the `AirSpace.show()` function, demonstrating the visibility it provides into the
wireless network:

.. code-block:: none

    +----------------+-------------------+-------------+---------------+--------------+---------+
    | Connected Node |    MAC Address    |  IP Address |  Subnet Mask  |  Frequency   |  Status |
    +----------------+-------------------+-------------+---------------+--------------+---------+
    |    router_1    | 31:29:46:53:ed:f8 | 192.168.1.1 | 255.255.255.0 | WiFi 2.4 GHz | Enabled |
    |    router_2    | 34:c8:47:43:98:78 | 192.168.1.2 | 255.255.255.0 | WiFi 2.4 GHz | Enabled |
    +----------------+-------------------+-------------+---------------+--------------+---------+

This table aids in verifying that wireless devices are correctly configured and operational. It also helps in
diagnosing connectivity issues by ensuring that devices are on the correct frequency and have the appropriate network
settings. The `Status` column, indicating whether a device is enabled or disabled, further assists in troubleshooting
by quickly identifying any devices that are not actively participating in the network.

Utilising the `AirSpace.show()` function is particularly beneficial in complex network simulations where multiple
wireless devices are in use. It provides a snapshot of the wireless landscape, facilitating the understanding of how
devices interact within the network and ensuring that configurations are aligned with the intended network architecture.

The addition of the ``WirelessRouter`` class enriches the PrimAITE simulation toolkit by enabling the simulation of
mixed wired and wireless network environments.
