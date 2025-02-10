.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _NTPClient:

NTPClient
#########

The NTPClient provides a client interface for connecting to the ``NTPServer``.

Key features
============

- Connects to the ``NTPServer`` via the ``SoftwareManager``.

Usage
=====

- Install on a Node via the ``SoftwareManager`` to start the database service.
- Service runs on UDP port 123 by default.

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
    from primaite.simulator.system.services.ntp.ntp_client import NTPClient

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Install NTPClient on server
    server.software_manager.install(NTPClient)
    ntp_client: NTPClient = server.software_manager.software.get("ntp-client")
    ntp_client.start()

    ntp_client.configure(ntp_server_ip_address=IPv4Address("192.168.0.10"))


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
                    - ref: ntp_client
                    type: ntp-client
                    options:
                        ntp_server_ip: 192.168.0.10

Configuration
=============

``ntp_server_ip``
"""""""""""""""""

Optional. Default value is ``None``.

The IP address of an NTP Server which provides a time that the ``NTPClient`` can synchronise to.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
