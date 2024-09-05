.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _FTPClient:

FTPClient
#########

The ``FTPClient`` provides a client interface for connecting to the :ref:`FTPServer`.

Key features
============

- Connects to the :ref:`FTPServer` via the ``SoftwareManager``.
- Simulates FTP requests and FTPPacket transfer across a network
- Allows the emulation of FTP commands between an FTP client and server:
    - PORT: specifies the port that server should connect to on the client (currently only uses ``Port.FTP``)
    - STOR: stores a file from client to server
    - RETR: retrieves a file from the FTP server
    - QUIT: disconnect from server
- Leverages the Service base class for install/uninstall, status tracking, etc.
- :ref:`FTPClient` and ``FTPServer`` utilise port 21 (FTP) throughout all file transfer / request

Usage
=====

- Install on a Node via the ``SoftwareManager`` to start the FTP client service.
- Service runs on FTP (command) port 21 by default
- Execute sending a file to the FTP server with ``send_file``
- Execute retrieving a file from the FTP server with ``request_file``

Implementation
==============

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Provides easy interface for Nodes to transfer files between each other.
- Extends base Service class.

Examples
========

Python
""""""

.. code-block:: python

    from primaite.simulator.network.hardware.nodes.host.server import Server
    from primaite.simulator.system.services.ftp.ftp_client import FTPClient

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.10",
        start_up_duration=0,
    )
    server.power_on()

    # Install FTPClient on server
    server.software_manager.install(FTPClient)
    ftp_client: FTPClient = server.software_manager.software.get("FTPClient")
    ftp_client.start()


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
                    - ref: ftp_client
                    type: FTPClient

Configuration
=============

``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
