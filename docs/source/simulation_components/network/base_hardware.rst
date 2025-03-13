.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

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

.. _node_description:

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

    node = Node(config={"hostname":"pc_a"})

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

    node = Node(config={"hostname":"pc_a", "operating_state":NodeOperatingState.ON})

    assert node.operating_state is NodeOperatingState.ON  # node is in ON state

Setting ``start_up_duration`` and/or ``shut_down_duration`` to ``0`` will allow for the ``power_on`` and ``power_off`` methods to be completed instantly without applying timesteps:

.. code-block:: python

    from primaite.simulator.network.hardware.base import Node
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState

    node = Node(config={"hostname":"pc_a", "start_up_duration":0, "shut_down_duration":0})

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
  Applications, taking into account the ``start_up_duration``.
- **power_off()**: Stops the node's operations, adhering to the ``shut_down_duration``.
- **ping()**: Sends ICMP echo requests to a specified IP address to test connectivity.
- **has_enabled_network_interface()**: Checks if the node has any network interfaces enabled, facilitating network
  communication.
- **show()**: Provides a summary of the node's current state, including network interfaces, operational status, and
  other key attributes.


The Node class handles installation of system software, network connectivity, frame processing, system logging, and
power states. It establishes baseline functionality while allowing subclassing to model specific node types like hosts,
routers, firewalls etc. The flexible architecture enables composing complex network topologies.

User, UserManager, and UserSessionManager
=========================================

The ``base.py`` module also includes essential classes for managing users and their sessions within the PrimAITE
simulation. These are the ``User``, ``UserManager``, and ``UserSessionManager`` classes. The base ``Node`` class comes
with ``UserManager``, and ``UserSessionManager`` classes pre-installed.

User Class
----------

The ``User`` class represents a user in the system. It includes attributes such as ``username``, ``password``,
``disabled``, and ``is_admin`` to define the user's credentials and status.

Example Usage
^^^^^^^^^^^^^

Creating a user:
    .. code-block:: python

        user = User(username="john_doe", password="12345")

UserManager Class
-----------------

The ``UserManager`` class handles user management tasks such as creating users, authenticating them, changing passwords,
and enabling or disabling user accounts. It maintains a dictionary of users and provides methods to manage them
effectively.

Example Usage
^^^^^^^^^^^^^

Creating a ``UserManager`` instance and adding a user:
    .. code-block:: python

        user_manager = UserManager()
        user_manager.add_user(username="john_doe", password="12345")

Authenticating a user:
    .. code-block:: python

        user = user_manager.authenticate_user(username="john_doe", password="12345")

UserSessionManager Class
------------------------

The ``UserSessionManager`` class manages user sessions, including local and remote sessions. It handles session creation,
timeouts, and provides methods for logging users in and out.

Example Usage
^^^^^^^^^^^^^

Creating a ``UserSessionManager`` instance and logging a user in locally:
    .. code-block:: python

        session_manager = UserSessionManager()
        session_id = session_manager.local_login(username="john_doe", password="12345")

Logging a user out:
    .. code-block:: python

        session_manager.local_logout()

Practical Examples
------------------

Below are unit tests which act as practical examples illustrating how to use the ``User``, ``UserManager``, and
``UserSessionManager`` classes within the context of a client-server network simulation.

Setting up a Client-Server Network
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from typing import Tuple
    from uuid import uuid4

    import pytest

    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.network.hardware.nodes.host.server import Server

    @pytest.fixture(scope="function")
    def client_server_network() -> Tuple[Computer, Server, Network]:
        network = Network()

        client = Computer(config={
            "hostname":"client",
            "ip_address":"192.168.1.2",
            "subnet_mask":"255.255.255.0",
            "default_gateway":"192.168.1.1",
            "start_up_duration":0,
            }
        )
        client.power_on()

        server = Server(config = {
            "hostname":"server",
            "ip_address":"192.168.1.3",
            "subnet_mask":"255.255.255.0",
            "default_gateway":"192.168.1.1",
            "start_up_duration":0,
            }
        )
        server.power_on()

        network.connect(client.network_interface[1], server.network_interface[1])

        return client, server, network

Local Login Success
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def test_local_login_success(client_server_network):
        client, server, network = client_server_network

        assert not client.user_session_manager.local_user_logged_in

        client.user_session_manager.local_login(username="admin", password="admin")

        assert client.user_session_manager.local_user_logged_in

Local Login Failure
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def test_local_login_failure(client_server_network):
        client, server, network = client_server_network

        assert not client.user_session_manager.local_user_logged_in

        client.user_session_manager.local_login(username="jane.doe", password="12345")

        assert not client.user_session_manager.local_user_logged_in

Adding a New User and Successful Local Login
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def test_new_user_local_login_success(client_server_network):
        client, server, network = client_server_network

        assert not client.user_session_manager.local_user_logged_in

        client.user_manager.add_user(username="jane.doe", password="12345")

        client.user_session_manager.local_login(username="jane.doe", password="12345")

        assert client.user_session_manager.local_user_logged_in

Clearing Previous Login on New Local Login
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def test_new_local_login_clears_previous_login(client_server_network):
        client, server, network = client_server_network

        assert not client.user_session_manager.local_user_logged_in

        current_session_id = client.user_session_manager.local_login(username="admin", password="admin")

        assert client.user_session_manager.local_user_logged_in

        assert client.user_session_manager.local_session.user.username == "admin"

        client.user_manager.add_user(username="jane.doe", password="12345")

        new_session_id = client.user_session_manager.local_login(username="jane.doe", password="12345")

        assert client.user_session_manager.local_user_logged_in

        assert client.user_session_manager.local_session.user.username == "jane.doe"

        assert new_session_id != current_session_id

Persistent Login for the Same User
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def test_new_local_login_attempt_same_uses_persists(client_server_network):
        client, server, network = client_server_network

        assert not client.user_session_manager.local_user_logged_in

        current_session_id = client.user_session_manager.local_login(username="admin", password="admin")

        assert client.user_session_manager.local_user_logged_in

        assert client.user_session_manager.local_session.user.username == "admin"

        new_session_id = client.user_session_manager.local_login(username="admin", password="admin")

        assert client.user_session_manager.local_user_logged_in

        assert client.user_session_manager.local_session.user.username == "admin"

        assert new_session_id == current_session_id
