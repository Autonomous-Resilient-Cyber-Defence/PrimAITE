.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _airspace:

AirSpace
========


1. Introduction
---------------

The AirSpace class is the central component for wireless networks in PrimAITE and is designed to model and manage the behavior and interactions of wireless network interfaces within a simulated wireless network environment. This documentation provides a detailed overview of the AirSpace class, its components, and how they interact to create a realistic simulation of wireless network dynamics.

2. Overview of the AirSpace System
----------------------------------

The AirSpace is a virtual representation of a physical wireless environment, managing multiple wireless network interfaces that simulate devices connected to the wireless network. These interfaces communicate over radio frequencies, with their interactions influenced by various factors modeled within the AirSpace.

2.1 Key Components
^^^^^^^^^^^^^^^^^^

- **Wireless Network Interfaces**: Representations of network interfaces connected physical devices like routers, computers, or IoT devices that can send and receive data wirelessly.
- **Bandwidth Management**: Tracks data transmission over frequencies to prevent overloading and simulate real-world network congestion.


3. Managing Wireless Network Interfaces
---------------------------------------

- Interfaces can be dynamically added or removed.
- Configurations can be changed in real-time.
- The AirSpace handles data transmissions, ensuring data sent by an interface is received by all other interfaces on the same frequency.


4. AirSpace Inspection
----------------------

The AirSpace class provides methods for visualizing network behavior:

- ``show_wireless_interfaces()``: Displays current state of all interfaces
- ``show_bandwidth_load()``: Shows bandwidth utilisation
