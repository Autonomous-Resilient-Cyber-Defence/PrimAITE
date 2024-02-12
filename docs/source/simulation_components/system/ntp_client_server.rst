.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

NTP Client Server
=================

NTP Server
----------
The ``NTPServer`` provides a NTP Server simulation by extending the base Service class.

NTP Client
----------
The ``NTPClient`` provides a NTP Client simulation by extending the base Service class.

Key capabilities
^^^^^^^^^^^^^^^^

- Simulates NTP requests and NTPPacket transfer across a network
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
^^^^^
- Install on a Node via the ``SoftwareManager`` to start the database service.
- Service runs on TCP port 123 by default.

Implementation
^^^^^^^^^^^^^^

- NTP request and responses use a ``NTPPacket`` object
- Extends Service class for integration with ``SoftwareManager``.

NTP Client
----------

The NTPClient provides a client interface for connecting to the ``NTPServer``.

Key features
^^^^^^^^^^^^

- Connects to the ``NTPServer`` via the ``SoftwareManager``.

Usage
^^^^^

- Install on a Node via the ``SoftwareManager`` to start the database service.
- Service runs on UDP port 123 by default.

Implementation
^^^^^^^^^^^^^^

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Provides easy interface for Nodes to find IP addresses via domain names.
- Extends base Service class.
