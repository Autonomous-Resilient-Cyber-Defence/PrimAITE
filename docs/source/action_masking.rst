.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _action_masking:

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
| **do-nothing**                           | Always Possible.                                                    |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-scan**                    | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-stop**                    | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-start**                   | Node is on. Service is stopped.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-pause**                   | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-resume**                  | Node is on. Service is paused.                                      |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-restart**                 | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-disable**                 | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-enable**                  | Node is on. Service is disabled.                                    |
+------------------------------------------+---------------------------------------------------------------------+
| **node-service-fix**                     | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node-application-execute**             | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-application-scan**                | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **node-application-close**               | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **node-application-fix**                 | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **node-application-install**             | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-application-remove**              | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-file-scan**                       | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node-file-create**                     | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-file-checkhash**                  | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node-file-delete**                     | Node is on. File exists.                                            |
+------------------------------------------+---------------------------------------------------------------------+
| **node-file-repair**                     | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node-file-restore**                    | Node is on. File exists. File is deleted.                           |
+------------------------------------------+---------------------------------------------------------------------+
| **node-file-corrupt**                    | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node-file-access**                     | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node-folder-create**                   | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-folder-scan**                     | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **node-folder-checkhash**                | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **node-folder-repair**                   | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **node-folder-restore**                  | Node is on. Folder exists. Folder is deleted.                       |
+------------------------------------------+---------------------------------------------------------------------+
| **node-os-scan**                         | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **host-nic-enable**                      | NIC is disabled. Node is on.                                        |
+------------------------------------------+---------------------------------------------------------------------+
| **host-nic-disable**                     | NIC is enabled. Node is on.                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-shutdown**                        | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-startup**                         | Node is off.                                                        |
+------------------------------------------+---------------------------------------------------------------------+
| **node-reset**                           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-nmap-ping-scan**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-nmap-port-scan**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-network-service-recon**           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **network-port-enable**                  | Node is on. Router is on.                                           |
+------------------------------------------+---------------------------------------------------------------------+
| **network-port-disable**                 | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **router-acl-add-rule**                  | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **router-acl-remove-rule**               | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **firewall-acl-add-rule**                | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **firewall-acl-remove-rule**             | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **configure-database-client**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **configure-ransomware-script**          | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **c2-server-ransomware-configure**       | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **configure-dos-bot**                    | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **configure-c2-beacon**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **c2-server-ransomware-launch**          | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **c2-server-terminal-command**           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **c2-server-data-exfiltrate**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-account-change-password**         | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-session-remote-login**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-session-remote-logoff**           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node-send-remote-command**             | Node is on.                                                         |
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
