.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


WebBrowser
==========

The ``WebBrowser`` provides a client interface for connecting to the ``WebServer``.

Key features
^^^^^^^^^^^^

- Connects to the ``WebServer`` via the ``SoftwareManager``.
- Simulates HTTP requests and HTTP packet transfer across a network
- Allows the emulation of HTTP requests between client and server:
    - Automatically uses ``DNSClient`` to resolve domain names
    - GET: performs an HTTP GET request from client to server
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
^^^^^

- Install on a Node via the ``SoftwareManager`` to start the ``WebBrowser``.
- Service runs on HTTP port 80 by default. (TODO: HTTPS)
- Execute sending an HTTP GET request with ``get_webpage``

Implementation
^^^^^^^^^^^^^^

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Provides easy interface for making HTTP requests between an HTTP client and server.
- Extends base Service class.


Example Usage
-------------

Dependencies
^^^^^^^^^^^^

.. code-block:: python

    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.nodes.computer import Computer
    from primaite.simulator.network.hardware.nodes.server import Server
    from primaite.simulator.system.applications.web_browser import WebBrowser
    from primaite.simulator.system.services.web_server.web_server_service import WebServer

Example peer to peer network
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    net = Network()

    pc1 = Computer(hostname="pc1", ip_address="192.168.1.50", subnet_mask="255.255.255.0")
    srv = Server(hostname="srv", ip_address="192.168.1.10", subnet_mask="255.255.255.0")
    pc1.power_on()
    srv.power_on()
    net.connect(pc1.network_interface[1], srv.network_interface[1])

Install the Web Server
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # web browser is automatically installed in computer nodes
    # IRL this is usually included with an OS
    client: WebBrowser = pc1.software_manager.software['WebBrowser']

    # install web server
    srv.software_manager.install(WebServer)
    webserv: WebServer = srv.software_manager.software['WebServer']

Open the web page
^^^^^^^^^^^^^^^^^

Using a domain name to connect to a website requires setting up DNS Servers. For this example, it is possible to use the IP address directly

.. code-block:: python

    # check that the get request succeeded
    print(client.get_webpage("http://192.168.1.10")) # should be True
