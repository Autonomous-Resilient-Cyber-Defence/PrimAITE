.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

############
Network Node
############


The ``network_node.py`` module within the PrimAITE project is pivotal for simulating network nodes like routers and
switches, which are integral to network traffic management. This module establishes the framework for these devices,
enabling them to receive and process network frames effectively.

Overview
========

The module defines the ``NetworkNode`` class, an abstract base class that outlines essential behaviours for network
devices tasked with handling network traffic. It is designed to be extended by more specific device simulations that
implement these foundational capabilities.

NetworkNode Class
=================

The ``NetworkNode`` class is at the heart of the module, providing an interface for network devices that participate
in the transmission and routing of data within the simulated environment.

**Key Features:**

- **Frame Processing:** Central to the class is the ability to receive and process network frames, facilitating the
   simulation of data flow through network devices.

- **Abstract Methods:** Includes abstract methods such as ``receive_frame``, which subclasses must implement to specify
   how devices handle incoming traffic.

- **Extensibility:** Designed for extension, allowing for the creation of specific device simulations, such as router
   and switch classes, that embody unique behaviours and functionalities.


The ``network_node.py`` module's abstract approach to defining network devices allows the PrimAITE project to simulate
a wide range of network behaviours and scenarios comprehensively. By providing a common framework for all network
nodes, it facilitates the development of a modular and scalable simulation environment.
