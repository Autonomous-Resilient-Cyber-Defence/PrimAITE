.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _switch_configuration:

``switch``
==========

A basic representation of a network switch within the simulation.

See :py:mod:`primaite.simulator.network.hardware.nodes.network.switch.Switch`

example switch
--------------

.. code-block:: yaml

    simulation:
      network:
        nodes:
          hostname: switch_1
          type: switch
          num_ports: 8

.. include:: common/common_node_attributes.rst

.. include:: common/node_type_list.rst

``num_ports``
-------------

Optional. Default value is ``8``.

The number of ports the switch will have.

.. |NODE| replace:: switch
.. |NODE_TYPE| replace:: ``switch``
