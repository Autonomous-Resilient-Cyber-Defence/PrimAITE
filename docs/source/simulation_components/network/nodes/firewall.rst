.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

########
Firewall
########

The ``firewall.py`` module is a cornerstone in network security within the PrimAITE simulation, designed to simulate
the functionalities of a firewall in monitoring, controlling, and securing network traffic.

Firewall Class
--------------

The ``Firewall`` class extends the ``Router`` class, incorporating advanced capabilities to scrutinise, direct,
and filter traffic between various network zones, guided by predefined security rules and policies.

Key Features
============


- **Access Control Lists (ACLs):** Employs ACLs to establish security rules for permitting or denying traffic
  based on IP addresses, protocols, and port numbers, offering detailed oversight of network traffic.
- **Network Zone Segmentation:** Facilitates network division into distinct zones, including internal, external,
  and DMZ (De-Militarized Zone), each governed by specific inbound and outbound traffic rules.
- **Interface Configuration:** Enables the configuration of network interfaces for connectivity to external,
  internal, and DMZ networks, including setting up IP addressing and subnetting.
- **Protocol and Service Management:** Oversees and filters traffic across different protocols and services,
  enforcing adherence to established security policies.
- **Dynamic Traffic Processing:** Actively processes incoming and outgoing traffic via relevant ACLs, determining
  whether to forward or block based on the evaluation of rules.
- **Logging and Diagnostics:** Integrates with ``SysLog`` for detailed logging of firewall actions, supporting
  security monitoring and incident investigation.

Operations
==========

- **Rule Definition and Management:** Permits the creation and administration of ACL rules for precise traffic
  control, enabling the firewall to serve as an effective guard against unauthorised access.
- **Traffic Forwarding and Filtering:** Assesses network frames against ACL rules to allow or block traffic,
  forwarding permitted traffic towards its destination whilst obstructing malicious or unauthorised requests.
- **Interface and Zone Configuration:** Provides mechanisms for configuring and managing network interfaces,
  aligning with logical network architecture and security zoning requisites.

Configuring Interfaces
======================

To set up firewall interfaces, allocate IP addresses and subnet masks to the external, internal, and DMZ interfaces
using the respective configuration methods:

.. code-block:: python

   firewall.configure_external_port(ip_address="10.0.0.1", subnet_mask="255.255.255.0")
   firewall.configure_internal_port(ip_address="192.168.1.1", subnet_mask="255.255.255.0")
   firewall.configure_dmz_port(ip_address="172.16.0.1", subnet_mask="255.255.255.0")


Firewall ACLs
=============

In the PrimAITE network simulation, six Access Control Lists (ACLs) are crucial for delineating and enforcing
comprehensive network security measures. These ACLs, designated as internal inbound, internal outbound, DMZ inbound,
DMZ outbound, external inbound, and external outbound, each serve a specific role in orchestrating the flow of data
through the network. They allow for meticulous control of traffic entering, exiting, and moving within the network,
ensuring robust protection against unauthorised access and potential cyber threats. By leveraging these ACLs both
individually and collectively, users can simulate a multi-layered security architecture.

Internal Inbound ACL
^^^^^^^^^^^^^^^^^^^^

This ACL controls incoming traffic from the external network and DMZ to the internal network. It's crucial for
preventing unauthorised access to internal resources. By filtering incoming requests, it ensures that only legitimate
and necessary traffic can enter the internal network, protecting sensitive data and systems.

Internal Outbound ACL
^^^^^^^^^^^^^^^^^^^^^

The internal outbound ACL manages traffic leaving the internal network to the external network or DMZ. It can restrict
internal users or systems from accessing potentially harmful external sites or services, mitigate data exfiltration
risks.

DMZ Inbound ACL
^^^^^^^^^^^^^^^

This ACL regulates access to services hosted in the DMZ from the external network and internal network. Since the DMZ
hosts public-facing services like web and email servers, the DMZ inbound ACL is pivotal in allowing necessary access
while blocking malicious or unauthorised attempts, thus serving as a first line of defence.

DMZ Outbound ACL
^^^^^^^^^^^^^^^^

The ACL controls traffic from DMZ to the external network and internal network. It's used to restrict the DMZ services
from initiating unauthorised connections, which is essential for preventing compromised DMZ services from being used
as launchpads for attacks or data exfiltration.

External Inbound ACL
^^^^^^^^^^^^^^^^^^^^

This ACL filters all incoming traffic from the external network towards the internal network or DMZ. It's instrumental
in blocking unwanted or potentially harmful external traffic, ensuring that only traffic conforming to the security
policies is allowed into the network. **This ACL should only be used when the rule applies to both internal and DMZ
networks.**

External Outbound ACL
^^^^^^^^^^^^^^^^^^^^^

This ACL governs traffic leaving the internal network or DMZ to the external network. It plays a critical role in data
loss prevention (DLP) by restricting the types of data and services that internal users and systems can access or
interact with on external networks. **This ACL should only be used when the rule applies to both internal and DMZ
networks.**

Using ACLs Together
^^^^^^^^^^^^^^^^^^^

When these ACLs are used in concert, they create a robust security matrix that controls traffic flow in all directions:
into the internal network, out of the internal network, into the DMZ, out of the DMZ, and between these networks and
the external world. For example, while the external inbound ACL might block all incoming SSH requests to protect both
the internal network and DMZ, the internal outbound ACL could allow SSH access to specific external servers for
management purposes. Simultaneously, the DMZ inbound ACL might permit HTTP and HTTPS traffic to specific servers to
provide access to web services while the DMZ outbound ACL ensures these servers cannot make unauthorised outbound
connections.

By effectively configuring and managing these ACLs, users can establish and experiment with detailed security policies
that are finely tuned to their simulated network's unique requirements and threat models, achieving granular oversight
over traffic flows. This not only enables secure simulated interactions and data exchanges within PrimAITE environments
but also fortifies the virtual network against unauthorised access and cyber threats, mirroring real-world network
security practices.


ACL Configuration Examples
==========================

The subsequent examples provide detailed illustrations on configuring ACL rules within PrimAITE's firewall setup,
addressing various scenarios that encompass external attempts to access resources not only within the internal network
but also within the DMZ. These examples reflect the firewall's specific port configurations and showcase the
versatility and control that ACLs offer in managing network traffic, ensuring that security policies are precisely
enforced. Each example highlights different aspects of ACL usage, from basic traffic filtering to more complex
scenarios involving specific service access and protection against external threats.

**Blocking External Traffic to Internal Network**

To prevent all external traffic from accessing the internal network, with exceptions for approved services:

.. code-block:: python

   # Default rule to deny all external traffic to the internal network
   firewall.internal_inbound_acl.add_rule(
       action=ACLAction.DENY,
       src_ip_address="0.0.0.0",
       src_wildcard_mask="255.255.255.255",
       dst_ip_address="192.168.1.0",
       dst_wildcard_mask="0.0.0.255",
       position=1
   )

   # Exception rule to allow HTTP traffic from external to internal network
   firewall.internal_inbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       dst_port=Port.HTTP,
       dst_ip_address="192.168.1.0",
       dst_wildcard_mask="0.0.0.255",
       position=2
   )

**Allowing External Access to Specific Services in DMZ**

To enable external traffic to access specific services hosted within the DMZ:

.. code-block:: python

   # Allow HTTP and HTTPS traffic to the DMZ
   firewall.dmz_inbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       dst_port=Port.HTTP,
       dst_ip_address="172.16.0.0",
       dst_wildcard_mask="0.0.0.255",
       position=3
   )
   firewall.dmz_inbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       dst_port=Port.HTTPS,
       dst_ip_address="172.16.0.0",
       dst_wildcard_mask="0.0.0.255",
       position=4
   )

**Edge Case - Permitting External SSH Access to a Specific Internal Server**

To permit SSH access from a designated external IP to a specific server within the internal network:

.. code-block:: python

   # Allow SSH from a specific external IP to an internal server
   firewall.internal_inbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       src_ip_address="10.0.0.2",
       dst_port=Port.SSH,
       dst_ip_address="192.168.1.10",
       position=5
   )

**Restricting Access to Internal Database Server**

To limit database server access to selected external IP addresses:

.. code-block:: python

   # Allow PostgreSQL traffic from an authorized external IP to the internal DB server
   firewall.internal_inbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       src_ip_address="10.0.0.3",
       dst_port=Port.POSTGRES_SERVER,
       dst_ip_address="192.168.1.20",
       position=6
   )

   # Deny all other PostgreSQL traffic from external sources
   firewall.internal_inbound_acl.add_rule(
       action=ACLAction.DENY,
       protocol=IPProtocol.TCP,
       dst_port=Port.POSTGRES_SERVER,
       dst_ip_address="192.168.1.0",
       dst_wildcard_mask="0.0.0.255",
       position=7
   )

**Permitting DMZ Web Server Access while Blocking Specific Threats**

To authorize HTTP/HTTPS access to a DMZ-hosted web server, excluding known malicious IPs:

.. code-block:: python

   # Deny access from a known malicious IP to any DMZ service
   firewall.dmz_inbound_acl.add_rule(
       action=ACLAction.DENY,
       src_ip_address="10.0.0.4",
       dst_ip_address="172.16.0.0",
       dst_wildcard_mask="0.0.0.255",
       position=8
   )

   # Allow HTTP/HTTPS traffic to the DMZ web server
   firewall.dmz_inbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       dst_port=Port.HTTP,
       dst_ip_address="172.16.0.2",
       position=9
   )
   firewall.dmz_inbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       dst_port=Port.HTTPS,
       dst_ip_address="172.16.0.2",
       position=10
   )

**Enabling Internal to DMZ Restricted Access**

To facilitate restricted access from the internal network to DMZ-hosted services:

.. code-block:: python

   # Permit specific internal application server HTTPS access to a DMZ-hosted API
   firewall.internal_outbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       src_ip_address="192.168.1.30",  # Internal application server IP
       dst_port=Port.HTTPS,
       dst_ip_address="172.16.0.3",  # DMZ API server IP
       position=11
   )

   # Deny all other traffic from the internal network to the DMZ
   firewall.internal_outbound_acl.add_rule(
       action=ACLAction.DENY,
       src_ip_address="192.168.1.0",
       src_wildcard_mask="0.0.0.255",
       dst_ip_address="172.16.0.0",
       dst_wildcard_mask="0.0.0.255",
       position=12
   )

   # Corresponding rule in DMZ inbound ACL to allow the traffic from the specific internal server
   firewall.dmz_inbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       src_ip_address="192.168.1.30",  # Ensuring this specific source is allowed
       dst_port=Port.HTTPS,
       dst_ip_address="172.16.0.3",  # DMZ API server IP
       position=13
   )

   # Deny all other internal traffic to the specific DMZ API server
   firewall.dmz_inbound_acl.add_rule(
       action=ACLAction.DENY,
       src_ip_address="192.168.1.0",
       src_wildcard_mask="0.0.0.255",
       dst_port=Port.HTTPS,
       dst_ip_address="172.16.0.3",  # DMZ API server IP
       position=14
   )

**Blocking Unwanted External Access**

To block all SSH access attempts from the external network:

.. code-block:: python

   # Deny all SSH traffic from any external source
   firewall.external_inbound_acl.add_rule(
       action=ACLAction.DENY,
       protocol=IPProtocol.TCP,
       dst_port=Port.SSH,
       position=1
   )

**Allowing Specific External Communication**

To allow the internal network to initiate HTTP connections to the external network:

.. code-block:: python

   # Permit outgoing HTTP traffic from the internal network to any external destination
   firewall.external_outbound_acl.add_rule(
       action=ACLAction.PERMIT,
       protocol=IPProtocol.TCP,
       dst_port=Port.HTTP,
       position=2
   )


The examples above demonstrate the versatility and power of ACLs in crafting nuanced security policies. By combining
rules that specify permitted and denied traffic, both broadly and narrowly defined, administrators can construct
a firewall policy that safeguards network resources while ensuring necessary access is maintained.

Show Rules Function
===================

The show_rules function in the Firewall class displays the configurations of Access Control Lists (ACLs) within a
network firewall. It presents a comprehensive table detailing the rules that govern the filtering and management of
network traffic.

**Functionality:**

This function showcases each rule in an ACL, outlining its:

- **Index**: The rule's position within the ACL.
- **Action**: Specifies whether to permit or deny matching traffic.
- **Protocol**: The network protocol to which the rule applies.
- **Src IP and Dst IP**: Source and destination IP addresses.
- **Src Wildcard and Dst** Wildcard: Wildcard masks for source and destination IP ranges.
- **Src Port and Dst Port**: Source and destination ports.
- **Matched**: The number of times the rule has been matched by traffic.

Example Output:

.. code-block:: text

    +---------------------------------------------------------------------------------------------------------------+
    |                               firewall_1 - External Inbound Access Control List                               |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | Index | Action | Protocol | Src IP | Src Wildcard | Src Port  | Dst IP | Dst Wildcard | Dst Port  | Matched   |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | 22    | PERMIT | ANY      | ANY    | ANY          | 219 (ARP) | ANY    | ANY          | 219 (ARP) | 1         |
    | 23    | PERMIT | ICMP     | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    | 24    | PERMIT | ANY      | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 2         |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+

    +---------------------------------------------------------------------------------------------------------------+
    |                               firewall_1 - External Outbound Access Control List                              |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | Index | Action | Protocol | Src IP | Src Wildcard | Src Port  | Dst IP | Dst Wildcard | Dst Port  | Matched   |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | 22    | PERMIT | ANY      | ANY    | ANY          | 219 (ARP) | ANY    | ANY          | 219 (ARP) | 0         |
    | 23    | PERMIT | ICMP     | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    | 24    | PERMIT | ANY      | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 2         |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+

    +---------------------------------------------------------------------------------------------------------------+
    |                               firewall_1 - Internal Inbound Access Control List                               |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | Index | Action | Protocol | Src IP | Src Wildcard | Src Port  | Dst IP | Dst Wildcard | Dst Port  | Matched   |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | 1     | PERMIT | ANY      | ANY    | ANY          | 123 (NTP) | ANY    | ANY          | 123 (NTP) | 1         |
    | 22    | PERMIT | ANY      | ANY    | ANY          | 219 (ARP) | ANY    | ANY          | 219 (ARP) | 0         |
    | 23    | PERMIT | ICMP     | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    | 24    | DENY   | ANY      | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+

    +---------------------------------------------------------------------------------------------------------------+
    |                               firewall_1 - Internal Outbound Access Control List                              |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | Index | Action | Protocol | Src IP | Src Wildcard | Src Port  | Dst IP | Dst Wildcard | Dst Port  | Matched   |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | 1     | PERMIT | ANY      | ANY    | ANY          | 123 (NTP) | ANY    | ANY          | 123 (NTP) | 1         |
    | 22    | PERMIT | ANY      | ANY    | ANY          | 219 (ARP) | ANY    | ANY          | 219 (ARP) | 1         |
    | 23    | PERMIT | ICMP     | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    | 24    | DENY   | ANY      | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+

    +---------------------------------------------------------------------------------------------------------------+
    |                                  firewall_1 - DMZ Inbound Access Control List                                 |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | Index | Action | Protocol | Src IP | Src Wildcard | Src Port  | Dst IP | Dst Wildcard | Dst Port  | Matched   |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | 1     | PERMIT | ANY      | ANY    | ANY          | 123 (NTP) | ANY    | ANY          | 123 (NTP) | 1         |
    | 22    | PERMIT | ANY      | ANY    | ANY          | 219 (ARP) | ANY    | ANY          | 219 (ARP) | 0         |
    | 23    | PERMIT | ICMP     | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    | 24    | DENY   | ANY      | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+

    +---------------------------------------------------------------------------------------------------------------+
    |                                 firewall_1 - DMZ Outbound Access Control List                                 |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | Index | Action | Protocol | Src IP | Src Wildcard | Src Port  | Dst IP | Dst Wildcard | Dst Port  | Matched   |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+
    | 1     | PERMIT | ANY      | ANY    | ANY          | 123 (NTP) | ANY    | ANY          | 123 (NTP) | 1         |
    | 22    | PERMIT | ANY      | ANY    | ANY          | 219 (ARP) | ANY    | ANY          | 219 (ARP) | 1         |
    | 23    | PERMIT | ICMP     | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    | 24    | DENY   | ANY      | ANY    | ANY          | ANY       | ANY    | ANY          | ANY       | 0         |
    +-------+--------+----------+--------+--------------+-----------+--------+--------------+-----------+-----------+


The ``firewall.py`` module within PrimAITE empowers users to accurately model and simulate the pivotal role of
firewalls in network security. It provides detailed command over traffic flow and enforces security policies to safeguard
networked assets.
