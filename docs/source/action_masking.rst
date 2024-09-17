.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

Action Masking
**************
The PrimAITE simulation is able to provide action masks in the environment output. These action masks let the agents know
about which actions are invalid based on the current environment state. For instance, it's not possible to install
software on a node that is turned off. Therefore, if an agent has a NODE_SOFTWARE_INSTALL in it's action map for that node,
the action mask will show `0` in the corresponding entry.

*Note: just because an action is available in the action mask does not mean it will be successful when executed. It just means it's possible to try to execute the action at this time.*

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
| **NODE_SERVICE_SCAN**                    | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SERVICE_STOP**                    | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SERVICE_START**                   | Node is on. Service is stopped.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SERVICE_PAUSE**                   | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SERVICE_RESUME**                  | Node is on. Service is paused.                                      |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SERVICE_RESTART**                 | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SERVICE_DISABLE**                 | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SERVICE_ENABLE**                  | Node is on. Service is disabled.                                    |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SERVICE_FIX**                     | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_APPLICATION_EXECUTE**             | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_APPLICATION_SCAN**                | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_APPLICATION_CLOSE**               | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_APPLICATION_FIX**                 | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_APPLICATION_INSTALL**             | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_APPLICATION_REMOVE**              | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FILE_SCAN**                       | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FILE_CREATE**                     | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FILE_CHECKHASH**                  | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FILE_DELETE**                     | Node is on. File exists.                                            |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FILE_REPAIR**                     | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FILE_RESTORE**                    | Node is on. File exists. File is deleted.                           |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FILE_CORRUPT**                    | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FILE_ACCESS**                     | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FOLDER_CREATE**                   | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FOLDER_SCAN**                     | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FOLDER_CHECKHASH**                | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FOLDER_REPAIR**                   | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_FOLDER_RESTORE**                  | Node is on. Folder exists. Folder is deleted.                       |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_OS_SCAN**                         | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **HOST_NIC_ENABLE**                      | NIC is disabled. Node is on.                                        |
+------------------------------------------+---------------------------------------------------------------------+
| **HOST_NIC_DISABLE**                     | NIC is enabled. Node is on.                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SHUTDOWN**                        | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_STARTUP**                         | Node is off.                                                        |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_RESET**                           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_NMAP_PING_SCAN**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_NMAP_PORT_SCAN**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_NMAP_NETWORK_SERVICE_RECON**      | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NETWORK_PORT_ENABLE**                  | Node is on. Router is on.                                           |
+------------------------------------------+---------------------------------------------------------------------+
| **NETWORK_PORT_DISABLE**                 | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **ROUTER_ACL_ADDRULE**                   | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **ROUTER_ACL_REMOVERULE**                | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **FIREWALL_ACL_ADDRULE**                 | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **FIREWALL_ACL_REMOVERULE**              | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_NMAP_PING_SCAN**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_NMAP_PORT_SCAN**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_NMAP_NETWORK_SERVICE_RECON**      | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **CONFIGURE_DATABASE_CLIENT**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **CONFIGURE_RANSOMWARE_SCRIPT**          | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **CONFIGURE_DOSBOT**                     | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **CONFIGURE_C2_BEACON**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **C2_SERVER_RANSOMWARE_LAUNCH**          | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **C2_SERVER_RANSOMWARE_CONFIGURE**       | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **C2_SERVER_TERMINAL_COMMAND**           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **C2_SERVER_DATA_EXFILTRATE**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_ACCOUNTS_CHANGE_PASSWORD**        | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **SSH_TO_REMOTE**                        | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **SESSIONS_REMOTE_LOGOFF**               | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **NODE_SEND_REMOTE_COMMAND**             | Node is on.                                                         |
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
