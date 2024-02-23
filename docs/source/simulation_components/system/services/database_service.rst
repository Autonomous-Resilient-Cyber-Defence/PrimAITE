.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

DatabaseService
===============

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
