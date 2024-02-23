.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

FTPServer
=========
Provides a FTP Client-Server simulation by extending the base Service class.

Key capabilities
^^^^^^^^^^^^^^^^

- Simulates FTP requests and FTPPacket transfer across a network
- Allows the emulation of FTP commands between an FTP client and server:
    - STOR: stores a file from client to server
    - RETR: retrieves a file from the FTP server
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
^^^^^
- Install on a Node via the ``SoftwareManager`` to start the FTP server service.
- Service runs on FTP (command) port 21 by default. (TODO: look at in depth implementation of FTP PORT command)

Implementation
^^^^^^^^^^^^^^

- FTP request and responses use a ``FTPPacket`` object
- Extends Service class for integration with ``SoftwareManager``.
