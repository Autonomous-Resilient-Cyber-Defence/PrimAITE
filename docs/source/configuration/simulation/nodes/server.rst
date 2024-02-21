.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _server_configuration:

``server``
==========

A basic representation of a server within the simulation.

See :py:mod:`primaite.simulator.network.hardware.nodes.host.server.Server`

example server
--------------

.. code-block:: yaml

    nodes:
        - ref: server_1
        hostname: server_1
        type: server
        ip_address: 192.168.10.10
        subnet_mask: 255.255.255.0
        default_gateway: 192.168.10.1
        dns_server: 192.168.1.10
        applications:
            ...
        services:
            ...

.. include:: common/common_node_attributes.rst

.. include:: common/node_type_list.rst

.. include:: common/common_host_node_attributes.rst

.. |NODE| replace:: server
.. |NODE_TYPE| replace:: ``server``
