.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _WebBrowser:

WebBrowser
##########

The ``WebBrowser`` provides a client interface for connecting to the :ref:`WebServer`.

Key features
============

- Connects to the :ref:`WebServer` via the ``SoftwareManager``.
- Simulates HTTP requests and HTTP packet transfer across a network
- Allows the emulation of HTTP requests between client and server:
    - Automatically uses ``DNSClient`` to resolve domain names
    - GET: performs an HTTP GET request from client to server
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
=====

- Install on a Node via the ``SoftwareManager`` to start the ``WebBrowser``.
- Service runs on HTTP port 80 by default.
- Execute sending an HTTP GET request with ``get_webpage``

Implementation
==============

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Provides easy interface for making HTTP requests between an HTTP client and server.
- Extends base Service class.


Examples
========

Python
""""""

The ``WebBrowser`` utilises :ref:`DNSClient` and :ref:`DNSServer` to resolve a URL.

The :ref:`DNSClient` must be configured to use the :ref:`DNSServer`. The :ref:`DNSServer` should be configured to have the ``WebBrowser`` ``target_url`` within its ``domain_mapping``.

.. code-block:: python

    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.applications.web_browser import WebBrowser

    # Create Computer
    computer = Computer(config={
        "hostname":"computer",
        "ip_address":"192.168.1.2",
        "subnet_mask":"255.255.255.0",
        "default_gateway":"192.168.1.1",
        "start_up_duration":0,
        }
    )
    computer.power_on()

    # Install WebBrowser on computer
    computer.software_manager.install(WebBrowser)
    web_browser: WebBrowser = computer.software_manager.software.get("web-browser")
    web_browser.run()

    # configure the WebBrowser
    web_browser.target_url = "example.com"

    # once DNS server is configured with the correct domain mapping
    # this should work
    web_browser.get_webpage()

Via Configuration
"""""""""""""""""

.. code-block:: yaml

    simulation:
      network:
        nodes:
        - hostname: example_computer
        type: computer
        ...
        applications:
        - type: web-browser
        options:
          target_url: http://example.com/

Configuration
=============


``target_url``
""""""""""""""

The URL that the ``WebBrowser`` will request when ``get_webpage`` is called without parameters.

The URL can be in any format so long as the domain is within it e.g.

The domain ``example.com`` can be matched by

- http://example.com/
- example.com


``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
