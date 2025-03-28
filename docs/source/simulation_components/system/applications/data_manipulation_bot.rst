.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _DataManipulationBot:

DataManipulationBot
###################

The ``DataManipulationBot`` class provides functionality to connect to a :ref:`DatabaseService` and execute malicious SQL statements.

Overview
========

The bot is intended to simulate a malicious actor carrying out attacks like:

- Dropping tables
- Deleting records
- Modifying data

on a database server by abusing an application's trusted database connectivity.

The bot performs attacks in the following stages to simulate the real pattern of an attack:

- Logon - *The bot gains credentials and accesses the node.*
- Port Scan - *The bot finds accessible database servers on the network.*
- Attacking - *The bot delivers the payload to the discovered database servers.*

Each of these stages has a random, configurable probability of succeeding (by default 10%). The bot can also be configured to repeat the attack once complete.
NB: The Port Scan is achieved using game layer functionality based on a probablility of success calculation.

Usage
=====

- Create an instance and call ``configure`` to set:
    - Target database server IP
    - Database password (if needed)
    - SQL statement payload
    - Probabilities for succeeding each of the above attack stages
- Call ``run`` to connect and execute the statement.

The bot handles connecting, executing the statement, and disconnecting.

In a simulation, the bot can be controlled by using ``DataManipulationAgent`` which calls ``run`` on the bot at configured timesteps.

Implementation
==============

The bot connects to a :ref:`DatabaseClient` and leverages its connectivity. The host running ``DataManipulationBot`` must also have a :ref:`DatabaseClient` installed on it.

- Uses the Application base class for lifecycle management.
- Credentials, target IP and other options set via ``configure``.
- ``run`` handles connecting, executing statement, and disconnecting.
- SQL payload executed via ``query`` method.
- Results in malicious SQL being executed on remote database server.


Examples
========

Python
""""""

.. code-block:: python

    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
    from primaite.simulator.system.applications.red_applications.data_manipulation_bot import DataManipulationBot
    from primaite.simulator.system.applications.database_client import DatabaseClient

    client_1 = Computer(config={
        "hostname":"client_1",
        "ip_address":"192.168.10.21",
        "subnet_mask":"255.255.255.0",
        "default_gateway":"192.168.10.1",
        "operating_state":NodeOperatingState.ON # initialise the computer in an ON state
        }
    )
    network.connect(endpoint_b=client_1.network_interface[1], endpoint_a=switch_2.network_interface[1])
    client_1.software_manager.install(DatabaseClient)
    client_1.software_manager.install(DataManipulationBot)
    data_manipulation_bot: DataManipulationBot = client_1.software_manager.software.get("data-manipulation-bot")
    data_manipulation_bot.configure(server_ip_address=IPv4Address("192.168.1.14"), payload="DELETE")
    data_manipulation_bot.run()

This would connect to the database service at 192.168.1.14, authenticate, and execute the SQL statement to delete database contents.

Example with ``DataManipulationAgent``
""""""""""""""""""""""""""""""""""""""

If not using the data manipulation bot manually, it needs to be used with a data manipulation agent. Below is an example section of configuration file for setting up a simulation with data manipulation bot and agent.

.. code-block:: yaml

    game:
      # ...
      agents:
        - ref: data_manipulation_red_bot
          team: RED
          type: red-database-corrupting-agent

          agent_settings:
    # ...

    simulation:
      network:
        nodes:
        - hostname: client_1
          type: computer
          # ... additional configuration here
          applications:
          - ref: data_manipulation_bot
            type: data-manipulation-bot
            options:
              port_scan_p_of_success: 0.1
              data_manipulation_p_of_success: 0.1
              payload: "DELETE"
              server_ip: 192.168.1.14
          - ref: web_server_database_client
            type: database-client
            options:
              db_server_ip: 192.168.1.14

Configuration
=============


``server_ip``
"""""""""""""

IP address of the :ref:`DatabaseService` which the ``DataManipulationBot`` will try to attack.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``server_password``
"""""""""""""""""""

Optional. Default value is ``None``.

The password that the ``DataManipulationBot`` will use to access the :ref:`DatabaseService`.

``payload``
"""""""""""

Optional. Default value is ``DELETE``.

The payload that the ``DataManipulationBot`` will send to the :ref:`DatabaseService`.

.. include:: ../common/db_payload_list.rst

``port_scan_p_of_success``
""""""""""""""""""""""""""

Optional. Default value is ``0.1``.

The chance of the ``DataManipulationBot`` to succeed with a port scan (and therefore continue the attack).

This must be a float value between ``0`` and ``1``.

``data_manipulation_p_of_success``
""""""""""""""""""""""""""""""""""

Optional. Default value is ``0.1``.

The chance of the ``DataManipulationBot`` to succeed with a data manipulation attack.

This must be a float value between ``0`` and ``1``.

``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
