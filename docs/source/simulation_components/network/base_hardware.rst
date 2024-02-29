.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

#############
Base Hardware
#############

The ``base.py`` module in ``primaite.simulator.network.hardware`` provides foundational components, interfaces, and classes for
modeling network hardware within PrimAITE simulations. It establishes core building blocks and abstractions that more
complex, specialized hardware components inherit from and build upon.

The key elements defined in ``base.py`` are:

``NetworkInterface``
====================

- Abstract base class for network interfaces like NICs. Defines common attributes like MAC address, speed, MTU.
- Requires subclasses to implement ``enable()``, ``disable()``, ``send_frame()`` and ``receive_frame()``.
- Provides basic state description and request handling capabilities.

``Node``
========
The Node class stands as a central component in ``base.py``, acting as the superclass for all network nodes within a
PrimAITE simulation.

Node Attributes
---------------

See :ref:`Node Attributes`

.. _Node Start up and Shut down:

Node Start up and Shut down
---------------------------
Nodes are powered on and off over multiple timesteps. By default, the node ``start_up_duration`` and ``shut_down_duration`` is 3 timesteps.

Example code where a node is turned on:

.. code-block:: python

    from primaite.simulator.network.hardware.base import Node
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState

    node = Node(hostname="pc_a")

    assert node.operating_state is NodeOperatingState.OFF # By default, node is instantiated in an OFF state

    node.power_on() # power on the node

    assert node.operating_state is NodeOperatingState.BOOTING # node is booting up

    for i in range(node.start_up_duration + 1):
        # apply timestep until the node start up duration
        node.apply_timestep(timestep=i)

    assert node.operating_state is NodeOperatingState.ON # node is in ON state


If the node needs to be instantiated in an on state:


.. code-block:: python

    from primaite.simulator.network.hardware.base import Node
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState

    node = Node(hostname="pc_a", operating_state=NodeOperatingState.ON)

    assert node.operating_state is NodeOperatingState.ON  # node is in ON state

Setting ``start_up_duration`` and/or ``shut_down_duration`` to ``0`` will allow for the ``power_on`` and ``power_off`` methods to be completed instantly without applying timesteps:

.. code-block:: python

    from primaite.simulator.network.hardware.base import Node
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState

    node = Node(hostname="pc_a", start_up_duration=0, shut_down_duration=0)

    assert node.operating_state is NodeOperatingState.OFF  # node is in OFF state

    node.power_on()

    assert node.operating_state is NodeOperatingState.ON  # node is in ON state

    node.power_off()

    assert node.operating_state is NodeOperatingState.OFF  # node is in OFF state

Node Behaviours/Functions
-------------------------


- **connect_nic()**: Connects a ``NetworkInterface`` to the node for network communication.
- **disconnect_nic()**: Removes a ``NetworkInterface`` from the node.
- **receive_frame()**: Handles the processing of incoming network frames.
- **apply_timestep()**: Advances the state of the node according to the simulation timestep.
- **power_on()**: Initiates the node, enabling all connected Network Interfaces and starting all Services and
  Applications, taking into account the `start_up_duration`.
- **power_off()**: Stops the node's operations, adhering to the `shut_down_duration`.
- **ping()**: Sends ICMP echo requests to a specified IP address to test connectivity.
- **has_enabled_network_interface()**: Checks if the node has any network interfaces enabled, facilitating network
  communication.
- **show()**: Provides a summary of the node's current state, including network interfaces, operational status, and
  other key attributes.


The Node class handles installation of system software, network connectivity, frame processing, system logging, and
power states. It establishes baseline functionality while allowing subclassing to model specific node types like hosts,
routers, firewalls etc. The flexible architecture enables composing complex network topologies.
