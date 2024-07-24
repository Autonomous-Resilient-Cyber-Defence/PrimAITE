.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

Action Masking
**************
The PrimAITE simulation is able to provide action masks in the environment output. These action masks let the agents know
about which actions are invalid based on the current environment state. For instance, it's not possible to install
software on a node that is turned off. Therefore, if an agent has a NODE_SOFTWARE_INSTALL in it's action map for that node,
the action mask will show `0` in the corresponding entry.

Configuration
=============
Action masking is supported for agents that use the `ProxyAgent` class (the class used for connecting to RL algorithms).
In order to use action masking, set the agent_settings.action_masking parameter to True in the config file.

Masking Logic
=============
The following logic is applied:

+------------------------------------------+---------------------------------------------------------------------+
| Action                                   | Action Mask Logic                                                   |
+==========================================+=====================================================================+
| **DONOTHING**                            | Always Possible.                                                    |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_SCAN**               | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_STOP**               | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_START**              | Node is on. Service is stopped.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_PAUSE**              | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_RESUME**             | Node is on. Service is paused.                                      |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_RESTART**            | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_DISABLE**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_ENABLE**             | Node is on. Service is disabled.                                    |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SERVICE_FIX**                | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_APPLICATION_EXECUTE**        | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_APPLICATION_SCAN**           | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_APPLICATION_CLOSE**          | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_APPLICATION_FIX**            | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_APPLICATION_INSTALL**        | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_APPLICATION_REMOVE**         | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FILE_SCAN**                  | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FILE_CREATE**                | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FILE_CHECKHASH**             | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FILE_DELETE**                | Node is on. File exists.                                            |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FILE_REPAIR**                | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FILE_RESTORE**               | Node is on. File exists. File is deleted.                           |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FILE_CORRUPT**               | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FILE_ACCESS**                | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FOLDER_CREATE**              | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FOLDER_SCAN**                | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FOLDER_CHECKHASH**           | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FOLDER_REPAIR**              | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_FOLDER_RESTORE**             | Node is on. Folder exists. Folder is deleted.                       |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_OS_SCAN**                    | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_NIC_ENABLE**                 | NIC is disabled. Node is on.                                        |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_NIC_DISABLE**                | NIC is enabled. Node is on.                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_SHUTDOWN**                   | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_STARTUP**                    | Node is off.                                                        |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_RESET**                      | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_NMAP_PING_SCAN**             | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_NMAP_PORT_SCAN**             | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_HOST_NMAP_NETWORK_SERVICE_RECON** | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_ROUTER_PORT_ENABLE**              | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_ROUTER_PORT_DISABLE**             | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_ROUTER_ACL_ADDRULE**              | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_ROUTER_ACL_REMOVERULE**           | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FIREWALL_PORT_ENABLE**            | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FIREWALL_PORT_DISABLE**           | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FIREWALL_ACL_ADDRULE**            | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FIREWALL_ACL_REMOVERULE**         | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+


Mechanism
=========
The environment iterates over the RL agent's ``action_map`` and generates the corresponding simulator request string.
It uses the ``RequestManager.check_valid()`` method to invoke the relevant ``RequestPermissionValidator`` without
actually running the request on the simulation.

Current Limitations
===================
Currently, action masking only considers whether the action as a whole is possible, it doesn't verify that the exact
parameter combination passed to the action make sense in the current context. For instance, if ACL rule 3 on router_1 is
already populated, the action for adding another rule at position 3 will be available regardless, as long as that router
is turned on. This will never block valid actions. It will just occasionally allow invalid actions.
