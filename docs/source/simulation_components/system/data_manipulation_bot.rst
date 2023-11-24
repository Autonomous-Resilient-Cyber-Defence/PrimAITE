.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


DataManipulationBot
===================

The ``DataManipulationBot`` class provides functionality to connect to a ``DatabaseService`` and execute malicious SQL statements.

The bot is controlled by a ``DataManipulationAgent``.

Overview
--------

The bot is intended to simulate a malicious actor carrying out attacks like:

- Dropping tables
- Deleting records
- Modifying data

On a database server by abusing an application's trusted database connectivity.

The bot performs attacks in the following stages to simulate the real pattern of an attack:

- Logon - *The bot gains access to the node.*
- Port Scan - *The bot finds accessible database servers on the network.*
- Attacking - *The bot delivers the payload to the discovered database servers.*

Each of these stages has a random, configurable probability of succeeding. The bot can also be configured to repeat the attack once complete.

Usage
-----

- Create an instance and call ``configure`` to set:
    - Target database server IP
    - Database password (if needed)
    - SQL statement payload
    - Probabilities for succeeding each of the above attack stages
- Call ``run`` to connect and execute the statement.

The bot handles connecting, executing the statement, and disconnecting.

Example
-------

.. code-block:: python

    client_1 = Computer(
        hostname="client_1", ip_address="192.168.10.21", subnet_mask="255.255.255.0", default_gateway="192.168.10.1"
    )
    client_1.power_on()
    network.connect(endpoint_b=client_1.ethernet_port[1], endpoint_a=switch_2.switch_ports[1])
    client_1.software_manager.install(DataManipulationBot)
    data_manipulation_bot: DataManipulationBot = client_1.software_manager.software["DataManipulationBot"]
    data_manipulation_bot.configure(server_ip_address=IPv4Address("192.168.1.14"), payload="DROP TABLE IF EXISTS user;")
    data_manipulation_bot.run()

This would connect to the database service at 192.168.1.14, authenticate, and execute the SQL statement to drop the 'users' table.

Implementation
--------------

The bot extends ``DatabaseClient`` and leverages its connectivity.

- Uses the Application base class for lifecycle management.
- Credentials, target IP and other options set via ``configure``.
- ``run`` handles connecting, executing statement, and disconnecting.
- SQL payload executed via ``query`` method.
- Results in malicious SQL being executed on remote database server.
