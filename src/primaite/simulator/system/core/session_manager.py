# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.core import SimComponent
from primaite.simulator.network.protocols.arp import ARPPacket
from primaite.simulator.network.protocols.icmp import ICMPPacket
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import IPPacket
from primaite.simulator.network.transmission.transport_layer import TCPHeader, UDPHeader
from primaite.utils.validation.ip_protocol import IPProtocol, PROTOCOL_LOOKUP
from primaite.utils.validation.port import Port, PORT_LOOKUP

if TYPE_CHECKING:
    from primaite.simulator.network.hardware.base import NetworkInterface
    from primaite.simulator.system.core.software_manager import SoftwareManager
    from primaite.simulator.system.core.sys_log import SysLog


class Session(SimComponent):
    """
    Models a network session.

    Encapsulates information related to communication between two network endpoints, including the protocol,
    source and destination IPs and ports.

    :param protocol: The IP protocol used in the session.
    :param src_ip_address: The source IP address.
    :param dst_ip_address: The destination IP address.
    :param src_port: The source port number (optional).
    :param dst_port: The destination port number (optional).
    :param connected: A flag indicating whether the session is connected.
    """

    protocol: str
    with_ip_address: IPv4Address
    src_port: Optional[Port]
    dst_port: Optional[Port]
    connected: bool = False

    @classmethod
    def from_session_key(cls, session_key: Tuple[IPProtocol, IPv4Address, Optional[Port], Optional[Port]]) -> Session:
        """
        Create a Session instance from a session key tuple.

        :param session_key: Tuple containing the session details.
        :return: A Session instance.
        """
        protocol, with_ip_address, src_port, dst_port = session_key
        return Session(
            protocol=protocol,
            with_ip_address=with_ip_address,
            src_port=src_port,
            dst_port=dst_port,
        )

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        pass


class SessionManager:
    """
    Manages network sessions, including session creation, lookup, and communication with other components.

    :param sys_log: A reference to the system log component.
    """

    def __init__(self, sys_log: SysLog):
        self.sessions_by_key: Dict[
            Tuple[IPProtocol, IPv4Address, IPv4Address, Optional[Port], Optional[Port]], Session
        ] = {}
        self.sessions_by_uuid: Dict[str, Session] = {}
        self.sys_log: SysLog = sys_log
        self.software_manager: SoftwareManager = None  # Noqa
        self.node: Node = None  # noqa

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        pass

    def clear(self):
        """Clears the sessions."""
        self.sessions_by_key.clear()
        self.sessions_by_uuid.clear()

    @staticmethod
    def _get_session_key(
        frame: Frame, inbound_frame: bool = True
    ) -> Tuple[IPProtocol, IPv4Address, Optional[Port], Optional[Port]]:
        """
        Extracts the session key from the given frame.

        The session key is a tuple containing the following elements:
        - IPProtocol: The transport protocol (e.g. TCP, UDP, ICMP).
        - IPv4Address: The source IP address.
        - IPv4Address: The destination IP address.
        - Optional[Port]: The source port number (if applicable).
        - Optional[Port]: The destination port number (if applicable).

        :param frame: The network frame from which to extract the session key.
        :return: A tuple containing the session key.
        """
        protocol = frame.ip.protocol
        with_ip_address = frame.ip.src_ip_address
        if protocol == PROTOCOL_LOOKUP["TCP"]:
            if inbound_frame:
                src_port = frame.tcp.src_port
                dst_port = frame.tcp.dst_port
            else:
                dst_port = frame.tcp.src_port
                src_port = frame.tcp.dst_port
                with_ip_address = frame.ip.dst_ip_address
        elif protocol == PROTOCOL_LOOKUP["UDP"]:
            if inbound_frame:
                src_port = frame.udp.src_port
                dst_port = frame.udp.dst_port
            else:
                dst_port = frame.udp.src_port
                src_port = frame.udp.dst_port
                with_ip_address = frame.ip.dst_ip_address
        else:
            src_port = None
            dst_port = None
        return protocol, with_ip_address, src_port, dst_port

    def resolve_outbound_network_interface(self, dst_ip_address: IPv4Address) -> Optional["NetworkInterface"]:
        """
        Resolves the appropriate outbound network interface for a given destination IP address.

        This method determines the most suitable network interface for sending a packet to the specified
        destination IP address. It considers only enabled network interfaces and checks if the destination
        IP address falls within the subnet of each interface. If no suitable local network interface is found,
        the method defaults to using the network interface associated with the default gateway.

        The search process prioritises local network interfaces based on the IP network to which they belong.
        If the destination IP address does not match any local subnet, the method assumes that the destination
        is outside the local network and hence, routes the packet through the default gateway's network interface.

        :param dst_ip_address: The destination IP address for which the outbound interface is to be resolved.
        :type dst_ip_address: IPv4Address
        :return: The network interface through which the packet should be sent to reach the destination IP address,
            or the default gateway's network interface if the destination is not within any local subnet.
        :rtype: Optional["NetworkInterface"]
        """
        for network_interface in self.node.network_interfaces.values():
            if dst_ip_address in network_interface.ip_network and network_interface.enabled:
                return network_interface
        return self.software_manager.arp.get_default_gateway_network_interface()

    def resolve_outbound_transmission_details(
        self,
        dst_ip_address: Optional[Union[IPv4Address, IPv4Network]] = None,
        src_port: Optional[Port] = None,
        dst_port: Optional[Port] = None,
        protocol: Optional[IPProtocol] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[
        Optional["NetworkInterface"],
        Optional[str],
        IPv4Address,
        Optional[Port],
        Optional[Port],
        Optional[IPProtocol],
        bool,
    ]:
        """
        Resolves the necessary details for outbound transmission based on the provided parameters.

        This method determines whether the payload should be broadcast or unicast based on the destination IP address
        and resolves the outbound network interface and destination MAC address accordingly.

        The method first checks if `session_id` is provided and uses the session details if available. For broadcast
        transmissions, it finds a suitable network interface and uses a broadcast MAC address. For unicast
        transmissions, it attempts to resolve the destination MAC address using ARP and finds the appropriate
        outbound network interface. If the destination IP address is outside the local network and no specific MAC
        address is resolved, it uses the default gateway for the transmission.

        :param dst_ip_address: The destination IP address or network. If an IPv4Network is provided, the method
            treats the transmission as a broadcast to that network. Optional.
        :type dst_ip_address: Optional[Union[IPv4Address, IPv4Network]]
        :param src_port: The source port number for the transmission. Optional.
        :type src_port: Optional[Port]
        :param dst_port: The destination port number for the transmission. Optional.
        :type dst_port: Optional[Port]
        :param protocol: The IP protocol to be used for the transmission. Optional.
        :type protocol: Optional[IPProtocol]
        :param session_id: The session ID associated with the transmission. If provided, the session details override
            other parameters. Optional.
        :type session_id: Optional[str]
        :return: A tuple containing the resolved outbound network interface, destination MAC address, destination IP
            address, source port, destination port, protocol, and a boolean indicating whether the transmission is a
            broadcast.
        :rtype: Tuple[Optional["NetworkInterface"], Optional[str], IPv4Address, Optional[Port], Optional[Port],
            Optional[IPProtocol], bool]
        """
        if dst_ip_address and not isinstance(dst_ip_address, (IPv4Address, IPv4Network)):
            dst_ip_address = IPv4Address(dst_ip_address)
        is_broadcast = False
        outbound_network_interface = None
        dst_mac_address = None

        # Use session details if session_id is provided
        if session_id:
            session = self.sessions_by_uuid[session_id]

            dst_ip_address = session.with_ip_address
            protocol = session.protocol
            src_port = session.src_port
            dst_port = session.dst_port

        # Determine if the payload is for broadcast or unicast

        # Handle broadcast transmission
        if isinstance(dst_ip_address, IPv4Network):
            is_broadcast = True
            dst_ip_address = dst_ip_address.broadcast_address
            if dst_ip_address:
                # Find a suitable NIC for the broadcast
                for network_interface in self.node.network_interfaces.values():
                    if dst_ip_address in network_interface.ip_network and network_interface.enabled:
                        dst_mac_address = "ff:ff:ff:ff:ff:ff"
                        outbound_network_interface = network_interface
                        break
        else:
            # Resolve MAC address for unicast transmission
            use_default_gateway = True
            for network_interface in self.node.network_interfaces.values():
                if dst_ip_address in network_interface.ip_network and network_interface.enabled:
                    dst_mac_address = self.software_manager.arp.get_arp_cache_mac_address(dst_ip_address)
                    break

            if dst_mac_address:
                use_default_gateway = False
                outbound_network_interface = self.software_manager.arp.get_arp_cache_network_interface(dst_ip_address)

            if use_default_gateway:
                dst_mac_address = self.software_manager.arp.get_default_gateway_mac_address()
                outbound_network_interface = self.software_manager.arp.get_default_gateway_network_interface()
        return outbound_network_interface, dst_mac_address, dst_ip_address, src_port, dst_port, protocol, is_broadcast

    def receive_payload_from_software_manager(
        self,
        payload: Any,
        dst_ip_address: Optional[Union[IPv4Address, IPv4Network]] = None,
        src_port: Optional[Port] = None,
        dst_port: Optional[Port] = None,
        session_id: Optional[str] = None,
        ip_protocol: IPProtocol = PROTOCOL_LOOKUP["TCP"],
        icmp_packet: Optional[ICMPPacket] = None,
    ) -> Union[Any, None]:
        """
        Receive a payload from the SoftwareManager and send it to the appropriate NIC for transmission.

        This method supports both unicast and Layer 3 broadcast transmissions. If `dst_ip_address` is an
        IPv4Network, a broadcast is initiated. For unicast, the destination MAC address is resolved via ARP.
        A new session is established if `session_id` is not provided, and an existing session is used otherwise.

        :param payload: The payload to be sent.
        :param dst_ip_address: The destination IP address or network for broadcast. Optional.
        :param dst_port: The destination port for the TCP packet. Optional.
        :param session_id: The Session ID from which the payload originates. Optional.
        :return: The outcome of sending the frame, or None if sending was unsuccessful.
        """
        if isinstance(payload, ARPPacket):
            # ARP requests need to be handles differently
            if payload.request:
                dst_mac_address = "ff:ff:ff:ff:ff:ff"
            else:
                dst_mac_address = payload.target_mac_addr
            outbound_network_interface = self.resolve_outbound_network_interface(payload.target_ip_address)
            is_broadcast = payload.request
            ip_protocol = PROTOCOL_LOOKUP["UDP"]
        else:
            vals = self.resolve_outbound_transmission_details(
                dst_ip_address=dst_ip_address,
                src_port=src_port,
                dst_port=dst_port,
                protocol=ip_protocol,
                session_id=session_id,
            )
            (
                outbound_network_interface,
                dst_mac_address,
                dst_ip_address,
                src_port,
                dst_port,
                protocol,
                is_broadcast,
            ) = vals
            if protocol:
                ip_protocol = protocol

        # Check if outbound NIC and destination MAC address are resolved
        if not outbound_network_interface or not dst_mac_address:
            return False

        if src_port is None and dst_port is None:
            raise ValueError(
                "Failed to resolve src or dst port. Have you sent the port from the service or application?"
            )

        tcp_header = None
        udp_header = None
        if ip_protocol == PROTOCOL_LOOKUP["TCP"]:
            tcp_header = TCPHeader(
                src_port=dst_port,
                dst_port=dst_port,
            )
        elif ip_protocol == PROTOCOL_LOOKUP["UDP"]:
            udp_header = UDPHeader(
                src_port=dst_port,
                dst_port=dst_port,
            )
        # TODO: Only create IP packet if not ARP
        # ip_packet = None
        # if dst_port != Port["ARP"]:
        #     IPPacket(
        #         src_ip_address=outbound_network_interface.ip_address,
        #         dst_ip_address=dst_ip_address,
        #         protocol=ip_protocol
        #     )
        # Construct the frame for transmission
        frame = Frame(
            ethernet=EthernetHeader(src_mac_addr=outbound_network_interface.mac_address, dst_mac_addr=dst_mac_address),
            ip=IPPacket(
                src_ip_address=outbound_network_interface.ip_address,
                dst_ip_address=dst_ip_address,
                protocol=ip_protocol,
            ),
            tcp=tcp_header,
            udp=udp_header,
            icmp=icmp_packet,
            payload=payload,
        )

        # Manage session for unicast transmission
        # TODO: Only create sessions for TCP
        if not (is_broadcast and session_id):
            session_key = self._get_session_key(frame, inbound_frame=False)
            session = self.sessions_by_key.get(session_key)
            if not session:
                # Create a new session if it doesn't exist
                session = Session.from_session_key(session_key)
                self.sessions_by_key[session_key] = session
                self.sessions_by_uuid[session.uuid] = session

        # Send the frame through the NIC
        return outbound_network_interface.send_frame(frame)

    def receive_frame(self, frame: Frame, from_network_interface: "NetworkInterface"):
        """
        Receive a Frame.

        Extract the session key using the _get_session_key method, and forward the payload to the appropriate
        session. If the session does not exist, a new one is created.

        :param frame: The frame being received.
        """
        # TODO: Only create sessions for TCP
        session_key = self._get_session_key(frame, inbound_frame=True)
        session: Session = self.sessions_by_key.get(session_key)
        if not session:
            # Create new session
            session = Session.from_session_key(session_key)
            self.sessions_by_key[session_key] = session
            self.sessions_by_uuid[session.uuid] = session
        dst_port = None
        if frame.tcp:
            dst_port = frame.tcp.dst_port
        elif frame.udp:
            dst_port = frame.udp.dst_port
        elif frame.icmp:
            dst_port = PORT_LOOKUP["NONE"]
        self.software_manager.receive_payload_from_session_manager(
            payload=frame.payload,
            port=dst_port,
            protocol=frame.ip.protocol,
            session_id=session.uuid,
            from_network_interface=from_network_interface,
            frame=frame,
        )

    def show(self, markdown: bool = False):
        """
        Print tables describing the SessionManager.

        Generate and print PrettyTable instances that show details about
        session's destination IP Address, destination Ports and the protocol to use.
        Output can be in Markdown format.

        :param markdown: Use Markdown style in table output. Defaults to False.
        """
        table = PrettyTable(["Destination IP", "Port", "Protocol"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} Session Manager"
        for session in self.sessions_by_key.values():
            table.add_row([session.dst_ip_address, session.dst_port, session.protocol])
        print(table)
