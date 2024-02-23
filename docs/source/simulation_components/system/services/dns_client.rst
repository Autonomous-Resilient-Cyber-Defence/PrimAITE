.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

DNSClient
=========

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
- Execute domain name checks with ``check_domain_exists``.
- ``DNSClient`` will automatically add the IP Address of the domain into its cache

Implementation
^^^^^^^^^^^^^^

- Leverages ``SoftwareManager`` for sending payloads over the network.
- Provides easy interface for Nodes to find IP addresses via domain names.
- Extends base Service class.
