.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


Software
========

-------------
Base Software
-------------

All software which inherits ``IOSoftware`` installed on a node will not work unless the node has been turned on.

See :ref:`Node Start up and Shut down`

.. code-block:: python

    from primaite.simulator.network.hardware.base import Node
    from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
    from primaite.simulator.system.services.service import ServiceOperatingState
    from primaite.simulator.system.services.web_server.web_server import WebServer

    node = Node(hostname="pc_a", start_up_duration=0, shut_down_duration=0)

    node.power_on()
    assert node.operating_state is NodeOperatingState.ON

    node.software_manager.install(WebServer)

    web_server: WebServer = node.software_manager.software.get("WebServer")
    assert web_server.operating_state is ServiceOperatingState.RUNNING # service is immediately ran after install

    node.power_off()
    assert node.operating_state is NodeOperatingState.OFF
    assert web_server.operating_state is ServiceOperatingState.STOPPED # service stops when node is powered off

    node.power_on()
    assert node.operating_state is NodeOperatingState.ON
    assert web_server.operating_state is ServiceOperatingState.RUNNING # service turned back on when node is powered on


Services, Processes and Applications:
#####################################

.. toctree::
   :maxdepth: 2

   database_client_server
   data_manipulation_bot
   dns_client_server
   ftp_client_server
   ntp_client_server
   web_browser_and_web_server_service
