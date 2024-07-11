.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

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
- **Environmental Settings**: Different types of environments (e.g., urban, rural) that affect signal propagation and interference.
- **Channel Management**: Handles channels and their widths (e.g., 20 MHz, 40 MHz) to determine data transmission over different frequencies.
- **Bandwidth Management**: Tracks data transmission over channels to prevent overloading and simulate real-world network congestion.

3. AirSpace Environment Types
-----------------------------

The AirspaceEnvironmentType is a critical component that simulates different physical environments:

- Urban, Suburban, Rural, etc.
- Each type simulates different levels of electromagnetic interference and signal propagation characteristics.
- Changing the AirspaceEnvironmentType impacts data rates by affecting the signal-to-noise ratio (SNR).

4. Simulation of Environment Changes
------------------------------------

When an AirspaceEnvironmentType is set or changed, the AirSpace:

1. Recalculates the maximum data transmission capacities for all managed frequencies and channel widths.
2. Updates all wireless interfaces to reflect new capacities.

5. Managing Wireless Network Interfaces
---------------------------------------

- Interfaces can be dynamically added or removed.
- Configurations can be changed in real-time.
- The AirSpace handles data transmissions, ensuring data sent by an interface is received by all other interfaces on the same frequency and channel.

6. Signal-to-Noise Ratio (SNR) Calculation
------------------------------------------

SNR is crucial in determining the quality of a wireless communication channel:

.. math::

   SNR = \frac{\text{Signal Power}}{\text{Noise Power}}

- Impacted by environment type, frequency, and channel width
- Higher SNR indicates a clearer signal, leading to higher data transmission rates

7. Total Channel Capacity Calculation
-------------------------------------

Channel capacity is calculated using the Shannon-Hartley theorem:

.. math::

   C = B \cdot \log_2(1 + SNR)

Where:

- C: channel capacity in bits per second (bps)
- B: bandwidth of the channel in hertz (Hz)
- SNR: signal-to-noise ratio

Implementation in AirSpace:

1. Convert channel width from MHz to Hz.
2. Recalculate SNR based on new environment or interface settings.
3. Apply Shannon-Hartley theorem to determine new maximum channel capacity in Mbps.

8. Shared Maximum Capacity Across Devices
-----------------------------------------

While individual devices have theoretical maximum data rates, the actual achievable rate is often less due to:

- Shared wireless medium among all devices on the same frequency and channel width
- Interference and congestion from multiple devices transmitting simultaneously

9. AirSpace Inspection
----------------------

The AirSpace class provides methods for visualizing network behavior:

- ``show_wireless_interfaces()``: Displays current state of all interfaces
- ``show_bandwidth_load()``: Shows channel loads and bandwidth utilization
