.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

######
Switch
######

The ``switch.py`` module is a crucial component of the PrimAITE, aimed at simulating network switches within a network simulation environment. Network switches play a vital role in managing data flow within local area networks (LANs) by forwarding frames based on MAC addresses. This module provides a comprehensive framework for modelling switch operations and behaviours.

Switch Class Overview
---------------------

The module introduces the concept of switch ports through the ``SwitchPort`` class, which extends the functionality of ``WiredNetworkInterface`` to simulate the operation of switch ports in a network.

**Key Features:**

- **Data Link Layer Operation:** Operates at the data link layer (Layer 2) of the OSI model, handling the reception and forwarding of frames based on MAC addresses.
- **Port Management:** Tools for configuring switch ports, including enabling/disabling ports, setting port speeds, and managing port security features.
- **Logging and Monitoring:** Integrates with ``SysLog`` for logging operational events, aiding in debugging and
  monitoring switch behaviour.

Functionality and Implementation
---------------------------------

- **MAC Address Learning:** Dynamically learns and associates MAC addresses with switch ports, enabling intelligent frame forwarding.
- **Frame Forwarding:** Utilises the learned MAC address table to forward frames only to the specific port associated with the destination MAC address, minimising unnecessary network traffic.

The ``switch.py`` module offers a realistic and configurable representation of switch operations. By detailing the functionalities of the ``SwitchPort`` class, the module lays the foundation for simulating complex network topologies.
