.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

NTPClient
=========

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
