.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

PCAP
====

The ``packet_capture.py`` module introduces a Packet Capture (PCAP) service within PrimAITE, designed to simulate
packet capturing functionalities for the simulated network environment. This service enables the logging of network
frames as JSON strings, providing valuable insights into the data flowing across the network.

Overview
--------

Packet capture is a crucial tool in network analysis, troubleshooting, and monitoring, allowing for the examination of
packets traversing the network. Within the context of the PrimAITE simulation, the PCAP service enhances the realism
and depth of network simulations by offering detailed visibility into network communications. Notably, PCAP is created
by default at the NetworkInterface level.

PacketCapture Class
-------------------

The ``PacketCapture`` class represents the core of the PCAP service, facilitating the capture and logging of network
frames for analysis.

**Features:**

- **Automatic Creation:** PCAP is automatically created at the NetworkInterface level, simplifying setup and integration.
- **Inbound and Outbound Frame Capture:** Frames can be captured and logged separately for inbound and outbound
  traffic, offering granular insight into network communications.
- **Logging Format:** Captures and logs frames as JSON strings, ensuring that the data is structured and easily
  interpretable.
- **File Location:** PCAP logs are saved to a specified directory within the simulation output, organised by hostname
  and IP address to facilitate easy retrieval and analysis.

Usage
-----

The PCAP service is seamlessly integrated within the simulation, automatically capturing and logging frames for both
inbound and outbound traffic at the NetworkInterface level. This automatic functionality, combined with the ability
to separate traffic directions, significantly enhances network analysis and troubleshooting capabilities.

This service is particularly useful for:

- **Network Analysis:** Detailed examination of packet flows and protocols within the simulated environment.
- **Troubleshooting:** Identifying and resolving network issues by analysing packet transmissions and errors.
- **Educational Purposes:** Teaching network principles and diagnostics through hands-on packet analysis.

The introduction of the ``packet_capture.py`` module significantly enhances the network simulation capabilities of
PrimAITE. By providing a robust tool for packet capture and analysis, PrimAITE allows users to gain deeper insights
into network operations, supporting a wide range of educational, developmental, and research activities.
