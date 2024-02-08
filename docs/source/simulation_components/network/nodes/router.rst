.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

######
Router
######

The ``router.py`` module is a pivotal component of the PrimAITE, designed to simulate the complex functionalities of a
router within a network simulation. Routers are essential for directing traffic between different network segments,
and this module provides the tools necessary to model these devices' behaviour and capabilities accurately.

Router Class
------------

The ``Router`` class embodies the core functionalities of a network router, extending the ``NetworkNode`` class to
incorporate routing-specific behaviours.

**Key Features:**

- **IP Routing:** Supports dynamic handling of IP packets, including forwarding based on destination IP addresses and
  subnetting.
- **Routing Table:** Maintains a routing table to determine the best path for forwarding packets.
- **Protocol Support:** Implements support for key networking protocols, including ARP for address resolution and ICMP
  for diagnostic messages.
- **Interface Management:** Manages multiple ``RouterInterface`` instances, enabling connections to different network
  segments.
- **Network Interface Configuration:** Tools for configuring router interfaces, including setting IP addresses, subnet
  masks, and enabling/disabling interfaces.
- **Logging and Monitoring:** Integrates with ``SysLog`` for logging operational events, aiding in debugging and
  monitoring router behaviour.

**Operations:**

- **Packet Forwarding:** Utilises the routing table to forward packets to their correct destination across
  interconnected networks.
- **ARP Handling:** Responds to ARP requests for any IP addresses configured on its interfaces, facilitating
  communication within local networks.
- **ICMP Processing:** Generates and processes ICMP packets, such as echo requests and replies, for network diagnostics.

The ``router.py`` module offers a comprehensive simulation of router functionalities. By providing detailed modelling of router operations, including packet forwarding, interface management, and protocol handling, PrimAITE enables the exploration of advanced network topologies and routing scenarios.
