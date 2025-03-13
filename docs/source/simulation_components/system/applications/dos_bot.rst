.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _DoSBot:

dos-bot
######

The ``dos-bot`` is an implementation of a Denial of Service attack within the PrimAITE simulation.
This specifically simulates a `Slow Loris attack`_.

.. _Slow Loris Attack: https://en.wikipedia.org/wiki/Slowloris_(computer_security)

Key features
============

- Connects to the :ref:`database-service` via the ``SoftwareManager``.
- Makes many connections to the :ref:`database-service` which ends up using up the available connections.

Usage
=====

- Configure with target IP address and optional password.
- use ``run`` to run the application_loop of dos-bot to begin attacks
- dos-bot runs through different actions at each timestep

Implementation
==============

- Leverages :ref:`database-client` to create connections with :ref`DatabaseServer`.
- Extends base Application class.

Examples
========

Python
""""""

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.applications.red_applications.dos_bot import dos-bot

    # Create Computer
    computer = Computer(config={
        "hostname":"computer",
        "ip_address":"192.168.1.2",
        "subnet_mask":"255.255.255.0",
        "default_gateway":"192.168.1.1",
        "start_up_duration":0,
        }
    )
    computer.power_on()

    # Install dos-bot on computer
    computer.software_manager.install(dos-bot)
    dos_bot: dos-bot = computer.software_manager.software.get("dos-bot")

    # Configure the dos-bot
    dos_bot.configure(
        target_ip_address=IPv4Address("192.168.0.10"),
        payload="SPOOF DATA",
        repeat=False,
        port_scan_p_of_success=0.8,
        dos_intensity=1.0,
        max_sessions=1000
    )

    # run dos-bot
    dos_bot.run()


Via Configuration
"""""""""""""""""

.. code-block:: yaml

    simulation:
      network:
        nodes:
        - hostname: example_computer
        type: computer
        ...
        applications:
        - type: dos-bot
        options:
          target_ip_address: 192.168.0.10
          payload: SPOOF DATA
          repeat: False
          port_scan_p_of_success: 0.8
          dos_intensity: 1.0
          max_sessions: 1000

Configuration
=============

``target_ip_address``
"""""""""""""""""""""

IP address of the :ref:`database-service` which the ``data-manipulation-bot`` will try to attack.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``target_port``
"""""""""""""""

Optional. Default value is ``5432``.

Port of the target service.

See :ref:`List of IPProtocols <List of IPProtocols>` for a list of protocols.

``payload``
"""""""""""

Optional. Default value is ``None``.

The payload that the ``dos-bot`` sends as part of its attack.

.. include:: ../common/db_payload_list.rst

``repeat``
""""""""""

Optional. Default value is ``False``.

If ``True`` the ``dos-bot`` will maintain its attack.

``port_scan_p_of_success``
""""""""""""""""""""""""""

Optional. Default value is ``0.1``.

The chance of the ``dos-bot`` to succeed with a port scan (and therefore continue the attack).

This must be a float value between ``0`` and ``1``.

``dos_intensity``
"""""""""""""""""

Optional. Default value is ``1.0``.

The intensity of the Denial of Service attack. This is multiplied by the number of ``max_sessions``.

This must be a float value between ``0`` and ``1``.

``max_sessions``
""""""""""""""""

Optional. Default value is ``1000``.

The maximum number of sessions the ``dos-bot`` is able to make.

This must be an integer value equal to or greater than ``0``.

``Common Attributes``
^^^^^^^^^^^^^^^^^^^^^

See :ref:`Common Configuration`
