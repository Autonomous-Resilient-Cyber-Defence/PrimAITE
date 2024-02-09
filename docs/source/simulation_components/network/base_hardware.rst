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
The Node class stands as a central component in ``base.py``, acting as the superclass for all network nodes within a
PrimAITE simulation.



Node Attributes
---------------


- **hostname**: The network hostname of the node.
- **operating_state**: Indicates the current hardware state of the node.
- **network_interfaces**: Maps interface names to NetworkInterface objects on the node.
- **network_interface**:  Maps port IDs to ``NetworkInterface`` objects on the node.
- **dns_server**: Specifies DNS servers for domain name resolution.
- **start_up_duration**: The time it takes for the node to become fully operational after being powered on.
- **shut_down_duration**: The time required for the node to properly shut down.
- **sys_log**: A system log for recording events related to the node.
- **session_manager**: Manages user sessions within the node.
- **software_manager**: Controls the installation and management of software and services on the node.

Node Behaviours/Functions
-------------------------


- **connect_nic()**: Connects a ``NetworkInterface`` to the node for network communication.
- **disconnect_nic()**: Removes a ``NetworkInterface`` from the node.
- **receive_frame()**: Handles the processing of incoming network frames.
- **apply_timestep()**: Advances the state of the node according to the simulation timestep.
- **power_on()**: Initiates the node, enabling all connected Network Interfaces and starting all Services and
  Applications, taking into account the `start_up_duration`.
- **power_off()**: Stops the node's operations, adhering to the `shut_down_duration`.
- **ping()**: Sends ICMP echo requests to a specified IP address to test connectivity.
- **has_enabled_network_interface()**: Checks if the node has any network interfaces enabled, facilitating network
  communication.
- **show()**: Provides a summary of the node's current state, including network interfaces, operational status, and
  other key attributes.


The Node class handles installation of system software, network connectivity, frame processing, system logging, and
power states. It establishes baseline functionality while allowing subclassing to model specific node types like hosts,
routers, firewalls etc. The flexible architecture enables composing complex network topologies.
