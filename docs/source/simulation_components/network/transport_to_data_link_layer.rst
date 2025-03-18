.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

Transport Layer to Data Link Layer
==================================

From the `OSI Model <[OSI Model](https://en.wikipedia.org/wiki/OSI_model,>`_, the transport layer (layer 4) through to
the data link layer (layer 2) have been loosely modelled to provide somewhat realistic network Frame generation.

Transport Layer (Layer 4)
#########################

**UDPHeader:** Represents a UDP header for the transport layer of a Network Frame. It includes source and destination
ports. UDP (User Datagram Protocol) is a connectionless and unreliable transport protocol used for data transmission.

..
    **TCPFlags:** Enum representing TCP control flags used in a TCP connection, such as SYN, ACK, FIN, and RST. TCP
    (Transmission Control Protocol) is a connection-oriented and reliable transport protocol used for establishing and
    maintaining data streams.
.. not currently used

**TCPHeader:** Represents a TCP header for the transport layer of a Network Frame. It includes source and destination
ports and TCP flags. This header is used for establishing and managing TCP connections.

Network Layer (Layer 3)
#######################


**IPProtocol:** Enum representing transport layer protocols in the IP header, such as TCP, UDP, and ICMP. It is used to
indicate the type of transport layer protocol being used in the IP header.

**Precedence:** Enum representing the Precedence levels in Quality of Service (QoS) for IP packets. It is used to
specify the priority of IP packets for Quality of Service handling.

**ICMPType:** Enumeration of common ICMP (Internet Control Message Protocol) types. It defines various types of ICMP
messages used for network troubleshooting and error reporting.

**ICMPPacket:** Models an ICMP header and includes ICMP type, code, identifier, and sequence number. It is used to
create ICMP packets for network control and error reporting.

**IPPacket:** Represents the IP layer of a network frame. It includes source and destination IP addresses, protocol
(TCP/UDP/ICMP), Time to Live (TTL), and Precedence for QoS. This header is used to route data packets across the
network based on IP addresses.


PrimAITE Layer (Custom Layer)
#############################

The PrimAITE layer has a custom header represented by the ``PrimaiteHeader`` class. It is designed to carry
PrimAITE-specific metadata required for reinforcement learning (RL) purposes.

**PrimaiteHeader:** This is a custom header for carrying PrimAITE-specific metadata. It contains the following fields:
 - **agent_source:** Enum representing the agent source of the transmission, such as RED, GREEN, or BLUE. This field helps identify the source or category of the data transmission.
 - **data_status:** Enum representing the status of the data in transmission, such as GOOD, COMPROMISED, or CORRUPT. This field indicates the integrity of the data being transmitted.

Data Link Layer (Layer 2)
#########################

**ARPEntry:** Represents an entry in the ARP cache. It consists of the following fields:

 - **mac_address:** The MAC address associated with the IP address.
 - **nic_uuid:** The NIC (Network Interface Card) UUID through which the NIC with the IP address is reachable.

**ARPPacket:** Represents the ARP layer of a network frame, and it includes the following fields:

 - **request:** ARP operation. Set to True for a request and False for a reply.
 - **sender_mac_addr:** Sender's MAC address.
 - **sender_ip_address:** Sender's IP address (IPv4 format).
 - **target_mac_addr:** Target's MAC address.
 - **target_ip_address:** Target's IP address (IPv4 format).

**EthernetHeader:** Represents the Ethernet layer of a network frame. It includes source and destination MAC addresses.
This header is used to identify the physical hardware addresses of devices on a local network.

**Frame:** Represents a complete network frame with all layers. It includes an ``EthernetHeader``, an ``IPPacket``, an
optional ``TCPHeader``, ``UDPHeader``, or ``ICMPPacket``, a ``PrimaiteHeader`` and an optional payload. This class
combines all the headers and data to create a complete network frame that can be sent over the network and used in the
PrimAITE simulation.

Basic Usage
###########

TCP SYN Frame
-------------

Here we will model a TCP synchronize request from a port 80 on the host 192.168.0.100 which has a NIC with a MAC
address of 'aa:bb:cc:dd:ee:ff' to port 8080 on the host 10.0.0.10 which has a NIC with a MAC address of
'11:22:33:44:55:66'.


.. code-block:: python

    from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
    from primaite.simulator.network.transmission.network_layer import IPPacket, IPProtocol
    from primaite.simulator.network.transmission.transport_layer import TCPFlags, TCPHeader

    # Transport Layer
    tcp_header = TCPHeader(
        src_port=80,
        dst_port=8080,
        flags=[TCPFlags.SYN]
    )

    # Network Layer
    ip_packet = IPPacket(
        src_ip_address="192.168.0.100",
        dst_ip_address="10.0.0.10",
        protocol=PROTOCOL_LOOKUP["TCP"]
    )
    # Data Link Layer
    ethernet_header = EthernetHeader(
        src_mac_addr="aa:bb:cc:dd:ee:ff",
        dst_mac_addr="11:22:33:44:55:66"
    )

    frame = Frame(
        ethernet=ethernet_header,
        ip=ip_packet,
        tcp=tcp_header,
    )

This produces the following ``Frame`` (displayed in json format)

.. code-block:: json

    {
        "ethernet": {
            "src_mac_addr": "aa:bb:cc:dd:ee:ff",
            "dst_mac_addr": "11:22:33:44:55:66"
        },
        "ip": {
            "src_ip_address": "192.168.0.100",
            "dst_ip_address": "10.0.0.10",
            "protocol": "tcp",
            "ttl": 64,
            "precedence": 0
        },
        "tcp": {
            "src_port": 80,
            "dst_port": 8080,
            "flags": [
                1
            ]
        },
        "primaite": {
            "agent_source": 2,
            "data_status": 1
        }
    }
