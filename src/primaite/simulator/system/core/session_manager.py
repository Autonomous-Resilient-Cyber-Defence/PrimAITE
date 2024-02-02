from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.core import SimComponent
from primaite.simulator.network.protocols.arp import ARPPacket
from primaite.simulator.network.protocols.icmp import ICMPPacket
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import IPPacket, IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port, TCPHeader, UDPHeader

if TYPE_CHECKING:
    from primaite.simulator.network.hardware.base import ARPCache, NIC
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

    protocol: IPProtocol
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
    :param arp_cache: A reference to the ARP cache component.
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
        if protocol == IPProtocol.TCP:
            if inbound_frame:
                src_port = frame.tcp.src_port
                dst_port = frame.tcp.dst_port
            else:
                dst_port = frame.tcp.src_port
                src_port = frame.tcp.dst_port
                with_ip_address = frame.ip.dst_ip_address
        elif protocol == IPProtocol.UDP:
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

    def resolve_outbound_nic(self, dst_ip_address: IPv4Address) -> Optional[NIC]:
        for nic in self.node.nics.values():
            if dst_ip_address in nic.ip_network and nic.enabled:
                return nic
        return self.software_manager.arp.get_default_gateway_nic()

    def resolve_outbound_transmission_details(
        self, dst_ip_address: Optional[Union[IPv4Address, IPv4Network]] = None, session_id: Optional[str] = None
    ) -> Tuple[Optional["NIC"], Optional[str], IPv4Address, Optional[IPProtocol], bool]:
        if not isinstance(dst_ip_address, (IPv4Address, IPv4Network)):
            dst_ip_address = IPv4Address(dst_ip_address)
        is_broadcast = False
        outbound_nic = None
        dst_mac_address = None
        protocol = None

        # Use session details if session_id is provided
        if session_id:
            session = self.sessions_by_uuid[session_id]
            dst_ip_address = session.with_ip_address
            protocol = session.protocol

        # Determine if the payload is for broadcast or unicast

        # Handle broadcast transmission
        if isinstance(dst_ip_address, IPv4Network):
            is_broadcast = True
            dst_ip_address = dst_ip_address.broadcast_address
            if dst_ip_address:
                # Find a suitable NIC for the broadcast
                for nic in self.node.nics.values():
                    if dst_ip_address in nic.ip_network and nic.enabled:
                        dst_mac_address = "ff:ff:ff:ff:ff:ff"
                        outbound_nic = nic
                        break
        else:
            # Resolve MAC address for unicast transmission
            use_default_gateway = True
            for nic in self.node.nics.values():
                if dst_ip_address in nic.ip_network and nic.enabled:
                    dst_mac_address = self.software_manager.arp.get_arp_cache_mac_address(dst_ip_address)
                    break

            if dst_ip_address:
                use_default_gateway = False
                outbound_nic = self.software_manager.arp.get_arp_cache_nic(dst_ip_address)

            if use_default_gateway:
                dst_mac_address = self.software_manager.arp.get_default_gateway_mac_address()
                outbound_nic = self.software_manager.arp.get_default_gateway_nic()
        return outbound_nic, dst_mac_address, dst_ip_address, protocol, is_broadcast

    def receive_payload_from_software_manager(
        self,
        payload: Any,
        dst_ip_address: Optional[Union[IPv4Address, IPv4Network]] = None,
        dst_port: Optional[Port] = None,
        session_id: Optional[str] = None,
        ip_protocol: IPProtocol = IPProtocol.TCP,
        icmp_packet: Optional[ICMPPacket] = None
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
                dst_mac_address = payload.sender_mac_addr
            outbound_nic = self.resolve_outbound_nic(payload.target_ip_address)
            is_broadcast = payload.request
            ip_protocol = IPProtocol.UDP
        else:
            vals = self.resolve_outbound_transmission_details(
                dst_ip_address=dst_ip_address, session_id=session_id
            )
            outbound_nic, dst_mac_address, dst_ip_address, protocol, is_broadcast = vals
            if protocol:
                ip_protocol = protocol

        # Check if outbound NIC and destination MAC address are resolved
        if not outbound_nic or not dst_mac_address:
            return False

        tcp_header = None
        udp_header = None
        if ip_protocol == IPProtocol.TCP:
            tcp_header = TCPHeader(
                src_port=dst_port,
                dst_port=dst_port,
            )
        elif ip_protocol == IPProtocol.UDP:
            udp_header = UDPHeader(
                src_port=dst_port,
                dst_port=dst_port,
            )
        # Construct the frame for transmission
        frame = Frame(
            ethernet=EthernetHeader(src_mac_addr=outbound_nic.mac_address, dst_mac_addr=dst_mac_address),
            ip=IPPacket(src_ip_address=outbound_nic.ip_address, dst_ip_address=dst_ip_address, protocol=ip_protocol),
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
        return outbound_nic.send_frame(frame)

    def receive_frame(self, frame: Frame, from_nic: NIC):
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
            dst_port = Port.NONE
        self.software_manager.receive_payload_from_session_manager(
            payload=frame.payload,
            port=dst_port,
            protocol=frame.ip.protocol,
            session_id=session.uuid,
            from_nic=from_nic,
            frame=frame
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
            table.add_row([session.dst_ip_address, session.dst_port.value, session.protocol.name])
        print(table)
