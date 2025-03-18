.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _io_settings:

``io_settings``
===============
This section configures how PrimAITE saves data during simulation and training.

``io_settings`` hierarchy
-------------------------

.. code-block:: yaml

    io_settings:
        save_agent_actions: True
        save_step_metadata: False
        save_pcap_logs: False
        save_sys_logs: False
        save_agent_logs: False
        write_sys_log_to_terminal: False
        write_agent_log_to_terminal: False
        sys_log_level: WARNING
        agent_log_level: INFO


``save_agent_actions``
----------------------

Optional. Default value is ``True``.

If ``True``, this will create a JSON file each episode detailing every agent's action in each step of that episode, formatted according to the CAOS format. This includes scripted, RL, and red agents.

``save_step_metadata``
----------------------

Optional. Default value is ``False``.

If ``True``, The RL agent(s) actions, environment states and other data will be saved at every single step.


``save_pcap_logs``
------------------

Optional. Default value is ``False``.

If ``True``, then the pcap files which contain all network traffic during the simulation will be saved.


``save_sys_logs``
-----------------

Optional. Default value is ``False``.

If ``True``, then the log files which contain all node actions during the simulation will be saved.

``save_agent_logs``
-----------------

Optional. Default value is ``False``.

If ``True``, then the log files which contain all human readable agent behaviour during the simulation will be saved.

``write_sys_log_to_terminal``
-----------------------------

Optional. Default value is ``False``.

If ``True``, PrimAITE will print sys log to the terminal.

``write_agent_log_to_terminal``
-----------------------------

Optional. Default value is ``False``.

If ``True``, PrimAITE will print all human readable agent behaviour logs to the terminal.


``sys_log_level & agent_log_level``
---------------------------------

Optional. Default value is ``WARNING``.

The level of logging that should be visible in the syslog, agent logs or the logs output to the terminal.

``save_sys_logs`` or ``write_sys_log_to_terminal`` has to be set to ``True`` for this setting to be used.

This is also true for agent behaviour logging.

Available options are:

- ``DEBUG``: Debug level items and the items below
- ``INFO``: Info level items and the items below
- ``WARNING``: Warning level items and the items below
- ``ERROR``: Error level items and the items below
- ``CRITICAL``: Only critical level logs

See also |logging_levels|

.. |logging_levels| raw:: html

    <a href="https://docs.python.org/3/library/logging.html#logging-levels" target="blank">Python logging levels</a>
