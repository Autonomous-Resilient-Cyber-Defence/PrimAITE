.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _Developer Tools:

Developer Tools
***************

PrimAITE includes developer CLI tools that are intended to be used by developers.

dev-mode
========

The dev-mode contains configuration which override any of the config files during runtime.

This is intended to make debugging easier by removing the need to find the relevant configuration file/settings.

Enabling dev-mode
-----------------

The PrimAITE dev-mode can be enabled via the use of

.. code-block::

    primaite dev-mode enable

Disabling dev-mode
------------------

The PrimAITE dev-mode can be disabled via the use of

.. code-block::

    primaite dev-mode disable

Show current mode
-----------------

To show if the dev-mode is enabled or not, use
The PrimAITE dev-mode can be disabled via the use of

.. code-block::

    primaite dev-mode show

dev-mode configuration
======================

The following configures some specific items that the dev-mode overrides, if enabled.

`--sys-log-level` or `-level`
-----------------------------

The level of system logs can be overridden by dev-mode.

By default, this is set to DEBUG

The available options for both system and agent logs are:

+-------------------+
| Log Level         |
+===================+
| DEBUG             |
+-------------------+
| INFO              |
+-------------------+
| WARNING           |
+-------------------+
| ERROR             |
+-------------------+
| CRITICAL          |
+-------------------+

.. code-block::

    primaite dev-mode config -level INFO

or

.. code-block::

    primaite dev-mode config --sys-log-level INFO


`--agent-log-level`
-------------------

The level of agent logs can be overridden by dev-mode.

By default, this is set to DEBUG.

.. code-block::

    primaite dev-mode config --agent-log-level INFO


`--output-sys-logs` or `-sys`
-----------------------------

The outputting of system logs can be overridden by dev-mode.

By default, this is set to False

Enabling system logs
""""""""""""""""""""

To enable outputting of system logs

.. code-block::

    primaite dev-mode config --output-sys-logs

or

.. code-block::

    primaite dev-mode config -sys

Disabling system logs
"""""""""""""""""""""

To disable outputting of system logs

.. code-block::

    primaite dev-mode config --no-sys-logs

or

.. code-block::

    primaite dev-mode config -nsys

Enabling agent logs
""""""""""""""""""""

To enable outputting of system logs

.. code-block::

    primaite dev-mode config --output-agent-logs

or

.. code-block::

    primaite dev-mode config -agent

Disabling system logs
"""""""""""""""""""""

To disable outputting of system logs

.. code-block::

    primaite dev-mode config --no-agent-logs

or

.. code-block::

    primaite dev-mode config -nagent

`--output-pcap-logs` or `-pcap`
-------------------------------

The outputting of packet capture logs can be overridden by dev-mode.

By default, this is set to False

Enabling PCAP logs
""""""""""""""""""

To enable outputting of packet capture logs

.. code-block::

    primaite dev-mode config --output-pcap-logs

or

.. code-block::

    primaite dev-mode config -pcap

Disabling PCAP logs
"""""""""""""""""""

To disable outputting of packet capture logs

.. code-block::

    primaite dev-mode config --no-pcap-logs

or

.. code-block::

    primaite dev-mode config -npcap

`--output-to-terminal` or `-t`
------------------------------

The outputting of system logs to the terminal can be overridden by dev-mode.

By default, this is set to False

Enabling system log output to terminal
""""""""""""""""""""""""""""""""""""""

To enable outputting of system logs to terminal

.. code-block::

    primaite dev-mode config --output-to-terminal

or

.. code-block::

    primaite dev-mode config -t

Disabling system log output to terminal
"""""""""""""""""""""""""""""""""""""""

To disable outputting of system logs to terminal

.. code-block::

    primaite dev-mode config --no-terminal

or

.. code-block::

    primaite dev-mode config -nt

path
----

PrimAITE dev-mode can override where sessions are output.

By default, PrimAITE will output the sessions in USER_HOME/primaite/sessions

With dev-mode enabled, by default, this will be changed to PRIMAITE_REPOSITORY_ROOT/sessions

However, providing a path will let dev-mode output sessions to the given path e.g.

.. code-block:: bash
    :caption: Unix

    primaite dev-mode config path ~/output/path

.. code-block:: powershell
    :caption: Windows (Powershell)

    primaite dev-mode config path ~\output\path

default path
""""""""""""

To reset the path to use the PRIMAITE_REPOSITORY_ROOT/sessions, run the command

.. code-block::

    primaite dev-mode config path --default
