.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _C2_Suite:

Command and Control Application Suite
#####################################

Comprising of two applications, the command and control (C2) suites intends to introduce
malicious network architecture and begin to further the realism of red agents within primAITE.

Overview:
=========

These two new classes intend to Red Agents a cyber realistic way of leveraging the capabilities of the ``Terminal`` application.
Whilst introducing both more oppourtinies for the blue agent to notice and subvert Red Agents during an episode.

For a more in-depth look at the command and control applications then please refer to the ``C2-E2E-Notebook``.

``C2 Server``
""""""""""""

The C2 Server application is intended to represent the malicious infrastructure already under the control of an adversary.

The C2 Server is configured to listen and await ``keep alive`` traffic from a c2 beacon. Once received the C2 Server is able to send and receive c2 commands.

Currently, the C2 Server offers three commands:

+---------------------+---------------------------------------------------------------------------+
|C2 Command           | Meaning                                                                   |
+=====================+===========================================================================+
|RANSOMWARE_CONFIGURE | Configures an installed ransomware script based on the passed parameters. |
+---------------------+---------------------------------------------------------------------------+
|RANSOMWARE_LAUNCH    | Launches the installed ransomware script.                                 |
+---------------------+---------------------------------------------------------------------------+
|TERMINAL_COMMAND     | Executes a command via the terminal installed on the C2 Beacons Host.     |
+---------------------+---------------------------------------------------------------------------+


It's important to note that in order to keep the PrimAITE realistic from a cyber perspective,
The C2 Server application should never be visible or actionable upon directly by the blue agent.

This is because in the real world, C2 servers are hosted on ephemeral public domains that would not be accessible by private network blue agent.
Therefore granting a blue agent's the ability to perform counter measures directly against the application would be unrealistic.

It is more accurate to see the host that the C2 Server is installed on as being able to route to the C2 Server (Internet Access).

``C2 Beacon``
"""""""""""""

The C2 Beacon application is intended to represent malware that is used to establish and maintain contact to a C2 Server within a compromised network.

A C2 Beacon will need to be first configured with the C2 Server IP Address which can be done via the ``configure`` method.

Once installed and configured; the c2 beacon can establish connection with the C2 Server via executing the application.

This will send an initial ``keep alive`` to the given C2 Server (The C2 Server IPv4Address must be given upon C2 Beacon configuration).
Which is then resolved and responded by another ``Keep Alive`` by the c2 server back to the C2 beacon to confirm connection.

The C2 Beacon will send out periodic keep alive based on it's configuration parameters to configure it's active connection with the c2 server.

It's recommended that a C2 Beacon is installed and configured mid episode by a Red Agent for a more cyber realistic simulation.

Usage
=====

As mentioned, the C2 Suite is intended to grant Red Agents further flexibility whilst also expanding a blue agent's observation_space.

Adding to this, the following behaviour of the C2 beacon can be configured by users for increased domain randomisation:

- Frequency of C2 ``Keep Alive `` Communication``
- C2 Communication Port
- C2 Communication Protocol


Implementation
==============

Both applications inherit from an abstract C2 which handles the keep alive functionality and main logic.
However, each host implements it's receive methods individually.

- The ``C2 Beacon`` is responsible for the following logic:
    - Establishes and confirms connection to the C2 Server via sending ``C2Payload.KEEP_ALIVE``.
    - Receives and executes C2 Commands given by the C2 Server via ``C2Payload.INPUT``.
    - Returns the RequestResponse of the C2 Commands executed back the C2 Server via ``C2Payload.OUTPUT``.

- The ``C2 Server`` is responsible for the following logic:
    - Listens and resolves connection to a C2 Beacon via responding to ``C2Payload.KEEP_ALIVE``.
    - Sends C2 Commands to the C2 Beacon via ``C2Payload.INPUT``.
    - Receives the RequestResponse of the C2 Commands executed by C2 Beacon via ``C2Payload.OUTPUT``.



Examples
========

Python
""""""
.. code-block:: python
    from primaite.simulator.system.applications.red_applications.c2.c2_beacon import C2Beacon
    from primaite.simulator.system.applications.red_applications.c2.c2_server import C2Server
    from primaite.simulator.system.applications.red_applications.c2.c2_server import C2Command
    from primaite.simulator.network.hardware.nodes.host.computer import Computer

    # Network Setup

    node_a = Computer(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0)
    node_a.power_on()
    node_a.software_manager.install(software_class=C2Server)
    node_a.software_manager.get_open_ports()


    node_b = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node_b.power_on()
    node_b.software_manager.install(software_class=C2Beacon)
    node_b.software_manager.install(software_class=RansomwareScript)
    network.connect(node_a.network_interface[1], node_b.network_interface[1])


    # C2 Application objects

    c2_server_host = simulation_testing_network.get_node_by_hostname("node_a")
    c2_beacon_host = simulation_testing_network.get_node_by_hostname("node_b")


    c2_server: C2Server = c2_server_host.software_manager.software["C2Server"]
    c2_beacon: C2Beacon = c2_beacon_host.software_manager.software["C2Beacon"]

    # Configuring the C2 Beacon
    c2_beacon.configure(c2_server_ip_address="192.168.0.10", keep_alive_frequency=5)

    # Launching the C2 Server (Needs to be running in order to listen for connections)
    c2_server.run()

    # Establishing connection
    c2_beacon.establish()

    # Example command: Configuring Ransomware

    ransomware_config = {"server_ip_address": "1.1.1.1"}
    c2_server._send_command(given_command=C2Command.RANSOMWARE_CONFIGURE, command_options=ransomware_config)


For a more in-depth look at the command and control applications then please refer to the ``C2-Suite-E2E-Notebook``.
