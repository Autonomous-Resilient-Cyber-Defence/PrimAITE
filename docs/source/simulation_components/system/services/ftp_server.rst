.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _FTPServer:

FTPServer
#########

Provides a FTP Client-Server simulation by extending the base Service class.

Key capabilities
================

- Simulates FTP requests and FTPPacket transfer across a network
- Allows the emulation of FTP commands between an FTP client and server:
    - STOR: stores a file from client to server
    - RETR: retrieves a file from the FTP server
- Leverages the Service base class for install/uninstall, status tracking, etc.
- :ref:`FTPClient` and ``FTPServer`` utilise port 21 (FTP) throughout all file transfer / request

Usage
=====

- Install on a Node via the ``SoftwareManager`` to start the FTP server service.
- Service runs on FTP (command) port 21 by default

Implementation
==============

- FTP request and responses use a ``FTPPacket`` object
- Extends Service class for integration with ``SoftwareManager``.


Examples
========

Python
""""""

.. code-block:: python

    from primaite.simulator.network.hardware.nodes.host.server import Server
    from primaite.simulator.system.services.ftp.ftp_server import FTPServer

    # Create Server
    server = Server(config = {
        "hostname":"server",
        "ip_address":"192.168.2.2",
        "subnet_mask":"255.255.255.0",
        "default_gateway":"192.168.1.10",
        "start_up_duration":0,
        }
    )
    server.power_on()

    # Install FTPServer on server
    server.software_manager.install(FTPServer)
    ftp_server: FTPServer = server.software_manager.software.get("ftp-server")
    ftp_server.start()

    ftp_server.server_password = "test"

Via Configuration
"""""""""""""""""

.. code-block:: yaml

    simulation:
        network:
            nodes:
            - hostname: example_server
            type: server
            ...
            services:
            - type: ftp-server
            options:
                server_password: test

Configuration
=============

``server_password``
"""""""""""""""""""

Optional. Default value is ``None``.

The password that needs to be provided by a connecting :ref:`FTPClient` in order to create a successful connection.

``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
