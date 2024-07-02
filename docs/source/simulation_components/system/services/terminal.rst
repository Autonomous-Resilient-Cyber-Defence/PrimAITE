.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _Terminal:

Terminal
########

The ``Terminal`` provides a generic terminal simulation, by extending the base Service class

Key capabilities
================

 - Authenticates User connection by maintaining an active User account.
 - Ensures packets are matched to an existing session
 - Simulates common Terminal commands
 - Leverages the Service base class for install/uninstall, status tracking etc.


Usage
=====

 - Install on a node via the ``SoftwareManager`` to start the Terminal
 - Terminal Clients connect, execute commands and disconnect.
 - Service runs on SSH port 22 by default.
