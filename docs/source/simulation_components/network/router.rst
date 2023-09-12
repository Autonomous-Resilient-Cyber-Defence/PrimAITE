.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _router:

Router Module
=============

The router module contains classes for simulating the functions of a network router.

Router
------

The Router class represents a multi-port network router that can receive, process, and route network packets between its ports and other Nodes

The router maintains internal state including:

- RouteTable - Routing table to lookup where to forward packets.
- AccessControlList - Access control rules to block or allow packets.
- ARP cache - MAC address lookups for connected devices.
- ICMP handler - Handles ICMP requests to router interfaces.

The router receives incoming frames on enabled ports. It processes the frame headers and applies the following logic:

1. Checks the AccessControlList if the packet is permitted. If blocked, it is dropped.
2. For permitted packets, routes the frame based on:
  - ARP cache lookups for destination MAC address.
  - ICMP echo requests handled directly.
  - RouteTable lookup to forward packet out other ports.
3. Updates ARP cache as it learns new information about the Network.



RouteTable
----------

The RouteTable holds RouteEntry objects representing routes. It finds the best route for a destination IP using a metric and the longest prefix match algorithm.

Routes can be added and looked up based on destination IP address. The RouteTable is used by the Router when forwarding packets between other Nodes.

AccessControlList
-----------------

The AccessControlList defines Access Control Rules to block or allow packets. Packets are checked against the rules to determine if they are permitted to be forwarded.

Rules can be added to deny or permit traffic based on IP, port, and protocol. The ACL is checked by the Router when packets are received.

Packet Processing
-----------------

-The Router supports the following protocols and packet types:

ARP
^^^

- Handles both ARP requests and responses.
- Updates ARP cache.
- Proxies ARP replies for connected networks.
- Routes ARP requests.

ICMP
^^^^

- Responds to ICMP echo requests to Router interfaces.
- Routes other ICMP messages based on routes.

TCP/UDP
^^^^^^^

- Forwards packets based on routes like IP.
- Applies ACL rules based on protocol, source/destination IP address, and source/destination port numbers.
- Decrements TTL and drops expired TTL packets.
