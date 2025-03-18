.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _DatabaseClient:

DatabaseClient
##############

The ``DatabaseClient`` provides a client interface for connecting to the :ref:`DatabaseService`.

Key features
============

- Connects to the :ref:`DatabaseService` via the ``SoftwareManager``.
- Handles connecting and disconnecting.
- Handles multiple connections using a dictionary, mapped to connection UIDs
- Executes SQL queries and retrieves result sets.

Usage
=====

- Initialise with server IP address and optional password.
- Connect to the :ref:`DatabaseService` with ``get_new_connection``.
- Retrieve results in a dictionary.
- Disconnect when finished.

Implementation
==============

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Active sessions are held as ``DatabaseClientConnection`` objects in a dictionary.
- Connect and disconnect methods manage sessions.
- Payloads serialised as dictionaries for transmission.
- Extends base Application class.

Examples
========

Python
""""""

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.applications.database_client import DatabaseClient

    client_1 = Computer(config={
        "hostname":"client_1",
        "ip_address":"192.168.10.21",
        "subnet_mask":"255.255.255.0",
        "default_gateway":"192.168.10.1",
        "operating_state":NodeOperatingState.ON # initialise the computer in an ON state
        }
    )

    # install DatabaseClient
    client.software_manager.install(DatabaseClient)

    database_client: DatabaseClient = client.software_manager.software.get("database-client")

    # Configure the DatabaseClient
    database_client.configure(server_ip_address=IPv4Address("192.168.0.1"))  # address of the DatabaseService
    database_client.run()

    # Establish a new connection
    database_client.get_new_connection()


Via Configuration
"""""""""""""""""

.. code-block:: yaml

    simulation:
      network:
        nodes:
        - hostname: example_computer
        type: computer
        ...
        applications:
        - type: database-client
        options:
          db_server_ip: 192.168.0.1

Configuration
=============


``db_server_ip``
""""""""""""""""

IP address of the :ref:`DatabaseService` that the ``DatabaseClient`` will connect to

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``server_password``
"""""""""""""""""""

Optional. Default value is ``None``.

The password that the ``DatabaseClient`` will use to access the :ref:`DatabaseService`.

``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
