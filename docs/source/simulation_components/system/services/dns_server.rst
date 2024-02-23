.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

DNSServer
=========
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
