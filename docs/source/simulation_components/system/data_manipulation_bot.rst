.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


DataManipulationBot
===================

The ``DataManipulationBot`` class provides functionality to connect to a ``DatabaseService`` and execute malicious SQL statements.

Overview
--------

The bot is intended to simulate a malicious actor carrying out attacks like:

- Dropping tables
- Deleting records
- Modifying data

On a database server by abusing an application's trusted database connectivity.

The bot performs attacks in the following stages to simulate the real pattern of an attack:

- Logon - *The bot gains credentials and accesses the node.*
- Port Scan - *The bot finds accessible database servers on the network.*
- Attacking - *The bot delivers the payload to the discovered database servers.*

Each of these stages has a random, configurable probability of succeeding (by default 10%). The bot can also be configured to repeat the attack once complete.

Usage
-----

- Create an instance and call ``configure`` to set:
    - Target database server IP
    - Database password (if needed)
    - SQL statement payload
    - Probabilities for succeeding each of the above attack stages
- Call ``run`` to connect and execute the statement.

The bot handles connecting, executing the statement, and disconnecting.

In a simulation, the bot can be controlled by using ``DataManipulationAgent`` which calls ``run`` on the bot at configured timesteps.

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
    data_manipulation_bot.configure(server_ip_address=IPv4Address("192.168.1.14"), payload="DELETE")
    data_manipulation_bot.run()

This would connect to the database service at 192.168.1.14, authenticate, and execute the SQL statement to drop the 'users' table.

Example with ``DataManipulationAgent``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If not using the data manipulation bot manually, it needs to be used with a data manipulation agent. Below is an example section of configuration file for setting up a simulation with data manipulation bot and agent.

.. code-block:: yaml

    game_config:
      # ...
      agents:
        - ref: data_manipulation_red_bot
          team: RED
          type: RedDatabaseCorruptingAgent

          observation_space:
            type: UC2RedObservation
            options:
              nodes:
                - node_ref: client_1
                  observations:
                  - logon_status
                  - operating_status
                  applications:
                  - application_ref: data_manipulation_bot
                    observations:
                      operating_status
                      health_status
                  folders: {}

          action_space:
            action_list:
              - type: DONOTHING
              - type: NODE_APPLICATION_EXECUTE
            options:
              nodes:
              - node_ref: client_1
                applications:
                  - application_ref: data_manipulation_bot
              max_folders_per_node: 1
              max_files_per_folder: 1
              max_services_per_node: 1

          reward_function:
            reward_components:
              - type: DUMMY

          agent_settings:
            start_settings:
              start_step: 25
              frequency: 20
              variance: 5
    # ...

    simulation:
      network:
        nodes:
        - ref: client_1
          type: computer
          # ... additional configuration here
          applications:
          - ref: data_manipulation_bot
            type: DataManipulationBot
            options:
              port_scan_p_of_success: 0.1
              data_manipulation_p_of_success: 0.1
              payload: "DELETE"
              server_ip: 192.168.1.14

Implementation
--------------

The bot extends ``DatabaseClient`` and leverages its connectivity.

- Uses the Application base class for lifecycle management.
- Credentials, target IP and other options set via ``configure``.
- ``run`` handles connecting, executing statement, and disconnecting.
- SQL payload executed via ``query`` method.
- Results in malicious SQL being executed on remote database server.
