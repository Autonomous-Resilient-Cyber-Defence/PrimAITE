.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


Database Client Server
======================

Database Service
----------------

The ``DatabaseService`` provides a SQL database server simulation by extending the base Service class.

Key capabilities
^^^^^^^^^^^^^^^^

- Creates a database file in the ``Node`` 's ``FileSystem`` upon creation.
- Handles connecting clients by maintaining a dictionary of connections mapped to session IDs.
- Authenticates connections using a configurable password.
- Simulates ``SELECT``, ``DELETE`` and ``INSERT`` SQL queries.
- Returns query results and status codes back to clients.
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
^^^^^
- Install on a Node via the ``SoftwareManager`` to start the database service.
- Clients connect, execute queries, and disconnect.
- Service runs on TCP port 5432 by default.

Implementation
^^^^^^^^^^^^^^

- Creates the database file within the node's file system.
- Manages client connections in a dictionary by session ID.
- Processes SQL queries.
- Returns results and status codes in a standard dictionary format.
- Extends Service class for integration with ``SoftwareManager``.

Database Client
---------------

The DatabaseClient provides a client interface for connecting to the ``DatabaseService``.

Key features
^^^^^^^^^^^^

- Connects to the ``DatabaseService`` via the ``SoftwareManager``.
- Handles connecting and disconnecting.
- Executes SQL queries and retrieves result sets.

Usage
^^^^^

- Initialise with server IP address and optional password.
- Connect to the ``DatabaseService`` with ``connect``.
- Retrieve results in a dictionary.
- Disconnect when finished.

To create database backups:

- Configure the backup server on the ``DatabaseService`` by providing the Backup server ``IPv4Address`` with ``configure_backup``
- Create a backup using ``backup_database``. This fails if the backup server is not configured.
- Restore a backup using ``restore_backup``. By default, this uses the database created via ``backup_database``.

Implementation
^^^^^^^^^^^^^^

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Connect and disconnect methods manage sessions.
- Payloads serialised as dictionaries for transmission.
- Extends base Application class.
