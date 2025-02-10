.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _network:

Network
=======

The ``Network`` class serves as the backbone of the simulation. It offers a framework to manage various network
components such as routers, switches, servers, and clients. This document provides a detailed explanation of how to
effectively use the ``Network`` class.

Example Usage
-------------

Below demonstrates how to use the Router node to connect Nodes, and block traffic using ACLs. For this demonstration,
we'll use the following Network that has a client, server, two switches, and a router.

.. code-block:: text

    +------------+      +------------+      +------------+      +------------+      +------------+
    |            |      |            |      |            |      |            |      |            |
    |  client_1  +------+  switch_2  +------+  router_1  +------+  switch_1  +------+  server_1  |
    |            |      |            |      |            |      |            |      |            |
    +------------+      +------------+      +------------+      +------------+      +------------+

1. Relevant imports

.. code-block:: python

    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.base import NetworkInterface
    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.network.hardware.nodes.network.router import Router, ACLAction
    from primaite.simulator.network.hardware.nodes.host.server import Server
    from primaite.simulator.network.hardware.nodes.network.switch import Switch
    from primaite.simulator.network.transmission.network_layer import IPProtocol
    from primaite.simulator.network.transmission.transport_layer import Port

2. Create the Network

.. code-block:: python

    network = Network()

3. Create and configure the Router

.. code-block:: python

    router_1 = Router(hostname="router_1", num_ports=3)
    router_1.power_on()
    router_1.configure_port(port=1, ip_address="192.168.1.1", subnet_mask="255.255.255.0")
    router_1.configure_port(port=2, ip_address="192.168.2.1", subnet_mask="255.255.255.0")

4. Create and configure the two Switches

.. code-block:: python

    switch_1 = Switch(hostname="switch_1", num_ports=6)
    switch_1.power_on()
    switch_2 = Switch(hostname="switch_2", num_ports=6)
    switch_2.power_on()

5. Connect the Switches to the Router

.. code-block:: python

    network.connect(endpoint_a=router_1.network_interfaces[1], endpoint_b=switch_1.network_interface[6])
    router_1.enable_port(1)
    network.connect(endpoint_a=router_1.network_interfaces[2], endpoint_b=switch_2.network_interface[6])
    router_1.enable_port(2)

6. Create the Client and Server nodes.

.. code-block:: python

    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.2.1"
    )
    client_1.power_on()
    server_1 = Server(
        hostname="server_1",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1"
    )
    server_1.power_on()

7. Connect the Client and Server to the relevant Switch

.. code-block:: python

    network.connect(endpoint_a=switch_2.network_interface[1], endpoint_b=client_1.network_interface[1])
    network.connect(endpoint_a=switch_1.network_interface[1], endpoint_b=server_1.network_interface[1])

8. Add an ACL rule on the Router to allow ICMP traffic.

.. code-block:: python

    router_1.acl.add_rule(
        action=ACLAction.PERMIT,
        src_port=PORT_LOOKUP["ARP"],
        dst_port=PORT_LOOKUP["ARP"],
        position=22
    )

    router_1.acl.add_rule(
        action=ACLAction.PERMIT,
        protocol=PROTOCOL_LOOKUP["ICMP"],
        position=23
    )
