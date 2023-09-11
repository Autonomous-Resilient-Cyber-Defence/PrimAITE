.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _internal_frame_processing:

Internal Frame Processing
=========================

Inbound
-------

At the NIC
^^^^^^^^^^
When a Frame is received on the Node's NIC:

- The NIC checks if it is enabled. If so, it will process the Frame.
- The Frame's received timestamp is set.
- The Frame is captured by the NIC's PacketCapture if configured.
- The NIC decrements the IP Packet's TTL by 1.
- The NIC calls the Node's ``receive_frame`` method, passing itself as the receiving NIC and the Frame.


At the Node
^^^^^^^^^^^

When ``receive_frame`` is called on the Node:

- The source IP address is added to the ARP cache if not already present.
- The Frame's protocol is checked:
  - If ARP or ICMP, the Frame is passed to that protocol's handler method.
  - Otherwise it is passed to the SessionManager's ``receive_frame`` method.

At the SessionManager
^^^^^^^^^^^^^^^^^^^^^

When ``receive_frame`` is called on the SessionManager:

- It extracts the key session details from the Frame:
  - Protocol (TCP, UDP, etc)
  - Source IP
  - Destination IP
  - Source Port
  - Destination Port
- It checks if an existing Session matches these details.
- If no match, a new Session is created to represent this exchange.
-  The payload and new/existing Session ID are passed to the SoftwareManager's ``receive_payload_from_session_manager`` method.

At the SoftwareManager
^^^^^^^^^^^^^^^^^^^^^^

Inside ``receive_payload_from_session_manager``:

- The SoftwareManager checks its port/protocol mapping to find which Service or Application is listening on the destination port and protocol.
- The payload and Session ID are forwarded to that receiver Service/Application instance via their ``receive`` method.
- The Service/Application can then process the payload as needed.

Outbound
--------

At the Service/Application
^^^^^^^^^^^^^^^^^^^^^^^^^^

When a Service or Application needs to send a payload:

- It calls the SoftwareManager's ``send_payload_to_session_manager`` method.
- Passes the payload, and either destination IP and destination port for new payloads, or session id for existing sessions.

At the SoftwareManager
^^^^^^^^^^^^^^^^^^^^^^

Inside ``send_payload_to_session_manager``:

- The SoftwareManager forwards the payload and details through to to the SessionManager's ``receive_payload_from_software_manager`` method.

At the SessionManager
^^^^^^^^^^^^^^^^^^^^^

When ``receive_payload_from_software_manager`` is called:

- If a Session ID was provided, it looks up the Session.
- Gets the destination MAC address by checking the ARP cache.
- If no Session ID was provided, the destination Port, IP address and Mac Address are used along with the outbound IP Address and Mac Address to create a new Session.
- Calls `send_payload_to_nic`` to construct and send the Frame.

When ``send_payload_to_nic`` is called:

- It constructs a new Frame with the payload, using the source NIC's MAC, source IP, destination MAC, etc.
- The outbound NIC is looked up via the ARP cache based on destination IP.
- The constructed Frame is passed to the outbound NIC's ``send_frame`` method.

At the NIC
^^^^^^^^^^

When ``send_frame`` is called:

- The NIC checks if it is enabled before sending.
- If enabled, it sends the Frame out to the connected Link.
