.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

SysLog
======

The ``sys_log.py`` module introduces a system logging (SysLog) service within PrimAITE, designed to facilitate the
management and recording of system logs for nodes in the simulated network environment. This essential service tracks
system events, assists in debugging, and aids network analysis by providing a structured and accessible log of
activities.

Overview
--------

System logging is vital in network management and diagnostics, offering a timestamped record of events within network
devices. In the PrimAITE simulation context, the SysLog service automatically enables logging at the node level,
enhancing the simulation's analysis and troubleshooting capabilities without manual configuration.

SysLog Class
------------

**Features:**

- **Automatic Activation:** SysLog is enabled by default at the node level, ensuring comprehensive activity logging
  with no additional setup.
- **Log Levels:** Supports various logging levels, including debug, info, error, etc., allowing for detailed
  categorisation and severity indication of log messages.
- **Terminal Output:** Logs can be printed to the terminal by setting `to_terminal=True`, offering real-time monitoring
  and debugging capabilities.
- **Logging Format:** Records system logs in standard text format for enhanced readability and interpretability.
- **File Location:** Systematically saves logs to a designated directory within the simulation output, organised by
  hostname, facilitating log management and retrieval.

Usage
-----

SysLog service is seamlessly integrated into the simulation, with automatic activation for each node and support for
various logging levels. The addition of terminal output capabilities further enhances the utility of SysLog for
real-time event monitoring and troubleshooting.

This service is invaluable for:

- **Event Tracking:** Documents key system events, configuration changes, and operational status updates.
- **Debugging:** Aids in identifying and resolving simulated network issues by providing a comprehensive event history.
- **Network Analysis:** Offers insights into network node behaviour and interactions.


The ``sys_log.py`` module significantly enhances PrimAITE's network simulation capabilities. Providing a robust system
logging tool, automatically enabled at the node level and featuring various log levels and terminal output options,
PrimAITE enables users to conduct in-depth network simulations.
