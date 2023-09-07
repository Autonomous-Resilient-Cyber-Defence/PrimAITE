from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.core import SimComponent
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import IPPacket, IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port, TCPHeader

if TYPE_CHECKING:
    from primaite.simulator.network.hardware.base import ARPCache
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

    def __init__(self, sys_log: SysLog, arp_cache: "ARPCache"):
        self.sessions_by_key: Dict[Tuple[IPProtocol, IPv4Address, Optional[Port], Optional[Port]], Session] = {}
        self.sessions_by_uuid: Dict[str, Session] = {}
        self.sys_log: SysLog = sys_log
        self.software_manager: SoftwareManager = None  # Noqa
        self.arp_cache: "ARPCache" = arp_cache

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        pass

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

    def receive_payload_from_software_manager(
        self,
        payload: Any,
        dst_ip_address: Optional[IPv4Address] = None,
        dst_port: Optional[Port] = None,
        session_id: Optional[str] = None,
        is_reattempt: bool = False,
    ) -> Union[Any, None]:
        """
        Receive a payload from the SoftwareManager.

        If no session_id, a Session is established. Once established, the payload is sent to ``send_payload_to_nic``.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload is to originate from. Optional. If None, one will be created.
        """
        if session_id:
            session = self.sessions_by_uuid[session_id]
            dst_ip_address = self.sessions_by_uuid[session_id].with_ip_address
            dst_port = self.sessions_by_uuid[session_id].dst_port

        dst_mac_address = self.arp_cache.get_arp_cache_mac_address(dst_ip_address)

        if dst_mac_address:
            outbound_nic = self.arp_cache.get_arp_cache_nic(dst_ip_address)
        else:
            if not is_reattempt:
                self.arp_cache.send_arp_request(dst_ip_address)
                return self.receive_payload_from_software_manager(
                    payload=payload,
                    dst_ip_address=dst_ip_address,
                    dst_port=dst_port,
                    session_id=session_id,
                    is_reattempt=True,
                )
            else:
                return

        frame = Frame(
            ethernet=EthernetHeader(src_mac_addr=outbound_nic.mac_address, dst_mac_addr=dst_mac_address),
            ip=IPPacket(
                src_ip_address=outbound_nic.ip_address,
                dst_ip_address=dst_ip_address,
            ),
            tcp=TCPHeader(
                src_port=dst_port,
                dst_port=dst_port,
            ),
            payload=payload,
        )

        if not session_id:
            session_key = self._get_session_key(frame, inbound_frame=False)
            session = self.sessions_by_key.get(session_key)
            if not session:
                # Create new session
                session = Session.from_session_key(session_key)
                self.sessions_by_key[session_key] = session
                self.sessions_by_uuid[session.uuid] = session

        outbound_nic.send_frame(frame)

    def receive_frame(self, frame: Frame):
        """
        Receive a Frame.

        Extract the session key using the _get_session_key method, and forward the payload to the appropriate
        session. If the session does not exist, a new one is created.

        :param frame: The frame being received.
        """
        session_key = self._get_session_key(frame, inbound_frame=True)
        session: Session = self.sessions_by_key.get(session_key)
        if not session:
            # Create new session
            session = Session.from_session_key(session_key)
            self.sessions_by_key[session_key] = session
            self.sessions_by_uuid[session.uuid] = session
        self.software_manager.receive_payload_from_session_manager(
            payload=frame.payload, port=frame.tcp.dst_port, protocol=frame.ip.protocol, session_id=session.uuid
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
