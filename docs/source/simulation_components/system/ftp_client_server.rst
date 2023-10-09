.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

FTP Client Server
=================

FTP Server
----------
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

FTP Client
----------

The ``FTPClient`` provides a client interface for connecting to the ``FTPServer``.

Key features
^^^^^^^^^^^^

- Connects to the ``FTPServer`` via the ``SoftwareManager``.
- Simulates FTP requests and FTPPacket transfer across a network
- Allows the emulation of FTP commands between an FTP client and server:
    - PORT: specifies the port that server should connect to on the client (currently only uses ``Port.FTP``)
    - STOR: stores a file from client to server
    - RETR: retrieves a file from the FTP server
    - QUIT: disconnect from server
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
^^^^^

- Install on a Node via the ``SoftwareManager`` to start the FTP client service.
- Service runs on FTP (command) port 21 by default. (TODO: look at in depth implementation of FTP PORT command)
- Execute sending a file to the FTP server with ``send_file``
- Execute retrieving a file from the FTP server with ``request_file``

Implementation
^^^^^^^^^^^^^^

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Provides easy interface for Nodes to transfer files between each other.
- Extends base Service class.


Example Usage
----------

Dependencies
^^^^^^^^^^^^

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.nodes.computer import Computer
    from primaite.simulator.network.hardware.nodes.server import Server
    from primaite.simulator.system.services.ftp.ftp_server import FTPServer
    from primaite.simulator.system.services.ftp.ftp_client import FTPClient

Example peer to peer network
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    net = Network()

    pc1 = Computer(hostname="pc1", ip_address="120.10.10.10", subnet_mask="255.255.255.0")
    srv = Server(hostname="srv", ip_address="120.10.10.20", subnet_mask="255.255.255.0")
    pc1.power_on()
    srv.power_on()
    net.connect(pc1.ethernet_port[1], srv.ethernet_port[1])

Install the FTP Server
^^^^^^^^^^^^^^^^^^^^^^

FTP Client should be pre installed on nodes

.. code-block:: python

    srv.software_manager.install(FTPServer)
    ftpserv: FTPServer = srv.software_manager.software['FTPServer']

Setting up the FTP Server
^^^^^^^^^^^^^^^^^^^^^^^^^

Set up the FTP Server with a file that the client will need to retrieve

.. code-block:: python

    srv.file_system.create_file('my_file.png')

Check that file was retrieved
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client.request_file(
        src_folder_name='root',
        src_file_name='my_file.png',
        dest_folder_name='root',
        dest_file_name='test.png',
        dest_ip_address=IPv4Address("120.10.10.20")
    )

    print(client.get_file(folder_name="root", file_name="test.png"))
