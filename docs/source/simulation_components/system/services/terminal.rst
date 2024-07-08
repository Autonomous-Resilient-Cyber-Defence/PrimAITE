.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _Terminal:

Terminal
########

The ``Terminal`` provides a generic terminal simulation, by extending the base Service class

Key capabilities
================

 - Authenticates User connection by maintaining an active User account.
 - Ensures packets are matched to an existing session
 - Simulates common Terminal commands
 - Leverages the Service base class for install/uninstall, status tracking etc.


Usage
=====

 - Install on a node via the ``SoftwareManager`` to start the Terminal
 - Terminal Clients connect, execute commands and disconnect.
 - Service runs on SSH port 22 by default.

Implementation
==============

- Manages SSH commands
- Ensures User login before sending commands
- Processes SSH commands
- Returns results in a  *<TBD>* format.


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
