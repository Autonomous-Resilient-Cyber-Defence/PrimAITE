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

.. image:: images/primaite_node_type_colour_key.png
    :width: 300
    :align: center

#1. Client-Server P2P Network
-----------------------------

This example demonstrates how to create a minimal two-node client-server P2P network. the network consists of a Computer
and a Server on the same subnet with a single Link connecting the two.


.. image:: images/primaite_example_client_server_p2p_network.png
    :width: 800
    :align: center

The yaml file contains two nodes in the ``simulation.network.nodes`` array, one with the `pc_1` reference and another
with the `server_1` reference. both nodes are given a node type, `pc_1` being a `computer` and `server_1` being a
`server`. Both nodes are then given an ip address and subnet mask.

The link between the two nodes is configured in the ``simulation.network.links`` array, with the hostname and network
interface for each being configured under ``endpoint_<a or b>_hostname`` and ``endpoint_<a or b>_port`` respectively.



.. code-block:: yaml
  :linenos:
  :emphasive-lines:

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

#2. Basic Switched Network
--------------------------

In this example we'll create a basic switched network. The network will consist of two Computers, a Server, and a
Switch, all on the same subnet.
