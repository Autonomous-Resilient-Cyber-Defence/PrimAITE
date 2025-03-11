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

However, any installed plugins that introduce new  ports or protocols are required to be set within this config as with any other base options:

.. code-block:: yaml

    game:
    max_episode_length: 128
    ports:
    - HTTP
    - POSTGRES_SERVER
    - EXAMPLE_PLUGIN_PORT
    protocols:
    - ICMP
    - TCP
    - UDP
    - EXAMPLE_PLUGIN_PROTOCOL
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
    - Action's must now be converted to camel-case:
    - Action ``options`` that previously required identifiers now instead require names.

.. code-block:: yaml

    # scan webapp service (4.0.0)
    1:
        action: node-service-scan   # camel-case
        options:
          node_name: web_server     # id's are no longer used - reference the name directly.
          service_name: web-server

    # scan webapp service (3.0.0)
    1:
        action: NODE_SERVICE_SCAN
        options:
          node_id: 1
          service_id: 0

- All reward component types must be converted to camel-case. (``SHARED_REWARD`` - ``shared-reward``)
- All agent types must be converted to camel-case. (``ProxyAgent`` - ``proxy-agent``)
- TAP agent settings are no longer set within ``tap_settings`` and settings be need a single tab dedent.
- TAP003 no longer accepts ``default_target_node`` & ``target_nodes`` as valid config options (These configuration were vestigial and ignored by TAP003).
- TAP003's ACL configuration options have been slightly altered as shown in the comments below:

.. code-block:: yaml

    # TAP003 Configuration yaml (4.0.0)
    agent_settings: # ``tap_settings`` no longer required
        start_step: 1
        frequency: 3
        variance: 0
        repeat_kill_chain: false
        repeat_kill_chain_stages: true
        default_starting_node: "example_host"
        starting_nodes:
        kill_chain:
          EXPLOIT:
            probability: 1
            malicious_acls:
            - target_router: example_target_router
              ip_address: 192.168.1.10
              position: 1
              permission: DENY
              src_ip: ALL                # source_ip_address
              src_wildcard: 0.0.255.255  # source_wildcard_mask
              dst_ip: ALL                # dest_ip_address
              dest_wildcard: 0.0.255.255 # dest_wildcard_mask
              src_port: ALL              # source_port
              dst_port: ALL              # dest_port
              protocol_name: ALL         # protocol


``simulation``
==============

The only simulation yaml changes are that all software has been renamed to use camel-case:

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


A simple search and replace can be used with the list above to update any configs.
