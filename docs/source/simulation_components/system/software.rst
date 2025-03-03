.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _software:


Software
========

-------------
Base Software
-------------

Software which inherits ``IOSoftware`` installed on a node will not work unless the node has been turned on.

See :ref:`Node Start up and Shut down`

.. code-block:: python

    from primaite.simulator.network.hardware.base import Node
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
    from primaite.simulator.system.services.service import ServiceOperatingState
    from primaite.simulator.system.services.web_server.web_server import WebServer

    node = Node(config={"hostname":"pc_a", "start_up_duration":0, "shut_down_duration":0})

    node.power_on()
    assert node.operating_state is NodeOperatingState.ON

    node.software_manager.install(WebServer)

    web_server: WebServer = node.software_manager.software.get("web-server")
    assert web_server.operating_state is ServiceOperatingState.RUNNING # service is immediately ran after install

    node.power_off()
    assert node.operating_state is NodeOperatingState.OFF
    assert web_server.operating_state is ServiceOperatingState.STOPPED # service stops when node is powered off

    node.power_on()
    assert node.operating_state is NodeOperatingState.ON
    assert web_server.operating_state is ServiceOperatingState.RUNNING # service turned back on when node is powered on

.. _List of Applications:

Applications
############

These are a list of applications that are currently available in PrimAITE:

.. include:: list_of_applications.rst

.. _List of Services:

Services
########

These are a list of services that are currently available in PrimAITE:

.. include:: list_of_services.rst

.. _List of Processes:

Processes
#########

`To be implemented`

Common Software Configuration
#############################

Below is a list of the common configuration items within Software components of PrimAITE:

.. include:: common/common_configuration.rst
