.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _network_examples:

``Network Examples``
====================

The below examples demonstrate how to configure different types of network in PrimAITE. They examples all have network
topology diagrams. Each rectangle represents a single Node, with the hostname inside of the rectangle. Physical inks are
represented by lines between two nodes. At each end of the line is the network interface number on the node the link is
connected to. Where the network interface is alsoa  layer-3 device, the label also contains the ip address and subnet
mask in CIDR format (``<ip address>/<no mask bits>``). All network diagrams on this page use the following node type
colour key:

.. image:: images/primaite_node_type_colour_key_dark.png
    :width: 300
    :align: center
    :class: only-dark

.. image:: images/primaite_node_type_colour_key_light.png
    :width: 300
    :align: center
    :class: only-light

#1. Client-Server P2P Network
-----------------------------

This example demonstrates how to create a minimal two-node client-server P2P network. The network consists of a Computer
and a Server on the same subnet with a single Link connecting the two.


.. image:: images/primaite_example_client_server_p2p_network_dark.png
    :align: center
    :class: only-dark

.. image:: images/primaite_example_client_server_p2p_network_light.png
    :align: center
    :class: only-light


Node Configuration
^^^^^^^^^^^^^^^^^^

Each node in the network is defined with several attributes, crucial for determining its role and functionality within
the Network:

- **Hostname**: The hostname assigned to the node on the Network.
- **Type**: Specifies the role of the node (e.g., computer, server, etc.).
- **IP Address and Subnet Mask**: These settings define the network interface's IP configuration which is essential for
  network communication.

Link Configuration
^^^^^^^^^^^^^^^^^^

The links section of the YAML configuration file specifies the physical connections between different network nodes
through their respective ports. This section is crucial for setting up the topology of the network, ensuring each node
is properly interconnected to facilitate communication and data transfer within the network. Each link in the network
is described with several attributes that define the connection between two endpoints:

- **endpoint_a_hostname**: The hostname of the first node in the connection.
- **endpoint_a_port**: The port number on the first node where the link is connected.
- **endpoint_b_hostname**: The hostname of the second node in the connection.
- **endpoint_b_port**: The port number on the second node where the link is connected.

Building the Config File
^^^^^^^^^^^^^^^^^^^^^^^^

**Defining the Network Scope and Scale**

1. **Identify the Participants**: The first step is to determine how many nodes are required and their roles. In this case,
   we've chosen a simple two-node P2P architecture with one client (`pc_1`) and one server (`server_1`). This setup is
   chosen to facilitate direct communication between a user (client) and a resource or service (server).
2. **Assign IP Addresses**: Choosing IP addresses that are within the same subnet (`192.168.1.x` with a subnet mask of
   `255.255.255.0`) ensures that the two nodes can communicate without routing.

**Configuring Individual Components**

3. **Node Configuration Simplicity**: With only two participants, the network design is straightforward, focusing on direct
   connectivity. Each node is configured with the minimal required settings: hostname, type, IP address, and subnet mask.
   The simplicity ensures that the configuration is easy to understand and manage.
4. **Logical Assignment of Roles**: The computer is designated as the client and the server as the service provider. This
   reflects typical real-world scenarios where a user's machine connects to a server that hosts resources or services.

**Configuring Connectivity**

5. **Direct Link Setup**: A direct link is planned between the two nodes. This is logical in a minimal setup where the
   primary goal is to ensure efficient, high-speed communication between the client and the server. This direct
   connection is configured through specified ports on each node, ensuring that these are the only two devices on this
   segment of the network.
6. **Port Selection**: Choosing port 1 for both nodes for the connection might be based on convention or simplicity, as
   typically, port numbering starts at 1. This makes it straightforward to follow and document.

.. code-block:: yaml

    simulation:
      network:
        nodes:
          - hostname: pc_1
            type: computer
            ip_address: 192.168.1.11
            subnet_mask: 255.255.255.0

          - hostname: server_1
            type: server
            ip_address: 192.168.1.13
            subnet_mask: 255.255.255.0

        links:
          - endpoint_a_hostname: pc_1
            endpoint_a_port: 1
            endpoint_b_hostname: server_1
            endpoint_b_port: 1

Inspection and Connectivity Test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following codeblock demonstrates how to access this network and all ``.show()`` to output the network details:

.. code-block:: python

  from primaite.simulator.network.networks import client_server_p2p_network

  network = client_server_p2p_network()

  network.show()

Which gives the output:

.. code-block:: text

  +---------------------------------------+
  |                 Nodes                 |
  +----------+----------+-----------------+
  | Node     | Type     | Operating State |
  +----------+----------+-----------------+
  | server_1 | Server   | ON              |
  | pc_1     | Computer | ON              |
  +----------+----------+-----------------+
  +------------------------------------------------------------------+
  |                           IP Addresses                           |
  +----------+------+--------------+---------------+-----------------+
  | Node     | Port | IP Address   | Subnet Mask   | Default Gateway |
  +----------+------+--------------+---------------+-----------------+
  | server_1 | 1    | 192.168.1.13 | 255.255.255.0 | None            |
  | pc_1     | 1    | 192.168.1.11 | 255.255.255.0 | None            |
  +----------+------+--------------+---------------+-----------------+
  +------------------------------------------------------------------------------------------------------------------------------------------------------+
  |                                                                        Links                                                                         |
  +------------+----------------------------------------+------------+----------------------------------------+-------+-------------------+--------------+
  | Endpoint A | A Port                                 | Endpoint B | B Port                                 | is Up | Bandwidth (MBits) | Current Load |
  +------------+----------------------------------------+------------+----------------------------------------+-------+-------------------+--------------+
  | pc_1       | Port 1: dd:70:be:52:b1:a9/192.168.1.11 | server_1   | Port 1: 17:3a:11:af:9b:b1/192.168.1.13 | True  | 100.0             | 0.00000%     |
  +------------+----------------------------------------+------------+----------------------------------------+-------+-------------------+--------------+

Finally, once the network is configured as expected, a connectivity test should be carried out. This can be done by
"pinging" one node from another node. The below code block demonstrates how `pc_1` pings `server_1`.

.. code-block:: python

    from primaite.simulator.network.networks import client_server_p2p_network_example

    network = client_server_p2p_network_example()

    pc_1 = network.get_node_by_hostname("pc_1")
    pc_1.ping("192.168.1.13)

If SysLog capture is toggled on and the simulation log level is set to INFO, the `pc_1` the result of the ping should be
captures in the `pc_1` SysLog:

.. code-block:: text

    +--------------------------------------------------------------------------------------------------------------------------------------------------------------+
    |                                                                         pc_1 Sys Log                                                                         |
    +-------------------------+-------+----------------------------------------------------------------------------------------------------------------------------+
    | Timestamp               | Level | Message                                                                                                                    |
    +-------------------------+-------+----------------------------------------------------------------------------------------------------------------------------+
    | 2024-04-24 20:50:06,016 | INFO  | Network Interface Port 1: b6:76:56:5b:4a:94/192.168.1.11 enabled                                                           |
    | 2024-04-24 20:50:06,017 | INFO  | Pinging 192.168.1.13:                                                                                                      |
    | 2024-04-24 20:50:06,017 | INFO  | Sending ARP request from NIC Port 1: b6:76:56:5b:4a:94/192.168.1.11 for ip 192.168.1.13                                    |
    | 2024-04-24 20:50:06,018 | INFO  | Adding ARP cache entry for ee:7e:d5:37:41:b8/192.168.1.13 via NIC Port 1: b6:76:56:5b:4a:94/192.168.1.11                   |
    | 2024-04-24 20:50:06,018 | INFO  | Received ARP response for 192.168.1.13 from ee:7e:d5:37:41:b8 via Network Interface Port 1: b6:76:56:5b:4a:94/192.168.1.11 |
    | 2024-04-24 20:50:06,019 | INFO  | Reply from 192.168.1.13: bytes=32, time=<1ms, TTL=63                                                                       |
    | 2024-04-24 20:50:06,020 | INFO  | Reply from 192.168.1.13: bytes=32, time=<1ms, TTL=63                                                                       |
    | 2024-04-24 20:50:06,021 | INFO  | Reply from 192.168.1.13: bytes=32, time=<1ms, TTL=63                                                                       |
    | 2024-04-24 20:50:06,022 | INFO  | Reply from 192.168.1.13: bytes=32, time=<1ms, TTL=63                                                                       |
    | 2024-04-24 20:50:06,022 | INFO  | Ping statistics for 192.168.1.13: Packets: Sent = 4, Received = 4, Lost = 0 (0.0% loss)                                    |
    +-------------------------+-------+----------------------------------------------------------------------------------------------------------------------------+


#2. Basic LAN
-------------

This example demonstrates setting up a basic Local Area Network (LAN) consisting of two Computers, a Server, a Switch,
and a Router, all configured on the same subnet. This type of network is commonly used in small office or home office
settings, providing shared access to resources like files and printers, while also offering a connection to the
internet through a router. This network provides a deeper dive into the new concepts introduced, including default
gateways, router configurations with ACLs, and port settings.

.. image:: images/primaite_example_basic_lan_network_dark.png
    :align: center
    :class: only-dark

.. image:: images/primaite_example_basic_lan_network_light.png
    :align: center
    :class: only-light

Node Configuration
^^^^^^^^^^^^^^^^^^

- **Type**: We now introduce two new node types, switch and router.

**Computers & Servers**

- **Default Gateway**: The IP address of the router that provides connectivity beyond the local network, essential for
  accessing external networks.

**Routers & Switches**

- **Number of Ports**: Indicates how many physical connections the switch supports, which determines how many devices
  can be connected.

**Routers**

- **Ports Configuration**: Each port on the router can be independently configured with an IP address and subnet mask,
  important for managing different network interfaces.
- **Access Control Lists** (ACLs): Specifies rules that control the flow of traffic into and out of the router,
  enhancing security by permitting or denying traffic based on source/destination IP addresses, and/or source/destination
  ports, and/or protocol.

Building the Config File
^^^^^^^^^^^^^^^^^^^^^^^^

**Defining the Network Scope and Scale**

1. **Identify the Participants**: For the basic LAN, we have identified the need for two computers (pc_1 and pc_2), a
   server (server_1), and networking devices including a switch (switch_1) and a router (router_1). This configuration
   supports a typical small office environment where multiple users require access to shared resources and external
   network connectivity (not configured in this network).

2. **Role Assignment**:

   - **Computers** (`pc_1` and `pc_2`): Act as client systems for users to perform daily tasks and access shared
     resources on the server.
   - **Server** (`server_1`): Hosts resources such as files and applications needed by client systems.
   - **Switch** (`switch_1`): Serves as the central hub connecting all nodes within the LAN to facilitate internal
     network communications.
   - **Router** (`router_1`): Would provide a gateway to external networks, routing traffic between the LAN and the
     internet or other external networks.

**Configuring Connectivity**

3. **Switch Configuration**: The switch is configured with four ports to accommodate the two computers, the server, and
   a connection to the router. This setup ensures all nodes are interconnected for seamless communication within the LAN.
4. **Router Setup as default Gateway**: The router is set up as the default gateway. It has one port that connects to
   the switch.
5. **Security Settings with ACLs**:

   - The ACL on the router (acl: 10) is configured to permit traffic from the specified internal IP range
     (`192.168.0.0/24`) to access the router’s IP address (`192.168.1.1`). Essentially, this ACL allows the nodes in
     the LAN to communicate with their default gateway (but no further at this stage).

6. **Physical Layout Planning**: Each node is strategically connected to the switch to minimise links and optimise
     network performance. The computers (`pc_1` and `pc_2`) and the server (`server_1`) are each connected to individual
     ports on the switch, maintaining an organised and efficient network topology.


.. code-block:: yaml

  simulation:
    network:
      nodes:
        - hostname: pc_1
          type: computer
          ip_address: 192.168.1.11
          subnet_mask: 255.255.255.0
          default_gateway: 192.168.1.1

        - hostname: pc_2
          type: computer
          ip_address: 192.168.1.12
          subnet_mask: 255.255.255.0
          default_gateway: 192.168.1.1

        - hostname: server_1
          type: server
          ip_address: 192.168.1.13
          subnet_mask: 255.255.255.0
          default_gateway: 192.168.1.1

        - hostname: switch_1
          type: switch
          num_ports: 4

        - hostname: router_1
          type: router
          num_ports: 1
          ports:
            1:
              ip_address: 192.168.1.1
              subnet_mask: 255.255.255.0
          acl:
            10:
              action: PERMIT
              src_ip_address: 192.168.0.0
              src_wildcard_mask: 0.0.0.255
              dst_ip_address: 192.168.1.1

      links:
        - endpoint_a_hostname: pc_1
          endpoint_a_port: 1
          endpoint_b_hostname: switch_1
          endpoint_b_port: 1
        - endpoint_a_hostname: pc_2
          endpoint_a_port: 1
          endpoint_b_hostname: switch_1
          endpoint_b_port: 2
        - endpoint_a_hostname: server_1
          endpoint_a_port: 1
          endpoint_b_hostname: switch_1
          endpoint_b_port: 3
        - endpoint_a_hostname: router_1
          endpoint_a_port: 1
          endpoint_b_hostname: switch_1
          endpoint_b_port: 4


Inspection and Connectivity Test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The following codeblock demonstrates how to access this network and all ``.show()`` to output the network details:

.. code-block:: python

    from primaite.simulator.network.networks import basic_lan_network_example

    network = basic_lan_network_example()

    network.show()

Which gives the output:

.. code-block:: text

    +---------------------------------------+
    |                 Nodes                 |
    +----------+----------+-----------------+
    | Node     | Type     | Operating State |
    +----------+----------+-----------------+
    | router_1 | Router   | ON              |
    | switch_1 | Switch   | ON              |
    | server_1 | Server   | ON              |
    | pc_1     | Computer | ON              |
    | pc_2     | Computer | ON              |
    +----------+----------+-----------------+
    +------------------------------------------------------------------+
    |                           IP Addresses                           |
    +----------+------+--------------+---------------+-----------------+
    | Node     | Port | IP Address   | Subnet Mask   | Default Gateway |
    +----------+------+--------------+---------------+-----------------+
    | router_1 | 1    | 192.168.1.1  | 255.255.255.0 | None            |
    | server_1 | 1    | 192.168.1.13 | 255.255.255.0 | 192.168.1.1     |
    | pc_1     | 1    | 192.168.1.11 | 255.255.255.0 | 192.168.1.1     |
    | pc_2     | 1    | 192.168.1.12 | 255.255.255.0 | 192.168.1.1     |
    +----------+------+--------------+---------------+-----------------+
    +-----------------------------------------------------------------------------------------------------------------------------------------+
    |                                                                  Links                                                                  |
    +------------+----------------------------------------+------------+---------------------------+-------+-------------------+--------------+
    | Endpoint A | A Port                                 | Endpoint B | B Port                    | is Up | Bandwidth (MBits) | Current Load |
    +------------+----------------------------------------+------------+---------------------------+-------+-------------------+--------------+
    | router_1   | Port 1: 63:7e:be:05:fa:72/192.168.1.1  | switch_1   | Port 4: 99:e0:be:79:c4:0a | True  | 100.0             | 0.00000%     |
    | server_1   | Port 1: ee:1d:f5:a1:92:85/192.168.1.13 | switch_1   | Port 3: 6c:17:28:4b:98:b9 | True  | 100.0             | 0.00000%     |
    | pc_2       | Port 1: a3:f2:02:bf:f0:7d/192.168.1.12 | switch_1   | Port 2: c5:3e:f2:c0:da:66 | True  | 100.0             | 0.00000%     |
    | pc_1       | Port 1: 27:db:3f:be:ce:9b/192.168.1.11 | switch_1   | Port 1: d1:ff:2f:be:9d:97 | True  | 100.0             | 0.00000%     |
    +------------+----------------------------------------+------------+---------------------------+-------+-------------------+--------------+

Finally, once the network is configured as expected, a connectivity test should be carried out. This can be done by
"pinging" the default gateway of the server and computers (port 1 on `router_1`). Not only will this test the physical
connections, but the ACL that allows the nodes in the LAN to communicate with their default gateway.

.. code-block:: python

    from primaite.simulator.network.networks import basic_lan_network_example

    network = basic_lan_network_example()

    pc_1 = network.get_node_by_hostname("pc_1")
    pc_1.ping(pc_1.default_gateway)

pc_1.sys_log.show()

If SysLog capture is toggled on and the simulation log level is set to INFO, the `pc_1` the result of the ping should be
captures in the `pc_1` SysLog:

.. code-block:: text

    +-------------------------------------------------------------------------------------------------------------------------------------------------------------+
    |                                                                         pc_1 Sys Log                                                                        |
    +-------------------------+-------+---------------------------------------------------------------------------------------------------------------------------+
    | Timestamp               | Level | Message                                                                                                                   |
    +-------------------------+-------+---------------------------------------------------------------------------------------------------------------------------+
    | 2024-04-24 21:35:09,888 | INFO  | Pinging 192.168.1.1:                                                                                                      |
    | 2024-04-24 21:35:09,889 | INFO  | Sending ARP request from NIC Port 1: 50:fe:d9:ff:a9:4d/192.168.1.11 for ip 192.168.1.1                                    |
    | 2024-04-24 21:35:09,890 | INFO  | Adding ARP cache entry for d2:eb:16:1b:56:0d/192.168.1.1 via NIC Port 1: 50:fe:d9:ff:a9:4d/192.168.1.11                   |
    | 2024-04-24 21:35:09,890 | INFO  | Received ARP response for 192.168.1.1 from d2:eb:16:1b:56:0d via Network Interface Port 1: 50:fe:d9:ff:a9:4d/192.168.1.11 |
    | 2024-04-24 21:35:09,892 | INFO  | Reply from 192.168.1.1: bytes=32, time=1ms, TTL=62                                                                        |
    | 2024-04-24 21:35:09,892 | INFO  | Reply from 192.168.1.1: bytes=32, time=<1ms, TTL=62                                                                       |
    | 2024-04-24 21:35:09,893 | INFO  | Reply from 192.168.1.1: bytes=32, time=<1ms, TTL=62                                                                       |
    | 2024-04-24 21:35:09,894 | INFO  | Reply from 192.168.1.1: bytes=32, time=<1ms, TTL=62                                                                       |
    | 2024-04-24 21:35:09,894 | INFO  | Ping statistics for 192.168.1.1: Packets: Sent = 4, Received = 4, Lost = 0 (0.0% loss)                                    |
    +-------------------------+-------+---------------------------------------------------------------------------------------------------------------------------+

To verify that the ACL on `router_1` worked, we can call `.acl.show()`. This not only shows the ACL rules, but the
number of times each rule has been hit. the code block below is an extension of the above code block that accesses the
`basic_lan_network_example`.

.. code-block:: python

    router_1 = network.get_node_by_hostname("router_1")
    router_1.acl.show()

This gives the output:

.. code-block:: text

    +---------------------------------------------------------------------------------------------------------------------+
    |                                             router_1 Access Control List                                            |
    +-------+--------+----------+-------------+--------------+----------+-------------+--------------+----------+---------+
    | Index | Action | Protocol | Src IP      | Src Wildcard | Src Port | Dst IP      | Dst Wildcard | Dst Port | Matched |
    +-------+--------+----------+-------------+--------------+----------+-------------+--------------+----------+---------+
    | 10    | PERMIT | ANY      | 192.168.1.0 | 0.0.0.255    | ANY      | 192.168.1.1 | 0.0.0.0      | ANY      | 5       |
    | 24    | DENY   | ANY      | ANY         | ANY          | ANY      | ANY         | ANY          | ANY      | 0       |
    +-------+--------+----------+-------------+--------------+----------+-------------+--------------+----------+---------+

#3. Multi-LAN with Internet
---------------------------

This example presents an advanced network configuration that simulates a real-world scenario involving a home or office
network, an Internet Service Provider (ISP), and a comprehensive corporate network for a fictional company named
SomeTech. This extended network includes detailed sub-networks with specialised services, multiple routers featuring
complex routing capabilities, and robust security protocols implemented through Access Control Lists (ACLs). Designed
to mimic the intricacies of actual network environments, this network provides a detailed look at how various network
components interact and function together to support both internal corporate activities and external communications.


.. image:: images/primaite_example_multi_lan_with_internet_network_dark.png
    :align: center
    :class: only-dark

.. image:: images/primaite_example_multi_lan_with_internet_network_light.png
    :align: center
    :class: only-light


Node Configuration
^^^^^^^^^^^^^^^^^^

**Computers and Servers**

- **DNS Server**: Specifies the server that resolves domain names, which is crucial for accessing network services by
  hostname instead of IP addresses. In this scenario, DNS servers play a vital role in connecting with external
  internet services and internal applications.

**Routers & Firewalls**

- **Routes**: Routers also manage specific routes that direct traffic between subnets within the larger network. These routes are defined in the routing table and include:

  - **IP Address**: The IP address of the destination node/subnet.
  - **Subnet Mask**: Defines the size of the destination subnet and differentiates between network address and host identifier.
  - **Next Hop IP Address**: The address of the next hop router or gateway that packets should be sent to when trying
    to reach the destination subnet. This setting is essential for routing decisions in multi-network environments.
- **Default Route**: This is a crucial setting in complex network environments where multiple routers are used. It
  directs outbound traffic to a specified gateway, typically used for accessing the Internet or connecting to upstream
  networks.

**Firewalls**

- **Ports Configuration**: Similar to routers but with named ports to differentiate between external (internet-facing),
  internal, and demilitarized zone (DMZ) connections.