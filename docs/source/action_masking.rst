.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

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
| **do_nothing**                           | Always Possible.                                                    |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_scan**                    | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_stop**                    | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_start**                   | Node is on. Service is stopped.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_pause**                   | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_resume**                  | Node is on. Service is paused.                                      |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_restart**                 | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_disable**                 | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_enable**                  | Node is on. Service is disabled.                                    |
+------------------------------------------+---------------------------------------------------------------------+
| **node_service_fix**                     | Node is on. Service is running.                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **node_application_execute**             | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_application_scan**                | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **node_application_close**               | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **node_application_fix**                 | Node is on. Application is running.                                 |
+------------------------------------------+---------------------------------------------------------------------+
| **node_application_install**             | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_application_remove**              | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_file_scan**                       | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node_file_create**                     | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_file_checkhash**                  | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node_file_delete**                     | Node is on. File exists.                                            |
+------------------------------------------+---------------------------------------------------------------------+
| **node_file_repair**                     | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node_file_restore**                    | Node is on. File exists. File is deleted.                           |
+------------------------------------------+---------------------------------------------------------------------+
| **node_file_corrupt**                    | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node_file_access**                     | Node is on. File exists. File not deleted.                          |
+------------------------------------------+---------------------------------------------------------------------+
| **node_folder_create**                   | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_folder_scan**                     | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **node_folder_checkhash**                | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **node_folder_repair**                   | Node is on. Folder exists. Folder not deleted.                      |
+------------------------------------------+---------------------------------------------------------------------+
| **node_folder_restore**                  | Node is on. Folder exists. Folder is deleted.                       |
+------------------------------------------+---------------------------------------------------------------------+
| **node_os_scan**                         | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **host_nic_enable**                      | NIC is disabled. Node is on.                                        |
+------------------------------------------+---------------------------------------------------------------------+
| **host_nic_disable**                     | NIC is enabled. Node is on.                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_shutdown**                        | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_startup**                         | Node is off.                                                        |
+------------------------------------------+---------------------------------------------------------------------+
| **node_reset**                           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_nmap_ping_scan**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_nmap_port_scan**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_network_service_recon**           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **network_port_enable**                  | Node is on. Router is on.                                           |
+------------------------------------------+---------------------------------------------------------------------+
| **network_port_disable**                 | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **router_acl_addrule**                   | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **router_acl_removerule**                | Router is on.                                                       |
+------------------------------------------+---------------------------------------------------------------------+
| **firewall_acl_addrule**                 | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **firewall_acl_removerule**              | Firewall is on.                                                     |
+------------------------------------------+---------------------------------------------------------------------+
| **configure_database_client**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **configure_ransomware_script**          | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **c2_server_ransomware_configure**       | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **configure_dos_bot**                    | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **configure_c2_beacon**                  | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **c2_server_ransomware_launch**          | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **c2_server_terminal_command**           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **c2_server_data_exfiltrate**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_account_change_password**         | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_session_remote_login**            | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_session_remote_logoff**           | Node is on.                                                         |
+------------------------------------------+---------------------------------------------------------------------+
| **node_send_remote_command**             | Node is on.                                                         |
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
