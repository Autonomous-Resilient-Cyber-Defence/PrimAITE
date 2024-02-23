.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


DatabaseClient
===============

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
