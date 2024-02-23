.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _DoSBot:

DoSBot
######

The ``DoSBot`` is an implementation of a Denial of Service attack within the PrimAITE simulation. This specifically simulates a `Slow Loris attack <https://en.wikipedia.org/wiki/Slowloris_(computer_security)>`.

Key features
============

- Connects to the :ref:`DatabaseService` via the ``SoftwareManager``.
- Makes many connections to the :ref:`DatabaseService` which ends up using up the available connections.

Usage
=====

- Configure with target IP address and optional password.
- use ``run`` to run the application_loop of DoSBot to begin attacks
- DoSBot runs through different actions at each timestep

Implementation
==============

- Leverages :ref:`DatabaseClient` to create connections with :ref`DatabaseServer`.
- Extends base Application class.

Examples
========

Python
""""""

.. code-block:: python

    from ipaddress import IPv4Address

    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.system.applications.red_applications.dos_bot import DoSBot

    # Create Computer
    computer = Computer(
        hostname="computer",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    computer.power_on()

    # Install DoSBot on computer
    computer.software_manager.install(DoSBot)
    dos_bot: DoSBot = computer.software_manager.software.get("DoSBot")

    # Configure the DoSBot
    dos_bot.configure(
        target_ip_address=IPv4Address("192.168.0.10"),
        payload="SPOOF DATA",
        repeat=False,
        port_scan_p_of_success=0.8,
        dos_intensity=1.0,
        max_sessions=1000
    )

    # run DoSBot
    dos_bot.run()


Via Configuration
"""""""""""""""""

.. code-block:: yaml

    simulation:
        network:
            nodes:
                - ref: example_computer
                hostname: example_computer
                type: computer
                ...
                applications:
                    - ref: dos_bot
                    type: DoSBot
                    options:
                        target_ip_address: 192.168.0.10
                        payload: SPOOF DATA
                        repeat: False
                        port_scan_p_of_success: 0.8
                        dos_intensity: 1.0
                        max_sessions: 1000

Configuration
=============

.. include:: ../common/common_configuration.rst

.. |SOFTWARE_NAME| replace:: DoSBot
.. |SOFTWARE_NAME_BACKTICK| replace:: ``DoSBot``

``target_ip_address``
"""""""""""""""""""""

IP address of the :ref:`DatabaseService` which the ``DataManipulationBot`` will try to attack.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``target_port``
"""""""""""""""

Optional. Default value is ``5432``.

Port of the target service.

See :ref:`List of IPProtocols <List of IPProtocols>` for a list of protocols.

``payload``
"""""""""""

Optional. Default value is ``None``.

The payload that the ``DoSBot`` sends as part of its attack.

``repeat``
""""""""""

Optional. Default value is ``False``.

If ``True`` the ``DoSBot`` will maintain its attack.

``port_scan_p_of_success``
""""""""""""""""""""""""""

Optional. Default value is ``0.1``.

The chance of the ``DoSBot`` to succeed with a port scan (and therefore continue the attack).

This must be a float value between ``0`` and ``1``.

``dos_intensity``
"""""""""""""""""

Optional. Default value is ``1.0``.

The intensity of the Denial of Service attack. This is multiplied by the number of ``max_sessions``.

This must be a float value between ``0`` and ``1``.

``max_sessions``
""""""""""""""""

Optional. Default value is ``1000``.

The maximum number of sessions the ``DoSBot`` is able to make.

This must be an integer value above equal to or greater than ``0``.
