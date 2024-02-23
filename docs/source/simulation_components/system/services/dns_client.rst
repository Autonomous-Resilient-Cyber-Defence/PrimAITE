.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _DNSClient:

DNSClient
#########

The DNSClient provides a client interface for connecting to the :ref:`DNSServer`.

Key features
============

- Connects to the :ref:`DNSServer` via the ``SoftwareManager``.
- Executes DNS lookup requests and keeps a cache of known domain name IP addresses.
- Handles connection to DNSServer and querying for domain name IP addresses.

Usage
=====

- Install on a Node via the ``SoftwareManager`` to start the database service.
- Service runs on TCP port 53 by default. (TODO: TCP for now, should be UDP in future)
- Execute domain name checks with ``check_domain_exists``.
- ``DNSClient`` will automatically add the IP Address of the domain into its cache

Implementation
==============

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Provides easy interface for Nodes to find IP addresses via domain names.
- Extends base Service class.

Examples
========

Python
""""""

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.hardware.nodes.host.server import Server
    from primaite.simulator.system.services.dns.dns_client import DNSClient

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Install DNSClient on server
    server.software_manager.install(DNSClient)
    dns_client: DNSClient = server.software_manager.software.get("DNSClient")
    dns_client.start()

    # configure DatabaseService
    dns_client.dns_server = IPv4Address("192.168.0.10")


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
                    - ref: dns_client
                    type: DNSClient
                    options:
                        dns_server: 192.168.0.10

Configuration
=============

.. include:: ../common/common_configuration.rst

.. |SOFTWARE_NAME| replace:: DNSClient
.. |SOFTWARE_NAME_BACKTICK| replace:: ``DNSClient``

``dns_server``
""""""""""""""

Optional. Default value is ``None``.

The IP Address of the :ref:`DNSServer`.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.
