# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""Internet Control Message Protocol."""
import secrets
from ipaddress import IPv4Address
from typing import Any, Dict, Optional, Tuple, Union

from pydantic import Field

from primaite import getLogger
from primaite.simulator.network.hardware.base import NetworkInterface
from primaite.simulator.network.protocols.icmp import ICMPPacket, ICMPType
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.system.services.service import Service
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP

_LOGGER = getLogger(__name__)


class ICMP(Service, discriminator="icmp"):
    """
    The Internet Control Message Protocol (ICMP) service.

    Enables the sending and receiving of ICMP messages such as echo requests and replies. This is typically used for
    network diagnostics, notably the ping command.
    """

    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for ICMP."""

        type: str = "icmp"

    config: "ICMP.ConfigSchema" = Field(default_factory=lambda: ICMP.ConfigSchema())

    request_replies: Dict = {}

    def __init__(self, **kwargs):
        kwargs["name"] = "icmp"
        kwargs["port"] = PORT_LOOKUP["NONE"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["ICMP"]
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        :return: Current state of this object and child objects.
        """
        return super().describe_state()

    def clear(self):
        """
        Clears the ICMP request and reply tracker.

        This is typically used to reset the state of the service, removing all tracked ICMP echo requests and their
        corresponding replies.
        """
        self.request_replies.clear()

    def ping(self, target_ip_address: Union[IPv4Address, str], pings: int = 4) -> bool:
        """
        Pings a target IP address by sending an ICMP echo request and waiting for a reply.

        :param target_ip_address: The IP address to be pinged.
        :param pings: The number of echo requests to send. Defaults to 4.
        :return: True if the ping was successful (i.e., if a reply was received for every request sent), otherwise
            False.
        """
        if not self._can_perform_action():
            return False
        if target_ip_address.is_loopback:
            self.sys_log.info("Pinging loopback address")
            return any(network_interface.enabled for network_interface in self.network_interfaces.values())
        self.sys_log.info(f"Pinging {target_ip_address}:", to_terminal=False)
        sequence, identifier = 0, None
        while sequence < pings:
            sequence, identifier = self._send_icmp_echo_request(target_ip_address, sequence, identifier, pings)
        request_replies = self.software_manager.icmp.request_replies.get(identifier)
        passed = request_replies == pings
        if request_replies:
            self.software_manager.icmp.request_replies.pop(identifier)
        else:
            request_replies = 0
        output = (
            f"Ping statistics for {target_ip_address}: "
            f"Packets: Sent = {pings}, "
            f"Received = {request_replies}, "
            f"Lost = {pings - request_replies} ({(pings - request_replies) / pings * 100}% loss)"
        )
        self.sys_log.info(output, to_terminal=False)

        return passed

    def _send_icmp_echo_request(
        self, target_ip_address: IPv4Address, sequence: int = 0, identifier: Optional[int] = None, pings: int = 4
    ) -> Tuple[int, Union[int, None]]:
        """
        Sends an ICMP echo request to a specified target IP address.

        :param target_ip_address: The target IP address for the echo request.
        :param sequence: The sequence number of the echo request.
        :param identifier: The identifier for the ICMP packet. If None, a default identifier is used.
        :param pings: The number of pings to send. Defaults to 4.
        :return: A tuple containing the next sequence number and the identifier.
        """
        network_interface = self.software_manager.session_manager.resolve_outbound_network_interface(target_ip_address)

        if not network_interface:
            self.sys_log.warning(
                "Cannot send ICMP echo request as there is no outbound Network Interface to use. Try configuring the "
                "default gateway."
            )
            return pings, None

        sequence += 1

        icmp_packet = ICMPPacket(identifier=identifier, sequence=sequence)
        payload = secrets.token_urlsafe(int(32 / 1.3))  # Standard ICMP 32 bytes size

        self.software_manager.session_manager.receive_payload_from_software_manager(
            payload=payload,
            dst_ip_address=target_ip_address,
            dst_port=self.port,
            ip_protocol=self.protocol,
            icmp_packet=icmp_packet,
        )
        return sequence, icmp_packet.identifier

    def _process_icmp_echo_request(self, frame: Frame, from_network_interface: NetworkInterface):
        """
        Processes an ICMP echo request received by the service.

        :param frame: The network frame containing the ICMP echo request.
        """
        if frame.ip.dst_ip_address != from_network_interface.ip_address:
            return
        self.sys_log.info(f"Received echo request from {frame.ip.src_ip_address}")

        network_interface = self.software_manager.session_manager.resolve_outbound_network_interface(
            frame.ip.src_ip_address
        )

        if not network_interface:
            self.sys_log.warning(
                "Cannot send ICMP echo reply as there is no outbound Network Interface to use. Try configuring the "
                "default gateway."
            )
            return

        icmp_packet = ICMPPacket(
            icmp_type=ICMPType.ECHO_REPLY,
            icmp_code=0,
            identifier=frame.icmp.identifier,
            sequence=frame.icmp.sequence + 1,
        )
        payload = secrets.token_urlsafe(int(32 / 1.3))  # Standard ICMP 32 bytes size
        self.sys_log.info(f"Sending echo reply to {frame.ip.dst_ip_address}")

        self.software_manager.session_manager.receive_payload_from_software_manager(
            payload=payload,
            dst_ip_address=frame.ip.src_ip_address,
            dst_port=self.port,
            ip_protocol=self.protocol,
            icmp_packet=icmp_packet,
        )

    def _process_icmp_echo_reply(self, frame: Frame):
        """
        Processes an ICMP echo reply received by the service, logging the reply details.

        :param frame: The network frame containing the ICMP echo reply.
        """
        time = frame.transmission_duration()
        time_str = f"{time}ms" if time > 0 else "<1ms"
        self.sys_log.info(
            f"Reply from {frame.ip.src_ip_address}: "
            f"bytes={len(frame.payload)}, "
            f"time={time_str}, "
            f"TTL={frame.ip.ttl}",
            to_terminal=False,
        )
        if not self.request_replies.get(frame.icmp.identifier):
            self.request_replies[frame.icmp.identifier] = 0
        self.request_replies[frame.icmp.identifier] += 1

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Processes received data, handling ICMP echo requests and replies.

        :param payload: The payload received.
        :param session_id: The session ID associated with the received data.
        :param kwargs: Additional keyword arguments.
        :return: True if the payload was processed successfully, otherwise False.
        """
        frame: Frame = kwargs["frame"]
        from_network_interface = kwargs["from_network_interface"]

        if not frame.icmp:
            return False

        if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
            self._process_icmp_echo_request(frame, from_network_interface)
        elif frame.icmp.icmp_type == ICMPType.ECHO_REPLY:
            self._process_icmp_echo_reply(frame)
        return True
