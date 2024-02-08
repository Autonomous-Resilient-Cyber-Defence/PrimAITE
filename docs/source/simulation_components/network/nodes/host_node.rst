
#########
Host Node
#########

The ``host_node.py`` module is a core component of the PrimAITE project, aimed at simulating network host. It
encapsulates the functionality necessary for modelling the behaviour, communication capabilities, and interactions of
hosts in a networked environment.


HostNode Class
==============

The ``HostNode`` class acts as a foundational representation of a networked device or computer, capable of both
initiating and responding to network communications.

**Attributes:**

- Manages IP addressing with support for IPv4.
- Employs ``NIC`` or ``WirelessNIC`` (subclasses of``IPWiredNetworkInterface``) to simulate wired network connections.
- Integrates with ``SysLog`` for logging operational events, aiding in debugging and monitoring the host node's
  behaviour.

**Key Methods:**

- Facilitates the sending and receiving of ``Frame`` objects to simulate data link layer communications.
- Manages a variety of network services and applications, enhancing the simulation's realism and functionality.

Default Services and Applications
=================================

Both the ``HostNode`` and its subclasses come equipped with a suite of default services and applications critical for
fundamental network operations:

1. **ARP (Address Resolution Protocol):** The ``HostARP`` subclass enhances ARP functionality for host-specific
   operations.

2. **DNS (Domain Name System) Client:** Facilitates domain name resolution to IP addresses, enabling web navigation.

3. **FTP (File Transfer Protocol) Client:** Supports file transfers across the network.

4. **ICMP (Internet Control Message Protocol):** Utilised for network diagnostics and control, such as executing ping
   requests.

5. **NTP (Network Time Protocol) Client:** Synchronises the host's clock with network time servers.

6. **Web Browser:** A simulated application that allows the host to request and display web content.
