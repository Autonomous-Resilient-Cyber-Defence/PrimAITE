# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, Final, List, Optional, Set, Tuple, Union

from prettytable import PrettyTable
from pydantic import validate_call

from primaite.interface.request import RequestResponse
from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.system.applications.application import Application
from primaite.utils.validation.ip_protocol import IPProtocol, is_valid_protocol, PROTOCOL_LOOKUP
from primaite.utils.validation.ipv4_address import IPV4Address
from primaite.utils.validation.port import is_valid_port, Port, PORT_LOOKUP


class PortScanPayload(SimComponent):
    """
    A class representing the payload for a port scan.

    :ivar ip_address: The target IP address for the port scan.
    :ivar port: The target port for the port scan.
    :ivar protocol: The protocol used for the port scan.
    :ivar request:Flag to indicate whether this is a request or not.
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
        state["port"] = self.port
        state["protocol"] = self.protocol
        state["request"] = self.request

        return state


class NMAP(Application, identifier="NMAP"):
    """
    A class representing the NMAP application for network scanning.

    NMAP is a network scanning tool used to discover hosts and services on a network. It provides functionalities such
    as ping scans to discover active hosts and port scans to detect open ports on those hosts.
    """

    config: "NMAP.ConfigSchema" = None

    _active_port_scans: Dict[str, PortScanPayload] = {}
    _port_scan_responses: Dict[str, PortScanPayload] = {}

    _PORT_SCAN_TYPE_MAP: Final[Dict[Tuple[bool, bool], str]] = {
        (True, True): "Box",
        (True, False): "Horizontal",
        (False, True): "Vertical",
        (False, False): "Port",
    }

    class ConfigSchema(Application.ConfigSchema):
        """ConfigSchema for NMAP."""

        type: str = "NMAP"

    def __init__(self, **kwargs):
        kwargs["name"] = "NMAP"
        kwargs["port"] = PORT_LOOKUP["NONE"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["NONE"]
        super().__init__(**kwargs)

    def _can_perform_network_action(self) -> bool:
        """
        Checks if the NMAP application can perform outbound network actions.

        This is done by checking the parent application can_per_action functionality. Then checking if there is an
        enabled NIC that can be used for outbound traffic.

        :return: True if outbound network actions can be performed, otherwise False.
        """
        if not super()._can_perform_action():
            return False

        for nic in self.software_manager.node.network_interface.values():
            if nic.enabled:
                return True
        return False

    def _init_request_manager(self) -> RequestManager:
        def _ping_scan_action(request: List[Any], context: Any) -> RequestResponse:
            results = self.ping_scan(
                target_ip_address=request[0]["target_ip_address"], show=request[0]["show"], json_serializable=True
            )
            if not self._can_perform_network_action():
                return RequestResponse.from_bool(False)
            return RequestResponse(
                status="success",
                data={"live_hosts": results},
            )

        def _port_scan_action(request: List[Any], context: Any) -> RequestResponse:
            results = self.port_scan(**request[0], json_serializable=True)
            if not self._can_perform_network_action():
                return RequestResponse.from_bool(False)
            return RequestResponse(
                status="success",
                data=results,
            )

        def _network_service_recon_action(request: List[Any], context: Any) -> RequestResponse:
            results = self.network_service_recon(**request[0], json_serializable=True)
            if not self._can_perform_network_action():
                return RequestResponse.from_bool(False)
            return RequestResponse(
                status="success",
                data=results,
            )

        rm = RequestManager()

        rm.add_request(
            name="ping_scan",
            request_type=RequestType(func=_ping_scan_action),
        )

        rm.add_request(
            name="port_scan",
            request_type=RequestType(func=_port_scan_action),
        )

        rm.add_request(
            name="network_service_recon",
            request_type=RequestType(func=_network_service_recon_action),
        )

        return rm

    def describe_state(self) -> Dict:
        """
        Describe the state of the NMAP application.

        :return: A dictionary representation of the NMAP application's state.
        :rtype: Dict
        """
        return super().describe_state()

    @staticmethod
    def _explode_ip_address_network_array(
        target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]]
    ) -> Set[IPv4Address]:
        """
        Explode a mixed array of IP addresses and networks into a set of individual IP addresses.

        This method takes a combination of single and lists of IPv4 addresses and IPv4 networks, expands any networks
        into their constituent subnet useable IP addresses, and returns a set of unique IP addresses. Broadcast and
        network addresses are excluded from the result.

        :param target_ip_address: A single or list of IPv4 addresses and networks.
        :type target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]]
        :return: A set of unique IPv4 addresses expanded from the input.
        :rtype: Set[IPv4Address]
        """
        if isinstance(target_ip_address, IPv4Address) or isinstance(target_ip_address, IPv4Network):
            target_ip_address = [target_ip_address]
        ip_addresses: List[IPV4Address] = []
        for ip_address in target_ip_address:
            if isinstance(ip_address, IPv4Network):
                ip_addresses += [
                    ip
                    for ip in ip_address.hosts()
                    if not ip == ip_address.broadcast_address and not ip == ip_address.network_address
                ]
            else:
                ip_addresses.append(ip_address)
        return set(ip_addresses)

    @validate_call()
    def ping_scan(
        self,
        target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]],
        show: bool = True,
        show_online_only: bool = True,
        json_serializable: bool = False,
    ) -> Union[List[IPV4Address], List[str]]:
        """
        Perform a ping scan on the target IP address(es).

        :param target_ip_address: The target IP address(es) or network(s) for the ping scan.
        :type target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]]
        :param show: Flag indicating whether to display the scan results. Defaults to True.
        :type show: bool
        :param show_online_only: Flag indicating whether to show only the online hosts. Defaults to True.
        :type show_online_only: bool
        :param json_serializable: Flag indicating whether the return value should be json serializable. Defaults to
            False.
        :type json_serializable: bool

        :return: A list of active IP addresses that responded to the ping.
        :rtype: Union[List[IPV4Address], List[str]]
        """
        active_nodes = []
        if show:
            table = PrettyTable(["IP Address", "Can Ping"])
            table.align = "l"
            table.title = f"{self.software_manager.node.hostname} NMAP Ping Scan"

        ip_addresses = self._explode_ip_address_network_array(target_ip_address)

        for ip_address in ip_addresses:
            # Prevent ping scan on this node
            if self.software_manager.node.ip_is_network_interface(ip_address=ip_address):
                continue
            can_ping = self.software_manager.icmp.ping(ip_address)
            if can_ping:
                active_nodes.append(ip_address if not json_serializable else str(ip_address))
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
            f"{self.name}: Sending port scan request over {payload.protocol} on port {payload.port} "
            f"({payload.port}) to {payload.ip_address}"
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
                f"{self.name}: Received port scan response from {payload.ip_address} on port {payload.port} "
                f"({payload.port}) over {payload.protocol}"
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
                f"{self.name}: Responding to port scan request for port {payload.port} "
                f"({payload.port}) over {payload.protocol}",
            )
            self.software_manager.send_payload_to_session_manager(payload=payload, session_id=session_id)

    @validate_call()
    def port_scan(
        self,
        target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]],
        target_protocol: Optional[Union[IPProtocol, List[IPProtocol]]] = None,
        target_port: Optional[Union[Port, List[Port]]] = None,
        show: bool = True,
        json_serializable: bool = False,
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
        :param json_serializable: Flag indicating whether the return value should be JSON serializable. Defaults to
            False.
        :type json_serializable: bool

        :return: A dictionary mapping IP addresses to protocols and lists of open ports.
        :rtype: Dict[IPv4Address, Dict[IPProtocol, List[Port]]]
        """
        ip_addresses = self._explode_ip_address_network_array(target_ip_address)

        if is_valid_port(target_port):
            target_port = [target_port]
        elif target_port is None:
            target_port = [PORT_LOOKUP[port] for port in PORT_LOOKUP if port not in {"NONE", "UNUSED"}]

        if is_valid_protocol(target_protocol):
            target_protocol = [target_protocol]
        elif target_protocol is None:
            target_protocol = [PROTOCOL_LOOKUP["TCP"], PROTOCOL_LOOKUP["UDP"]]

        scan_type = self._determine_port_scan_type(list(ip_addresses), target_port)
        active_ports = {}
        if show:
            table = PrettyTable(["IP Address", "Port", "Protocol"])
            table.align = "l"
            table.title = f"{self.software_manager.node.hostname} NMAP Port Scan ({scan_type})"
        self.sys_log.info(f"{self.name}: Starting port scan")
        for ip_address in ip_addresses:
            # Prevent port scan on this node
            if self.software_manager.node.ip_is_network_interface(ip_address=ip_address):
                continue
            for protocol in target_protocol:
                for port in set(target_port):
                    port_open = self._check_port_open_on_ip_address(ip_address=ip_address, port=port, protocol=protocol)
                    if port_open:
                        if show:
                            table.add_row([ip_address, port, protocol])
                        _ip_address = ip_address if not json_serializable else str(ip_address)
                        _protocol = protocol
                        _port = port
                        if _ip_address not in active_ports:
                            active_ports[_ip_address] = dict()
                        if _protocol not in active_ports[_ip_address]:
                            active_ports[_ip_address][_protocol] = []
                        active_ports[_ip_address][_protocol].append(_port)

        if show:
            print(table.get_string(sortby="IP Address"))

        return active_ports

    def network_service_recon(
        self,
        target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]],
        target_protocol: Optional[Union[IPProtocol, List[IPProtocol]]] = None,
        target_port: Optional[Union[Port, List[Port]]] = None,
        show: bool = True,
        show_online_only: bool = True,
        json_serializable: bool = False,
    ) -> Dict[IPv4Address, Dict[IPProtocol, List[Port]]]:
        """
        Perform a network service reconnaissance which includes a ping scan followed by a port scan.

        This method combines the functionalities of a ping scan and a port scan to provide a comprehensive
        overview of the services on the network. It first identifies active hosts in the target IP range by performing
        a ping scan. Once the active hosts are identified, it performs a port scan on these hosts to identify open
        ports and running services. This two-step process ensures that the port scan is performed only on live hosts,
        optimising the scanning process and providing accurate results.

        :param target_ip_address: The target IP address(es) or network(s) for the port scan.
        :type target_ip_address: Union[IPV4Address, List[IPV4Address], IPv4Network, List[IPv4Network]]
        :param target_protocol: The protocol(s) to use for the port scan. Defaults to None, which includes TCP and UDP.
        :type target_protocol: Optional[Union[IPProtocol, List[IPProtocol]]]
        :param target_port: The port(s) to scan. Defaults to None, which includes all valid ports.
        :type target_port: Optional[Union[Port, List[Port]]]
        :param show: Flag indicating whether to display the scan results. Defaults to True.
        :type show: bool
        :param show_online_only: Flag indicating whether to show only the online hosts. Defaults to True.
        :type show_online_only: bool
        :param json_serializable: Flag indicating whether the return value should be JSON serializable. Defaults to
            False.
        :type json_serializable: bool

        :return: A dictionary mapping IP addresses to protocols and lists of open ports.
        :rtype: Dict[IPv4Address, Dict[IPProtocol, List[Port]]]
        """
        ping_scan_results = self.ping_scan(
            target_ip_address=target_ip_address, show=show, show_online_only=show_online_only, json_serializable=False
        )
        return self.port_scan(
            target_ip_address=ping_scan_results,
            target_protocol=target_protocol,
            target_port=target_port,
            show=show,
            json_serializable=json_serializable,
        )

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
