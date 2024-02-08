.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

#############
Base Hardware
#############

The ``base.py`` module in ``primaite.simulator.network.hardware`` provides foundational components, interfaces, and classes for
modeling network hardware within PrimAITE simulations. It establishes core building blocks and abstractions that more
complex, specialized hardware components inherit from and build upon.

The key elements defined in ``base.py`` are:

NetworkInterface
================

- Abstract base class for network interfaces like NICs. Defines common attributes like MAC address, speed, MTU.
- Requires subclasses to implement ``enable()``, ``disable()``, ``send_frame()`` and ``receive_frame()``.
- Provides basic state description and request handling capabilities.

Node
====

The Node class is the most crucial component defined in base.py, serving as the parent class for all nodes within a
PrimAITE network simulation.

It encapsulates the following key attributes and behaviors:

- ``hostname`` - The node's hostname on the network.
- ``network_interfaces`` - Dict of NetworkInterface objects attached to the node.
- ``operating_state`` - The hardware state (on/off) of the node.
- ``sys_log`` - System log to record node events.
- ``session_manager`` - Manages user sessions on the node.
- ``software_manager`` - Manages software and services installed on the node.
- ``connect_nic()`` - Connects a NetworkInterface to the node.
- ``disconnect_nic()`` - Disconnects a NetworkInterface from the node.
- ``receive_frame()`` - Receive and process an incoming network frame.
- ``apply_timestep()`` - Progresses node state for a simulation timestep.
- ``power_on()`` - Powers on the node and enables NICs.
- ``power_off()`` - Powers off the node and disables NICs.


The Node class handles installation of system software, network connectivity, frame processing, system logging, and
power states. It establishes baseline functionality while allowing subclassing to model specific node types like hosts,
routers, firewalls etc. The flexible architecture enables composing complex network topologies.
