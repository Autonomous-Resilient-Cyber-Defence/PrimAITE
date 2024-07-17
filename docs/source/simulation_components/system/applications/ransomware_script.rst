.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _RansomwareScript:

RansomwareScript
###################

The RansomwareScript class provides functionality to connect to a :ref:`DatabaseService` and set a database's database.db into an ``CORRUPTED`` state.

Overview
========

The ransomware script intends to simulate a generic implementation of ransomware.

Currently, due to simulation restraints, the ransomware script is unable to attack a hosts without an active database service.

The ransomware script is similar to that of the data_manipulation_bot but does not have any separate stages or configurable probabilities.

Additionally, similar to the data_manipulation_bot, the ransomware script must be installed on a host with a pre-existing :ref:`DatabaseClient` application installed.

Usage
=====

- Create an instance and call ``configure`` to set:
    - Target Database IP
    - Database password (if needed)
- Call ``Execute`` to connect and execute the ransomware script.

This application handles connections to the database server and the connection made to encrypt the database but it does not handle disconnections.

Implementation
==============

Currently, the ransomware script connects to a :ref:`DatabaseClient` and leverages its connectivity. The host running ``RansomwareScript`` must also have a :ref:`DatabaseClient` installed on it.

- Uses the Application base class for lifecycle management.
- Target IP and other options set via ``configure``.
- ``execute`` handles connecting and encrypting.


Examples
========

Python
""""""
.. code-block:: python

    from primaite.simulator.network.hardware.nodes.host.computer import Computer
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
    from primaite.simulator.system.applications.red_applications.RansomwareScript import RansomwareScript
    from primaite.simulator.system.applications.database_client import DatabaseClient

    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.10.21",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        operating_state=NodeOperatingState.ON # initialise the computer in an ON state
    )
    network.connect(endpoint_b=client_1.network_interface[1], endpoint_a=switch_2.network_interface[1])
    client_1.software_manager.install(DatabaseClient)
    client_1.software_manager.install(RansomwareScript)
    RansomwareScript: RansomwareScript = client_1.software_manager.software.get("RansomwareScript")
    RansomwareScript.configure(server_ip_address=IPv4Address("192.168.1.14"))
    RansomwareScript.execute()


Configuration
=============

The RansomwareScript inherits configuration options such as ``fix_duration`` from its parent class. However, for the ``RansomwareScript`` the most relevant option is ``server_ip``.

.. include:: ../common/common_configuration.rst

.. |SOFTWARE_NAME| replace:: RansomwareScript
.. |SOFTWARE_NAME_BACKTICK| replace:: ``RansomwareScript``

``server_ip``
"""""""""""""

IP address of the :ref:`DatabaseService` which the ``RansomwareScript`` will encrypt.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.
