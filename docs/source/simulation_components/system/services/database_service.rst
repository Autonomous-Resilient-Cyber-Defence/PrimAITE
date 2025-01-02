.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _DatabaseService:

DatabaseService
###############

The ``DatabaseService`` provides a SQL database server simulation by extending the base Service class.

Key capabilities
================

- Creates a database file in the ``FileSystem`` of the ``Node`` (which the ``DatabaseService`` is installed on) upon creation.
- Handles connecting clients by maintaining a dictionary of connections mapped to session IDs.
- Authenticates connections using a configurable password.
- Simulates ``SELECT``, ``DELETE`` and ``INSERT`` SQL queries.
- Returns query results and status codes back to clients.
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
=====
- Install on a Node via the ``SoftwareManager`` to start the database service.
- Clients connect, execute queries, and disconnect.
- Service runs on TCP port 5432 by default.

**Supported queries:**

* ``SELECT``: As long as the database file is in a ``GOOD`` health state, the db service will respond with a 200 status code.
* ``DELETE``: This query represents an attack, it will cause the database file to enter a ``COMPROMISED`` state, and return a status code 200.
* ``INSERT``: If the database service is in a healthy state, this will return a 200 status, if it's not in a healthy state it will return 404.
* ``SELECT * FROM pg_stat_activity``: This query represents something an admin would send to check the status of the database. If the database service is in a healthy state, it returns a 200 status code, otherwise a 401 status code.

Implementation
==============

- Creates the database file within the node's file system.
- Manages client connections in a dictionary by session ID.
- Processes SQL queries.
- Returns results and status codes in a standard dictionary format.
- Extends Service class for integration with ``SoftwareManager``.

Examples
========

Python
""""""

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.hardware.nodes.host.server import Server
    from primaite.simulator.system.services.database.database_service import DatabaseService

    # Create Server
    server = Server(
        hostname="server",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    # Install DatabaseService on server
    server.software_manager.install(DatabaseService)
    db_service: DatabaseService = server.software_manager.software.get("DatabaseService")
    db_service.start()

    # configure DatabaseService
    db_service.configure_backup(IPv4Address("192.168.0.10"))


Via Configuration
"""""""""""""""""

.. code-block:: yaml

    simulation:
        network:
            nodes:
                - ref: example_server
                hostname: example_server
                type: server
                ...
                services:
                    - ref: database_service
                    type: DatabaseService
                    options:
                        backup_server_ip: 192.168.0.10

Configuration
=============

``backup_server_ip``
""""""""""""""""""""

Optional. Default value is ``None``.

The IP Address of the backup server that the ``DatabaseService`` will use to create backups of the database.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``password``
""""""""""""

Optional. Default value is ``None``.

The password that needs to be provided by connecting clients in order to create a successful connection.

``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
