.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _computer_configuration:

``computer``
============

A basic representation of a computer within the simulation.

See :py:mod:`primaite.simulator.network.hardware.nodes.host.computer.Computer`

example computer
----------------

.. code-block:: yaml

    nodes:
        - ref: client_1
        hostname: client_1
        type: computer
        ip_address: 192.168.0.10
        subnet_mask: 255.255.255.0
        default_gateway: 192.168.0.1
        dns_server: 192.168.1.10
        applications:
            ...
        services:
            ...

.. include:: common/common_node_attributes.rst

.. include:: common/node_type_list.rst

.. include:: common/common_host_node_attributes.rst

.. |NODE| replace:: computer
.. |NODE_TYPE| replace:: ``computer``
