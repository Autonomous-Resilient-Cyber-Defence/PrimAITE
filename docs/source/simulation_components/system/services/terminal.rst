.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _Terminal:

Terminal
########

The ``Terminal.py`` class provides a generic terminal simulation, by extending the base Service class within PrimAITE. The aim of this is to act as the primary entrypoint for Nodes within the environment.


Overview
========

The Terminal service uses Secure Socket (SSH) as the communication method between terminals. They operate on port 22, and are part of the services automatically
installed on Nodes when they are instantiated.

Key capabilities
""""""""""""""""

 - Ensures packets are matched to an existing session
 - Simulates common Terminal processes/commands.
 - Leverages the Service base class for install/uninstall, status tracking etc.

Usage
"""""

 - Pre-Installs on any `Node` (component with the exception of `Switches`).
 - Terminal Clients connect, execute commands and disconnect from remote nodes.
 - Ensures that users are logged in to the component before executing any commands.
 - Service runs on SSH port 22 by default.
 - Enables Agents to send commands both remotely and locally.

Implementation
""""""""""""""

 - Manages remote connections in a dictionary by session ID.
 - Processes commands, forwarding to the ``RequestManager`` or ``SessionManager`` where appropriate.
 - Extends Service class.
  - A detailed guide on the implementation and functionality of the Terminal class can be found in the "Terminal-Processing" jupyter notebook.

Command Format
^^^^^^^^^^^^^^

``Terminals`` implement their commands through leveraging the pre-existing :doc:`../../request_system`.

Due to this ``Terminals`` will only accept commands passed within the ``RequestFormat``.

:py:class:`primaite.game.interface.RequestFormat`

For example, ``terminal`` command actions when used in ``yaml`` format are formatted as follows:

.. code-block:: yaml
    command:
        - "file_system"
        - "create"
        - "file"
        - "downloads"
        - "cat.png"
        - "False"

**This command creates file called ``cat.png`` within the ``downloads`` folder.**

This is then loaded from ``yaml`` into a dictionary containing the terminal command:

.. code-block:: python

    {"command":["file_system", "create", "file", "downloads", "cat.png", "False"]}

Which is then parsed to the ``Terminals`` Request Manager to be executed.

Game Layer Usage (Agents)
========================

The below code examples demonstrate how to use terminal related actions in yaml files.

yaml
""""

``NODE_SEND_LOCAL_COMMAND``
"""""""""""""""""""""""""""

Agents can execute local commands without needing to perform a separate remote login action (``SSH_TO_REMOTE``).

.. code-block:: yaml

    ...
        ...
          action: NODE_SEND_LOCAL_COMMAND
          options:
            node_id: 0
            username: admin
            password: admin
            command: # Example command - Creates a file called 'cat.png' in the downloads folder.
              - "file_system"
              - "create"
              - "file"
              - "downloads"
              - "cat.png"
              - "False"


``SSH_TO_REMOTE``
"""""""""""""""""

Agents are able to use the terminal to login into remote nodes via ``SSH`` which allows for agents to execute commands on remote hosts.

.. code-block:: yaml

    ...
        ...
          action: SSH_TO_REMOTE
          options:
            node_id: 0
            username: admin
            password: admin
            remote_ip: 192.168.0.10 # Example Ip Address. (The remote host's IP that will be used by ssh)


``NODE_SEND_REMOTE_COMMAND``
""""""""""""""""""""""""""""

After remotely login into another host, a agent can use the ``NODE_SEND_REMOTE_COMMAND`` to execute commands across the network remotely.

.. code-block:: yaml

    ...
        ...
          action: NODE_SEND_REMOTE_COMMAND
          options:
            node_id: 0
            remote_ip: 192.168.0.10
            command:
              - "file_system"
              - "create"
              - "file"
              - "downloads"
              - "cat.png"
              - "False"



Simulation Layer Usage
======================


The below code examples demonstrate how to create a terminal, a remote terminal, and how to send a basic application install command to a remote node.

Python
""""""

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.services.terminal.terminal import Terminal
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState

    client = Computer(
        hostname="client",
        ip_address="192.168.10.21",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        operating_state=NodeOperatingState.ON,
    )

    terminal: Terminal = client.software_manager.software.get("Terminal")

Creating Remote Terminal Connection
"""""""""""""""""""""""""""""""""""


.. code-block:: python

    from primaite.simulator.system.services.terminal.terminal import Terminal
    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.services.terminal.terminal import RemoteTerminalConnection


    network = Network()
    node_a = Computer(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0)
    node_a.power_on()
    node_b = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node_b.power_on()
    network.connect(node_a.network_interface[1], node_b.network_interface[1])

    terminal_a: Terminal = node_a.software_manager.software.get("Terminal")


    term_a_term_b_remote_connection: RemoteTerminalConnection = terminal_a.login(username="admin", password="Admin123!", ip_address="192.168.0.11")



Executing a basic application install command
"""""""""""""""""""""""""""""""""""""""""""""

.. code-block:: python

    from primaite.simulator.system.services.terminal.terminal import Terminal
    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.services.terminal.terminal import RemoteTerminalConnection
    from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript


    network = Network()
    node_a = Computer(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0)
    node_a.power_on()
    node_b = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node_b.power_on()
    network.connect(node_a.network_interface[1], node_b.network_interface[1])

    terminal_a: Terminal = node_a.software_manager.software.get("Terminal")


    term_a_term_b_remote_connection: RemoteTerminalConnection = terminal_a.login(username="admin", password="Admin123!", ip_address="192.168.0.11")

    term_a_term_b_remote_connection.execute(["software_manager", "application", "install", "RansomwareScript"])



Creating a folder on a remote node
""""""""""""""""""""""""""""""""""

.. code-block:: python

    from primaite.simulator.system.services.terminal.terminal import Terminal
    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.services.terminal.terminal import RemoteTerminalConnection
    from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript


    network = Network()
    node_a = Computer(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0)
    node_a.power_on()
    node_b = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node_b.power_on()
    network.connect(node_a.network_interface[1], node_b.network_interface[1])

    terminal_a: Terminal = node_a.software_manager.software.get("Terminal")


    term_a_term_b_remote_connection: RemoteTerminalConnection = terminal_a.login(username="admin", password="Admin123!", ip_address="192.168.0.11")

    term_a_term_b_remote_connection.execute(["file_system", "create", "folder", "downloads"])


Disconnect from Remote Node
"""""""""""""""""""""""""""

.. code-block:: python

    from primaite.simulator.system.services.terminal.terminal import Terminal
    from primaite.simulator.network.container import Network
    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.services.terminal.terminal import RemoteTerminalConnection
    from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript


    network = Network()
    node_a = Computer(hostname="node_a", ip_address="192.168.0.10", subnet_mask="255.255.255.0", start_up_duration=0)
    node_a.power_on()
    node_b = Computer(hostname="node_b", ip_address="192.168.0.11", subnet_mask="255.255.255.0", start_up_duration=0)
    node_b.power_on()
    network.connect(node_a.network_interface[1], node_b.network_interface[1])

    terminal_a: Terminal = node_a.software_manager.software.get("Terminal")


    term_a_term_b_remote_connection: RemoteTerminalConnection = terminal_a.login(username="admin", password="Admin123!", ip_address="192.168.0.11")

    term_a_term_b_remote_connection.disconnect()


``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
