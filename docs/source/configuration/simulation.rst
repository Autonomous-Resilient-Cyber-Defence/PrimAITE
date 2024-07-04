.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK


``simulation``
==============
In this section the network layout is defined. This part of the config follows a hierarchical structure. Almost every component defines a ``ref`` field which acts as a human-readable unique identifier, used by other parts of the config, such as agents.

At the top level of the network are ``nodes``, ``links`` and ``airspace``.

e.g.

.. code-block:: yaml

    simulation:
        network:
            nodes:
            ...
            links:
            ...
            airspace:
            ...


``nodes``
---------

This is where the list of nodes are defined. Some items will differ according to the node type, however, there will be common items such as a node's reference (which is used by the agent), the node's ``type`` and ``hostname``

To see the configuration for these nodes, refer to the following:

.. toctree::
    :maxdepth: 1
    :glob:

    simulation/nodes/computer
    simulation/nodes/firewall
    simulation/nodes/router
    simulation/nodes/server
    simulation/nodes/switch
    simulation/nodes/wireless_router
    simulation/nodes/network_examples

``links``
---------

This is where the links between the nodes are formed.

e.g.

In order to recreate the network below, we will need to create 2 links:

- a link from computer_1 to the switch
- a link from computer_2 to the switch

.. image:: ../../_static/switched_p2p_network.png
    :width: 500
    :align: center

this results in:

.. code-block:: yaml

    links:
        - endpoint_a_hostname: computer_1
        endpoint_a_port: 1 # port 1 on computer_1
        endpoint_b_hostname: switch
        endpoint_b_port: 1 # port 1 on switch
        bandwidth: 100
        - endpoint_a_hostname: computer_2
        endpoint_a_port: 1 # port 1 on computer_2
        endpoint_b_hostname: switch
        endpoint_b_port: 2 # port 2 on switch
        bandwidth: 100

``ref``
^^^^^^^

The human readable name for the link. Not used in code, however is useful for a human to understand what the link is for.

``endpoint_a_hostname``
^^^^^^^^^^^^^^^^^^^^^^^

The ``hostname`` of the node which must be connected.

``endpoint_a_port``
^^^^^^^^^^^^^^^^^^^

The port on ``endpoint_a_hostname`` which is to be connected to ``endpoint_b_port``.
This accepts an integer value e.g. if port 1 is to be connected, the configuration should be ``endpoint_a_port: 1``

``endpoint_b_hostname``
^^^^^^^^^^^^^^^^^^^^^^^

The ``hostname`` of the node which must be connected.

``endpoint_b_port``
^^^^^^^^^^^^^^^^^^^

The port on ``endpoint_b_hostname`` which is to be connected to ``endpoint_a_port``.
This accepts an integer value e.g. if port 1 is to be connected, the configuration should be ``endpoint_b_port: 1``

``bandwidth``

This is an integer value specifying the allowed bandwidth across the connection. Units are in Mbps.

``airspace``
------------

This section configures settings specific to the wireless network's virtual airspace. It defines how wireless interfaces within the simulation will interact and perform under various environmental conditions.

``airspace_environment_type``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This setting specifies the environmental conditions of the airspace which affect the propagation and interference characteristics of wireless signals. Changing this environment type impacts how signal noise and interference are calculated, thus affecting the overall network performance, including data transmission rates and signal quality.

**Configurable Options**

- **rural**: A rural environment offers clear channel conditions due to low population density and minimal electronic device presence.

- **outdoor**: Outdoor environments like parks or fields have minimal electronic interference.

- **suburban**: Suburban environments strike a balance with fewer electronic interferences than urban but more than rural.

- **office**: Office environments have moderate interference from numerous electronic devices and overlapping networks.

- **urban**: Urban environments are characterized by tall buildings and a high density of electronic devices, leading to significant interference.

- **industrial**: Industrial areas face high interference from heavy machinery and numerous electronic devices.

- **transport**: Environments such as subways and buses where metal structures and high mobility create complex interference patterns.

- **dense_urban**: Dense urban areas like city centers have the highest level of signal interference due to the very high density of buildings and devices.

- **jamming_zone**: A jamming zone environment where signals are actively interfered with, typically through the use of signal jammers or scrambling devices. This represents the environment with the highest level of interference.

- **blocked**: A jamming zone environment with total levels of interference. Airspace is completely blocked.
