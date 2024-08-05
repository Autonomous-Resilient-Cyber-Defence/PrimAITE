.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _Terminal:

Terminal
========

The ``Terminal.py`` class provides a generic terminal simulation, by extending the base Service class within PrimAITE. The aim of this is to act as the primary entrypoint for Nodes within the environment.


Overview
--------

The Terminal service uses Secure Socket (SSH) as the communication method between terminals. They operate on port 22, and are part of the services automatically
installed on Nodes when they are instantiated.

Key capabilities
================

 - Ensures packets are matched to an existing session
 - Simulates common Terminal processes/commands.
 - Leverages the Service base class for install/uninstall, status tracking etc.

Usage
=====

 - Pre-Installs on any `Node` (component with the exception of `Switches`).
 - Terminal Clients connect, execute commands and disconnect from remote nodes.
 - Ensures that users are logged in to the component before executing any commands.
 - Service runs on SSH port 22 by default.

Implementation
==============

 - Manages remote connections in a dictionary by session ID.
 - Processes commands, forwarding to the ``RequestManager`` or ``SessionManager`` where appropriate.
 - Extends Service class.
  - A detailed guide on the implementation and functionality of the Terminal class can be found in the "Terminal-Processing" jupyter notebook.

Python
""""""

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.services.terminal.terminal import Terminal
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState

    client = Computer(
        hostname="client",
        ip_address="192.168.10.21",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        operating_state=NodeOperatingState.ON,
    )

    terminal: Terminal = client.software_manager.software.get("Terminal")
