.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

WebServer
=========
Provides a Web Server simulation by extending the base Service class.

Key capabilities
^^^^^^^^^^^^^^^^

- Simulates a web server with the capability to also request data from a database
- Allows the emulation of HTTP requests between client (e.g. a web browser) and server
    - GET request sends a get all users request to the database server and returns an HTTP 200 status if the database is responsive
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
^^^^^
- Install on a Node via the ``SoftwareManager`` to start the `WebServer`.
- Service runs on HTTP port 80 by default. (TODO: HTTPS)

Implementation
^^^^^^^^^^^^^^

- HTTP request uses a ``HttpRequestPacket`` object
- HTTP response uses a ``HttpResponsePacket`` object
- Extends Service class for integration with ``SoftwareManager``.
