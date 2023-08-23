from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from primaite.simulator.core import SimComponent
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port

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
    :param src_ip: The source IP address.
    :param dst_ip: The destination IP address.
    :param src_port: The source port number (optional).
    :param dst_port: The destination port number (optional).
    :param connected: A flag indicating whether the session is connected.
    """

    protocol: IPProtocol
    src_ip: IPv4Address
    dst_ip: IPv4Address
    src_port: Optional[Port]
    dst_port: Optional[Port]
    connected: bool = False

    @classmethod
    def from_session_key(
        cls, session_key: Tuple[IPProtocol, IPv4Address, IPv4Address, Optional[Port], Optional[Port]]
    ) -> Session:
        """
        Create a Session instance from a session key tuple.

        :param session_key: Tuple containing the session details.
        :return: A Session instance.
        """
        protocol, src_ip, dst_ip, src_port, dst_port = session_key
        return Session(protocol=protocol, src_ip=src_ip, dst_ip=dst_ip, src_port=src_port, dst_port=dst_port)

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
        self.sessions_by_key: Dict[
            Tuple[IPProtocol, IPv4Address, IPv4Address, Optional[Port], Optional[Port]], Session
        ] = {}
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
        frame: Frame, from_source: bool = True
    ) -> Tuple[IPProtocol, IPv4Address, IPv4Address, Optional[Port], Optional[Port]]:
        """
        Extracts the session key from the given frame.

        The session key is a tuple containing the following elements:
        - IPProtocol: The transport protocol (e.g. TCP, UDP, ICMP).
        - IPv4Address: The source IP address.
        - IPv4Address: The destination IP address.
        - Optional[Port]: The source port number (if applicable).
        - Optional[Port]: The destination port number (if applicable).

        :param frame: The network frame from which to extract the session key.
        :param from_source: A flag to indicate if the key should be extracted from the source or destination.
        :return: A tuple containing the session key.
        """
        protocol = frame.ip.protocol
        src_ip = frame.ip.src_ip
        dst_ip = frame.ip.dst_ip
        if protocol == IPProtocol.TCP:
            if from_source:
                src_port = frame.tcp.src_port
                dst_port = frame.tcp.dst_port
            else:
                dst_port = frame.tcp.src_port
                src_port = frame.tcp.dst_port
        elif protocol == IPProtocol.UDP:
            if from_source:
                src_port = frame.udp.src_port
                dst_port = frame.udp.dst_port
            else:
                dst_port = frame.udp.src_port
                src_port = frame.udp.dst_port
        else:
            src_port = None
            dst_port = None
        return protocol, src_ip, dst_ip, src_port, dst_port

    def receive_payload_from_software_manager(self, payload: Any, session_id: Optional[int] = None):
        """
        Receive a payload from the SoftwareManager.

        If no session_id, a Session is established. Once established, the payload is sent to ``send_payload_to_nic``.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload is to originate from. Optional. If None, one will be created.
        """
        # TODO: Implement session creation and

        self.send_payload_to_nic(payload, session_id)

    def send_payload_to_software_manager(self, payload: Any, session_id: int):
        """
        Send a payload to the software manager.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload originates from.
        """
        self.software_manager.receive_payload_from_session_manger()

    def send_payload_to_nic(self, payload: Any, session_id: int):
        """
        Send a payload across the Network.

        Takes a payload and a session_id. Builds a Frame and sends it across the network via a NIC.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload originates from
        """
        # TODO: Implement frame construction and sent to NIC.
        pass

    def receive_payload_from_nic(self, frame: Frame):
        """
        Receive a Frame from the NIC.

        Extract the session key using the _get_session_key method, and forward the payload to the appropriate
        session. If the session does not exist, a new one is created.

        :param frame: The frame being received.
        """
        session_key = self._get_session_key(frame)
        session = self.sessions_by_key.get(session_key)
        if not session:
            # Create new session
            session = Session.from_session_key(session_key)
            self.sessions_by_key[session_key] = session
            self.sessions_by_uuid[session.uuid] = session
        self.software_manager.receive_payload_from_session_manger(payload=frame, session=session)
        # TODO: Implement the frame deconstruction and send to SoftwareManager.
