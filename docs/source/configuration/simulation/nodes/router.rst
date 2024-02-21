.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _router_configuration:

``router``
==========

A basic representation of a network router within the simulation.

See :py:mod:`primaite.simulator.network.hardware.nodes.network.router.Router`

example router
--------------

.. code-block:: yaml

    nodes:
        - ref: router_1
        hostname: router_1
        type: router
        num_ports: 5
        ports:
            ...
        acl:
            ...

.. include:: common/common_node_attributes.rst

.. include:: common/node_type_list.rst

``num_ports``
-------------

Optional. Default value is ``5``.

The number of ports the router will have.

``ports``
---------

Sets up the router's ports with an IP address and a subnet mask.

Example of setting ports for a router with 2 ports:

.. code-block:: yaml

    nodes:
        - ref: router_1
        ...
        ports:
            1:
                ip_address: 192.168.1.1
                subnet_mask: 255.255.255.0
            2:
                ip_address: 192.168.10.1
                subnet_mask: 255.255.255.0

``ip_address``
""""""""""""""

The IP address for the given port. This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``subnet_mask``
"""""""""""""""

Optional. Default value is ``255.255.255.0``.

The subnet mask setting for the port.

``acl``
-------

Sets up the ACL rules for the router.

e.g.

.. code-block:: yaml

    nodes:
        - ref: router_1
        ...
        acl:
            1:
                action: PERMIT
                src_port: ARP
                dst_port: ARP
            2:
                action: PERMIT
                protocol: ICMP

See :py:mod:`primaite.simulator.network.hardware.nodes.network.router.AccessControlList`

See :ref:`List of Ports <List of Ports>` for a list of ports.

``action``
""""""""""

Available options are

- ``PERMIT`` : Allows the specified ``protocol`` or ``src_port`` and ``dst_port`` pairs
- ``DENY`` : Blocks the specified ``protocol`` or ``src_port`` and ``dst_port`` pairs

``src_port``
""""""""""""

Is used alongside ``dst_port``. Specifies the port where a packet originates. Used by the ACL Rule to determine if a packet with a specific source port is allowed to pass through the network node.

``dst_port``
""""""""""""

Is used alongside ``src_port``. Specifies the port where a packet is destined to arrive. Used by the ACL Rule to determine if a packet with a specific destination port is allowed to pass through the network node.

``protocol``
""""""""""""

Specifies which protocols are allowed by the ACL Rule to pass through the network node.

See :ref:`List of IPProtocols <List of IPProtocols>` for a list of protocols.

.. include:: common/common_network_node_attributes.rst

.. |NODE| replace:: router
.. |NODE_TYPE| replace:: ``router``
