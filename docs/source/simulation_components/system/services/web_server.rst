.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _WebServer:

WebServer
#########

Provides a Web Server simulation by extending the base Service class.

Key capabilities
================

- Simulates a web server with the capability to also request data from a database
- Allows the emulation of HTTP requests between client (e.g. a web browser) and server
    - GET request sends a get all users request to the database server and returns an HTTP 200 status if the database is responsive
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
=====

- Install on a Node via the ``SoftwareManager`` to start the `WebServer`.
- Service runs on HTTP port 80 by default. (TODO: HTTPS)
- A :ref:`DatabaseClient` must be installed and configured on the same node as the ``WebServer`` if it is intended to send a users request i.e.
    in the case that the :ref:`WebBrowser` sends a request with users in its request path, the ``WebServer`` will utilise the ``DatabaseClient`` to send a request to the ``DatabaseService``

Implementation
==============

- HTTP request uses a ``HttpRequestPacket`` object
- HTTP response uses a ``HttpResponsePacket`` object
- Extends Service class for integration with ``SoftwareManager``.


Examples
========

Python
""""""

.. code-block:: python

    from primaite.simulator.network.hardware.nodes.host.server import Server
    from primaite.simulator.system.services.web_server.web_server import WebServer

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Install WebServer on server
    server.software_manager.install(WebServer)
    web_server: WebServer = server.software_manager.software.get("WebServer")
    web_server.start()

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
                    - ref: web_server
                    type: WebServer

Configuration
=============

.. include:: ../common/common_configuration.rst

.. |SOFTWARE_NAME| replace:: WebServer
.. |SOFTWARE_NAME_BACKTICK| replace:: ``WebServer``
