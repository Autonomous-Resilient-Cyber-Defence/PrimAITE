.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _DNSServer:

DNSServer
#########

Also known as a DNS Resolver, the ``DNSServer`` provides a DNS Server simulation by extending the base Service class.

Key capabilities
================

- Simulates DNS requests and DNSPacket transfer across a network
- Registers domain names and the IP Address linked to the domain name
- Returns the IP address for a given domain name within a DNS Packet that a DNS Client can read
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
=====
- Install on a Node via the ``SoftwareManager`` to start the database service.
- Service runs on TCP port 53 by default. (TODO: TCP for now, should be UDP in future)

Implementation
==============

- DNS request and responses use a ``DNSPacket`` object
- Extends Service class for integration with ``SoftwareManager``.

Examples
========

Python
""""""

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.hardware.nodes.host.server import Server
    from primaite.simulator.system.services.dns.dns_server import DNSServer

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Install DNSServer on server
    server.software_manager.install(DNSServer)
    dns_server: DNSServer = server.software_manager.software.get("DNSServer")
    dns_server.start()

    # configure DatabaseService
    dns_server.dns_register("arcd.com", IPv4Address("192.168.10.10"))


Via Configuration
"""""""""""""""""

.. code-block:: yaml

    simulation:
        network:
            nodes:
                - ref: example_server
                hostname: example_server
                type: server
                ...
                services:
                    - ref: dns_server
                    type: DNSServer
                    options:
                        domain_mapping:
                            arcd.com: 192.168.0.10
                            another-example.com: 192.168.10.10

Configuration
=============


``domain_mapping``
""""""""""""""""""

Domain mapping takes the domain and IP Addresses as a key-value pairs i.e.

If the domain is "arcd.com" and the IP Address attributed to the domain is 192.168.0.10, then the value should be ``arcd.com: 192.168.0.10``

The key must be a string and the IP Address must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
