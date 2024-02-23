.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

NTPServer
=========
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
- Service runs on UDP port 123 by default.

Implementation
^^^^^^^^^^^^^^

- NTP request and responses use a ``NTPPacket`` object
- Extends Service class for integration with ``SoftwareManager``.
