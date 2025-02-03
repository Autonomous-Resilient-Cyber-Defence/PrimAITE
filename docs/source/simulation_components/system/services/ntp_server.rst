.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _NTPServer:

NTPServer
#########

The ``NTPServer`` provides a NTP Server simulation by extending the base Service class.

NTP Client
==========

The ``NTPClient`` provides a NTP Client simulation by extending the base Service class.

Key capabilities
================

- Simulates NTP requests and NTPPacket transfer across a network
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
=====
- Install on a Node via the ``SoftwareManager`` to start the database service.
- Service runs on UDP port 123 by default.

Implementation
==============

- NTP request and responses use a ``NTPPacket`` object
- Extends Service class for integration with ``SoftwareManager``.


Examples
========

Python
""""""

.. code-block:: python

    from primaite.simulator.network.hardware.nodes.host.server import Server
    from primaite.simulator.system.services.ntp.ntp_server import NTPServer

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Install NTPServer on server
    server.software_manager.install(NTPServer)
    ntp_server: NTPServer = server.software_manager.software.get("NTPServer")
    ntp_server.start()


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
                    - ref: ntp_server
                    type: ntp-server


``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
