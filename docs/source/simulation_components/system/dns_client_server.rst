.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

DNS Client Server
======================

DNS Server
----------------
Also known as a DNS Resolver, the ``DNSServer`` provides a DNS Server simulation by extending the base Service class.

Key capabilities
^^^^^^^^^^^^^^^^

- Simulates DNS requests and DNSPacket transfer across a network
- Registers domain names and the IP Address linked to the domain name
- Returns the IP address for a given domain name within a DNS Packet that a DNS Client can read
- Leverages the Service base class for install/uninstall, status tracking, etc.

Usage
^^^^^
- Install on a Node via the ``SoftwareManager`` to start the database service.
- Service runs on TCP port 53 by default. (TODO: TCP for now, should be UDP in future)

Implementation
^^^^^^^^^^^^^^

- DNS request and responses use a ``DNSPacket`` object
- Extends Service class for integration with ``SoftwareManager``.

DNS Client
---------------

The DNSClient provides a client interface for connecting to the ``DNSServer``.

Key features
^^^^^^^^^^^^

- Connects to the ``DNSServer`` via the ``SoftwareManager``.
- Executes DNS lookup requests and keeps a cache of known domain name IP addresses.
- Handles connection to DNSServer and querying for domain name IP addresses.

Usage
^^^^^

- Install on a Node via the ``SoftwareManager`` to start the database service.
- Service runs on TCP port 53 by default. (TODO: TCP for now, should be UDP in future)
- Execute domain name checks with ``check_domain_exists``, providing a ``DNSServer`` ``IPv4Address``.
- ``DNSClient`` will automatically add the IP Address of the domain into its cache

Implementation
^^^^^^^^^^^^^^

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Provides easy interface for Nodes to find IP addresses via domain names.
- Extends base Service class.
