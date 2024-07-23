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

 - Authenticates User connection by maintaining an active User account.
 - Ensures packets are matched to an existing session
 - Simulates common Terminal commands
 - Leverages the Service base class for install/uninstall, status tracking etc.

Usage
=====

 - Pre-Installs on any `HostNode` component. See the below code example of how to access the terminal.
 - Terminal Clients connect, execute commands and disconnect from remote components.
 - Ensures that users are logged in to the component before executing any commands.
 - Service runs on SSH port 22 by default.

Implementation
==============

The terminal takes inspiration from the `Database Client` and `Database Service` classes, and leverages the `UserSessionManager`
to provide User Credential authentication when receiving/processing commands.

Terminal acts as the interface between the user/component and both the Session and Requests Managers, facilitating
the passing of requests to both.


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
