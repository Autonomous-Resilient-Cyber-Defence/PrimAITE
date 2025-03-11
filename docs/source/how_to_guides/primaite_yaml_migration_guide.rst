.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _migration_guide:


PrimAITE 4.0.0 YAML Configuration Migration Guide
*************************************************

Users upgrading from previous PrimAITE versions will be required to update their pre-existing YAML configs.

This migration guide details how to update any 3.0.0 yaml configs section by section to match the new 4.0.0 schema.

Any users accustomed to PrimAITE 2.0.0 are encouraged to make a fresh start to fully adapt to the changes since 2.0.0 release.

``io_settings``
===============

No major schema alterations are required for ``io_settings``.

However, a few more options have been introduced:

.. code-block:: yaml

    io_settings:
        save_agent_actions: false
        save_step_metadata: false
        save_pcap_logs: false
        save_sys_logs: false
        save_agent_logs: false
        write_sys_log_to_terminal: false
        sys_log_level: WARNING
        agent_log_level: INFO

More information can be found in the detailed in the configuration page: :ref:`io_settings`.

``game``
========

No reformatting required for ``game`` section.

If users have installed plugins that introduce new ports or protocols then the game must be configured with use them.

This can be done by adding to the ``ports`` and ``protocols`` list as shown in the yaml snippet below:

.. code-block:: yaml

    game:
    max_episode_length: 128
    ports:
    - HTTP
    - POSTGRES_SERVER
    - <EXAMPLE_PLUGIN_PORT>
    protocols:
    - ICMP
    - TCP
    - UDP
    - <EXAMPLE_PLUGIN_PROTOCOL>
    thresholds:
        nmne:
        high: 10
        medium: 5
        low: 0


``agents``
==========

PrimAITE 4.0.0 removes the requirement for agents to use indexes in actions.

To match the new schema, 3.0.0  agent's must adhere to the following:

- The ``action_list`` sub-section within the ``action_space`` is no longer required and can be removed.
- The ``options`` sub-section can also be removed. (Note that you do not accidentally remove ``options`` sub-section within the ``observation_space``)
- The agent that require an ``action_map`` sub-section require the following alterations:
    - Action's must now be converted to kebab-case:
    - Action ``options`` that previously required identifiers now instead require names.

.. code-block:: yaml

    # scan webapp service (4.0.0)
    1:
        action: node-service-scan   # kebab-case
        options:
          node_name: web_server     # IDs are no longer used - reference the name directly.
          service_name: web-server

    # scan webapp service (3.0.0)
    1:
        action: NODE_SERVICE_SCAN
        options:
          node_id: 1
          service_id: 0

+-------------------------------------+-------------------------------------+
| *3.0.0 action name*                 | *4.0.0 action name*                 |
+=====================================+=====================================+
| ``DONOTHING``                       | ``do-nothing``                      |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_SCAN``               | ``node-service-scan``               |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_STOP``               | ``node-service-stop``               |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_START``              | ``node-service-start``              |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_PAUSE``              | ``node-service-pause``              |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_RESUME``             | ``node-service-resume``             |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_RESTART``            | ``node-service-restart``            |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_DISABLE``            | ``node-service-disable``            |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_ENABLE``             | ``node-service-enable``             |
+-------------------------------------+-------------------------------------+
| ``NODE_SERVICE_FIX``                | ``node-service-fix``                |
+-------------------------------------+-------------------------------------+
| ``NODE_APPLICATION_REMOVE``         | ``node-application-remove``         |
+-------------------------------------+-------------------------------------+
| ``NODE_APPLICATION_CLOSE``          | ``node-application-close``          |
+-------------------------------------+-------------------------------------+
| ``NODE_APPLICATION_SCAN``           | ``node-application-scan``           |
+-------------------------------------+-------------------------------------+
| ``NODE_APPLICATION_FIX``            | ``node-application-fix``            |
+-------------------------------------+-------------------------------------+
| ``NODE_FILE_SCAN``                  | ``node-file-scan``                  |
+-------------------------------------+-------------------------------------+
| ``NODE_FILE_CHECKHASH``             | ``node-file-checkhash``             |
+-------------------------------------+-------------------------------------+
| ``NODE_FILE_DELETE``                | ``node-file-delete``                |
+-------------------------------------+-------------------------------------+
| ``NODE_FILE_REPAIR``                | ``node-file-repair``                |
+-------------------------------------+-------------------------------------+
| ``NODE_FILE_RESTORE``               | ``node-file-restore``               |
+-------------------------------------+-------------------------------------+
| ``NODE_FOLDER_SCAN``                | ``node-folder-scan``                |
+-------------------------------------+-------------------------------------+
| ``NODE_FOLDER_CHECKHASH``           | ``node-folder-checkhash``           |
+-------------------------------------+-------------------------------------+
| ``NODE_FOLDER_REPAIR``              | ``node-folder-repair``              |
+-------------------------------------+-------------------------------------+
| ``NODE_FOLDER_RESTORE``             | ``node-folder-restore``             |
+-------------------------------------+-------------------------------------+
| ``NODE_OS_SCAN``                    | ``node-os-scan``                    |
+-------------------------------------+-------------------------------------+
| ``NODE_SHUTDOWN``                   | ``node-shutdown``                   |
+-------------------------------------+-------------------------------------+
| ``NODE_STARTUP``                    | ``node-startup``                    |
+-------------------------------------+-------------------------------------+
| ``NODE_RESET``                      | ``node-reset``                      |
+-------------------------------------+-------------------------------------+
| ``HOST_NIC_ENABLE``                 | ``host-nic-enable``                 |
+-------------------------------------+-------------------------------------+
| ``HOST_NIC_DISABLE``                | ``host-nic-disable``                |
+-------------------------------------+-------------------------------------+
| ``NETWORK_PORT_ENABLE``             | ``network-port-enable``             |
+-------------------------------------+-------------------------------------+
| ``NETWORK_PORT_DISABLE``            | ``network-port-disable``            |
+-------------------------------------+-------------------------------------+
| ``ROUTER_ACL_ADDRULE``              | ``router-acl-addrule``              |
+-------------------------------------+-------------------------------------+
| ``ROUTER_ACL_REMOVERULE``           | ``router-acl-removerule``           |
+-------------------------------------+-------------------------------------+
| ``FIREWALL_ACL_ADDRULE``            | ``firewall-acl-addrule``            |
+-------------------------------------+-------------------------------------+
| ``FIREWALL_ACL_REMOVERULE``         | ``firewall-acl-removerule``         |
+-------------------------------------+-------------------------------------+
| ``NODE_APPLICATION_EXECUTE``        | ``node-application-execute``        |
+-------------------------------------+-------------------------------------+
| ``NODE_APPLICATION_INSTALL``        | ``node-application-install``        |
+-------------------------------------+-------------------------------------+
| ``NODE_FOLDER_CREATE``              | ``node-folder-create``              |
+-------------------------------------+-------------------------------------+
| ``NODE_FILE_CREATE``                | ``node-file-create``                |
+-------------------------------------+-------------------------------------+
| ``NODE_FILE_ACCESS``                | ``node-file-access``                |
+-------------------------------------+-------------------------------------+
| ``NODE_NMAP_PING_SCAN``             | ``node-nmap-ping-scan``             |
+-------------------------------------+-------------------------------------+
| ``NODE_NMAP_PORT_SCAN``             | ``node-nmap-port-scan``             |
+-------------------------------------+-------------------------------------+
| ``NODE_NMAP_NETWORK_SERVICE_RECON`` | ``node-nmap-network-service-recon`` |
+-------------------------------------+-------------------------------------+
| ``CONFIGURE_RANSOMWARE_SCRIPT``     | ``configure-ransomware-script``     |
+-------------------------------------+-------------------------------------+
| ``CONFIGURE_C2_BEACON``             | ``configure-c2-beacon``             |
+-------------------------------------+-------------------------------------+
| ``CONFIGURE_DATABASE_CLIENT``       | ``configure-database-client``       |
+-------------------------------------+-------------------------------------+
| ``CONFIGURE_DOS_BOT``               | ``configure-dos-bot``               |
+-------------------------------------+-------------------------------------+
| ``C2_SERVER_RANSOMWARE_LAUNCH``     | ``c2-server-ransomware-launch``     |
+-------------------------------------+-------------------------------------+
| ``C2_SERVER_RANSOMWARE_CONFIGURE``  | ``c2-server-ransomware-configure``  |
+-------------------------------------+-------------------------------------+
| ``C2_SERVER_TERMINAL_COMMAND``      | ``c2-server-terminal-command``      |
+-------------------------------------+-------------------------------------+
| ``C2_SERVER_DATA_EXFILTRATE``       | ``c2-server-data-exfiltrate``       |
+-------------------------------------+-------------------------------------+
| ``HOST_NIC_ENABLE``                 | ``host-nic-enable``                 |
+-------------------------------------+-------------------------------------+
| ``HOST_NIC_DISABLE``                | ``host-nic-disable``                |
+-------------------------------------+-------------------------------------+
| ``NODE_FILE_CORRUPT``               | ``node-file-corrupt``               |
+-------------------------------------+-------------------------------------+
| ``NODE_SESSION_REMOTE_LOGIN``       | ``node-session-remote-login``       |
+-------------------------------------+-------------------------------------+
| ``NODE_SESSION_REMOTE_LOGOFF``      | ``node-session-remote-logoff``      |
+-------------------------------------+-------------------------------------+
| ``NODE_ACCOUNT_CHANGE_PASSWORD``    | ``node-account-change-password``    |
+-------------------------------------+-------------------------------------+
| ``NODE_SEND_REMOTE_COMMAND``        | ``node-send-remote-command``        |
+-------------------------------------+-------------------------------------+


- All reward component types must be converted to kebab-case. (``SHARED_REWARD`` - ``shared-reward``)

+----------------------------------------------+----------------------------------------------+
| *3.0.0 reward type*                          | *4.0.0 reward name*                          |
+==============================================+==============================================+
| ``SHARED_REWARD``                            | ``shared-reward``                            |
+----------------------------------------------+----------------------------------------------+
| ``WEB_SERVER_404_PENALTY``                   | ``web-server-404-penalty``                   |
+----------------------------------------------+----------------------------------------------+
| ``WEBPAGE_UNAVAILABLE_PENALTY``              | ``webpage-unavailable-penalty``              |
+----------------------------------------------+----------------------------------------------+
| ``GREEN_ADMIN_DATABASE_UNREACHABLE_PENALTY`` | ``green-admin-database-unreachable-penalty`` |
+----------------------------------------------+----------------------------------------------+
| ``ACTION_PENALTY                             | ``action-penalty``                           |
+----------------------------------------------+----------------------------------------------+
| ``DATABASE_FILE_INTEGRITY``                  | ``database-file-integrity``                  |
+----------------------------------------------+----------------------------------------------+


- All agent types must be converted to kebab-case. (``ProxyAgent`` - ``proxy-agent``)

+--------------------------------+-----------------------------------+
| *3.0.0 action type*            | *4.0.0 agent type*                |
+================================+===================================+
| ``ProxyAgent``                 | ``proxy-agent``                   |
+--------------------------------+-----------------------------------+
| ``RedDatabaseCorruptingAgent`` | ``red-database-corrupting-agent`` |
+--------------------------------+-----------------------------------+
| ``ProbabilisticAgent``         | ``probabilistic-agent``           |
+--------------------------------+-----------------------------------+
| ``RandomAgent``                | ``random-agent``                  |
+--------------------------------+-----------------------------------+
| ``PeriodicAgent``              | ``periodic-agent``                |
+--------------------------------+-----------------------------------+


``simulation``
==============

The only simulation yaml changes are that all software has been renamed to use kebab-case:

+-----------------------+------------------------+
|*3.0.0 software name*  |*4.0.0 software name*   |
+=======================+========================+
| ``WebBrowser``        | ``web-browser``        |
+-----------------------+------------------------+
| ``DatabaseClient``    | ``database-client``    |
+-----------------------+------------------------+
| ``DNSClient``         | ``dns-client``         |
+-----------------------+------------------------+
| ``FTPServer``         | ``ftp-server``         |
+-----------------------+------------------------+
| ``C2Beacon``          | ``c2-beacon``          |
+-----------------------+------------------------+
| ``C2Server``          | ``c2-server``          |
+-----------------------+------------------------+
| ``RansomwareScript``  | ``ransomware-script``  |
+-----------------------+------------------------+
| ``WebServer``         | ``web-server``         |
+-----------------------+------------------------+
| ``DOSBot``            | ``dos-bot``            |
+-----------------------+------------------------+
| ``FTPClient``         | ``ftp-client``         |
+-----------------------+------------------------+
| ``DNSServer``         | ``dns-server``         |
+-----------------------+------------------------+
| ``Terminal``          | ``terminal``           |
+-----------------------+------------------------+
| ``NTPClient``         | ``ntp-client``         |
+-----------------------+------------------------+
| ``NTPServer``         | ``ntp-server``         |
+-----------------------+------------------------+
| ``NMAP``              | ``nmap``               |
+-----------------------+------------------------+
| ``HostARP``           | ``host-arp``           |
+-----------------------+------------------------+
| ``ICMP``              | ``icmp``               |
+-----------------------+------------------------+


A simple search and replace can be used with the lists above to update any configs.
