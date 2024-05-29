from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, Final, List, Optional, Tuple, Union

from prettytable import PrettyTable
from pydantic import validate_call

from primaite.simulator.core import SimComponent
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.utils.validators import IPV4Address


class PortScanPayload(SimComponent):
    """
    A class representing the payload for a port scan.

    :ivar ip_address: The target IP address for the port scan.
    :ivar port: The target port for the port scan.
    :ivar protocol: The protocol used for the port scan.
    """

    ip_address: IPV4Address
    port: Port
    protocol: IPProtocol
    request: bool = True

    def describe_state(self) -> Dict:
        """
        Describe the state of the port scan payload.

        :return: A dictionary representation of the port scan payload state.
        :rtype: Dict
        """
        state = super().describe_state()
        state["ip_address"] = str(self.ip_address)
        state["port"] = self.port.value
        state["protocol"] = self.protocol.value
        state["request"] = self.request

        return state


class NMAP(Application):
    """
    A class representing the NMAP application for network scanning.

    NMAP is a network scanning tool used to discover hosts and services on a network. It provides functionalities such
    as ping scans to discover active hosts and port scans to detect open ports on those hosts.
    """

    _active_port_scans: Dict[str, PortScanPayload] = {}
    _port_scan_responses: Dict[str, PortScanPayload] = {}

    _PORT_SCAN_TYPE_MAP: Final[Dict[Tuple[bool, bool], str]] = {
        (True, True): "Box",
        (True, False): "Horizontal",
        (False, True): "Vertical",
        (False, False): "Port",
    }

    def __init__(self, **kwargs):
        kwargs["name"] = "NMAP"
        kwargs["port"] = Port.NONE
        kwargs["protocol"] = IPProtocol.NONE
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        """
        Describe the state of the NMAP application.

        :return: A dictionary representation of the NMAP application's state.
        :rtype: Dict
        """
        return super().describe_state()

    @validate_call()
    def ping_scan(
        self,
        target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]],
        show: bool = True,
        show_online_only: bool = True,
    ) -> List[IPV4Address]:
        """
        Perform a ping scan on the target IP address(es).

        :param target_ip_address: The target IP address(es) or network(s) for the ping scan.
        :type target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]]
        :param show: Flag indicating whether to display the scan results. Defaults to True.
        :type show: bool
        :param show_online_only: Flag indicating whether to show only the online hosts. Defaults to True.
        :type show_online_only: bool

        :return: A list of active IP addresses that responded to the ping.
        :rtype: List[IPV4Address]
        """
        active_nodes = []
        if show:
            table = PrettyTable(["IP Address", "Can Ping"])
            table.align = "l"
            table.title = f"{self.software_manager.node.hostname} NMAP Ping Scan"
        if isinstance(target_ip_address, IPv4Address) or isinstance(target_ip_address, IPv4Network):
            target_ip_address = [target_ip_address]
        ip_addresses = []
        for ip_address in target_ip_address:
            if isinstance(ip_address, IPv4Network):
                ip_addresses += [
                    ip
                    for ip in ip_address.hosts()
                    if not ip == ip_address.broadcast_address and not ip == ip_address.network_address
                ]
            else:
                ip_addresses.append(ip_address)
        for ip_address in set(ip_addresses):
            can_ping = self.software_manager.icmp.ping(ip_address)
            if can_ping:
                active_nodes.append(ip_address)
            if show and (can_ping or not show_online_only):
                table.add_row([ip_address, can_ping])
        if show:
            print(table.get_string(sortby="IP Address"))
        return active_nodes

    def _determine_port_scan_type(self, target_ip_addresses: List[IPV4Address], target_ports: List[Port]) -> str:
        """
        Determine the type of port scan based on the number of target IP addresses and ports.

        :param target_ip_addresses: The list of target IP addresses.
        :type target_ip_addresses: List[IPV4Address]
        :param target_ports: The list of target ports.
        :type target_ports: List[Port]

        :return: The type of port scan.
        :rtype: str
        """
        vertical_scan = len(target_ports) > 1
        horizontal_scan = len(target_ip_addresses) > 1

        return self._PORT_SCAN_TYPE_MAP[horizontal_scan, vertical_scan]

    def _check_port_open_on_ip_address(
        self,
        ip_address: IPv4Address,
        port: Port,
        protocol: IPProtocol,
        is_re_attempt: bool = False,
        port_scan_uuid: Optional[str] = None,
    ) -> bool:
        """
        Check if a port is open on a specific IP address.

        :param ip_address: The target IP address.
        :type ip_address: IPv4Address
        :param port: The target port.
        :type port: Port
        :param protocol: The protocol used for the port scan.
        :type protocol: IPProtocol
        :param is_re_attempt: Flag indicating if this is a reattempt. Defaults to False.
        :type is_re_attempt: bool
        :param port_scan_uuid: The UUID of the port scan payload. Defaults to None.
        :type port_scan_uuid: Optional[str]

        :return: True if the port is open, False otherwise.
        :rtype: bool
        """
        # The recursive base case
        if is_re_attempt:
            # Return True if a response has been received, otherwise return False
            if port_scan_uuid in self._port_scan_responses:
                self._port_scan_responses.pop(port_scan_uuid)
                return True
            return False

        # Send the port scan request
        payload = PortScanPayload(ip_address=ip_address, port=port, protocol=protocol)
        self._active_port_scans[payload.uuid] = payload
        self.sys_log.info(
            f"{self.name}: Sending port scan request over {payload.protocol.name} on port {payload.port.value} "
            f"({payload.port.name}) to {payload.ip_address}"
        )
        self.software_manager.send_payload_to_session_manager(
            payload=payload, dest_ip_address=ip_address, src_port=port, dest_port=port, ip_protocol=protocol
        )

        # Recursively call this function with as a reattempt
        return self._check_port_open_on_ip_address(
            ip_address=ip_address, port=port, protocol=protocol, is_re_attempt=True, port_scan_uuid=payload.uuid
        )

    def _process_port_scan_response(self, payload: PortScanPayload):
        """
        Process the response to a port scan request.

        :param payload: The port scan payload received in response.
        :type payload: PortScanPayload
        """
        if payload.uuid in self._active_port_scans:
            self._active_port_scans.pop(payload.uuid)
            self._port_scan_responses[payload.uuid] = payload
            self.sys_log.info(
                f"{self.name}: Received port scan response from {payload.ip_address} on port {payload.port.value} "
                f"({payload.port.name}) over {payload.protocol.name}"
            )

    def _process_port_scan_request(self, payload: PortScanPayload, session_id: str) -> None:
        """
        Process a port scan request.

        :param payload: The port scan payload received in the request.
        :type payload: PortScanPayload
        :param session_id: The session ID for the port scan request.
        :type session_id: str
        """
        if self.software_manager.check_port_is_open(port=payload.port, protocol=payload.protocol):
            payload.request = False
            self.sys_log.info(
                f"{self.name}: Responding to port scan request for port {payload.port.value} "
                f"({payload.port.name}) over {payload.protocol.name}",
                True,
            )
            self.software_manager.send_payload_to_session_manager(payload=payload, session_id=session_id)

    @validate_call()
    def port_scan(
        self,
        target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]],
        target_protocol: Optional[Union[IPProtocol, List[IPProtocol]]] = None,
        target_port: Optional[Union[Port, List[Port]]] = None,
        show: bool = True,
    ) -> Dict[IPv4Address, Dict[IPProtocol, List[Port]]]:
        """
        Perform a port scan on the target IP address(es).

        :param target_ip_address: The target IP address(es) or network(s) for the port scan.
        :type target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]]
        :param target_protocol: The protocol(s) to use for the port scan. Defaults to None, which includes TCP and UDP.
        :type target_protocol: Optional[Union[IPProtocol, List[IPProtocol]]]
        :param target_port: The port(s) to scan. Defaults to None, which includes all valid ports.
        :type target_port: Optional[Union[Port, List[Port]]]
        :param show: Flag indicating whether to display the scan results. Defaults to True.
        :type show: bool

        :return: A dictionary mapping IP addresses to protocols and lists of open ports.
        :rtype: Dict[IPv4Address, Dict[IPProtocol, List[Port]]]
        """
        if isinstance(target_ip_address, IPv4Address) or isinstance(target_ip_address, IPv4Network):
            target_ip_address = [target_ip_address]
        ip_addresses = []
        for ip_address in target_ip_address:
            if isinstance(ip_address, IPv4Network):
                ip_addresses += [
                    ip
                    for ip in ip_address.hosts()
                    if not ip == ip_address.broadcast_address and not ip == ip_address.network_address
                ]
            else:
                ip_addresses.append(ip_address)

        if isinstance(target_port, Port):
            target_port = [target_port]
        elif target_port is None:
            target_port = [port for port in Port if port not in {Port.NONE, Port.UNUSED}]

        if isinstance(target_protocol, IPProtocol):
            target_protocol = [target_protocol]
        elif target_protocol is None:
            target_protocol = [IPProtocol.TCP, IPProtocol.UDP]

        scan_type = self._determine_port_scan_type(target_ip_address, target_port)
        active_ports = {}
        if show:
            table = PrettyTable(["IP Address", "Port", "Name", "Protocol"])
            table.align = "l"
            table.title = f"{self.software_manager.node.hostname} NMAP Port Scan ({scan_type})"
        self.sys_log.info(f"{self.name}: Starting port scan")
        for ip_address in set(ip_addresses):
            for protocol in target_protocol:
                for port in set(target_port):
                    port_open = self._check_port_open_on_ip_address(ip_address=ip_address, port=port, protocol=protocol)

                    if port_open:
                        table.add_row([ip_address, port.value, port.name, protocol.name])

                        if ip_address not in active_ports:
                            active_ports[ip_address] = dict()
                        if protocol not in active_ports[ip_address]:
                            active_ports[ip_address][protocol] = []
                        active_ports[ip_address][protocol].append(port)

        if show:
            print(table.get_string(sortby="IP Address"))

        return active_ports

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receive and process a payload.

        :param payload: The payload to be processed.
        :type payload: Any
        :param session_id: The session ID associated with the payload.
        :type session_id: str

        :return: True if the payload was successfully processed, False otherwise.
        :rtype: bool
        """
        if isinstance(payload, PortScanPayload):
            if payload.request:
                self._process_port_scan_request(payload=payload, session_id=session_id)
            else:
                self._process_port_scan_response(payload=payload)

        return True
