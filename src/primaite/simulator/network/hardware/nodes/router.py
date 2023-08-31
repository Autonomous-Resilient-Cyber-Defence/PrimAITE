from __future__ import annotations

from enum import Enum
from ipaddress import IPv4Address, IPv4Network
from typing import Dict, List, Optional, Tuple, Union

from prettytable import PrettyTable

from primaite.simulator.core import SimComponent
from primaite.simulator.network.hardware.base import ARPCache, ICMP, NIC, Node
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import ICMPPacket, ICMPType, IPPacket, IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port, TCPHeader
from primaite.simulator.system.core.sys_log import SysLog


class ACLAction(Enum):
    """Enum for defining the ACL action types."""

    DENY = 0
    PERMIT = 1


class ACLRule(SimComponent):
    def describe_state(self) -> Dict:
        pass

    action: ACLAction = ACLAction.DENY
    protocol: Optional[IPProtocol] = None
    src_ip: Optional[IPv4Address] = None
    src_port: Optional[Port] = None
    dst_ip: Optional[IPv4Address] = None
    dst_port: Optional[Port] = None

    def __str__(self) -> str:
        rule_strings = []
        for key, value in self.model_dump(exclude={"uuid", "action_manager"}).items():
            if value is None:
                value = "ANY"
            if isinstance(value, Enum):
                rule_strings.append(f"{key}={value.name}")
            else:
                rule_strings.append(f"{key}={value}")
        return ", ".join(rule_strings)


class AccessControlList(SimComponent):
    sys_log: SysLog
    implicit_action: ACLAction
    implicit_rule: ACLRule
    max_acl_rules: int = 25
    _acl: List[Optional[ACLRule]] = [None] * 24

    def __init__(self, **kwargs) -> None:
        if not kwargs.get("implicit_action"):
            kwargs["implicit_action"] = ACLAction.DENY
        if not kwargs.get("max_acl_rules"):
            kwargs["max_acl_rules"] = 25
        kwargs["implicit_rule"] = ACLRule(action=kwargs["implicit_action"])
        kwargs["_acl"] = [None] * (kwargs["max_acl_rules"] - 1)

        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        pass

    @property
    def acl(self) -> List[Optional[ACLRule]]:
        return self._acl

    def add_rule(
            self,
            action: ACLAction,
            protocol: Optional[IPProtocol] = None,
            src_ip: Optional[Union[str, IPv4Address]] = None,
            src_port: Optional[Port] = None,
            dst_ip: Optional[Union[str, IPv4Address]] = None,
            dst_port: Optional[Port] = None,
            position: int = 0,
    ) -> None:
        if isinstance(src_ip, str):
            src_ip = IPv4Address(src_ip)
        if isinstance(dst_ip, str):
            dst_ip = IPv4Address(dst_ip)
        if 0 <= position < self.max_acl_rules:
            self._acl[position] = ACLRule(
                action=action, src_ip=src_ip, dst_ip=dst_ip, protocol=protocol, src_port=src_port, dst_port=dst_port
            )
        else:
            raise ValueError(f"Position {position} is out of bounds.")

    def remove_rule(self, position: int) -> None:
        if 0 <= position < self.max_acl_rules:
            self._acl[position] = None
        else:
            raise ValueError(f"Position {position} is out of bounds.")

    def is_permitted(
            self,
            protocol: IPProtocol,
            src_ip: Union[str, IPv4Address],
            src_port: Optional[Port],
            dst_ip: Union[str, IPv4Address],
            dst_port: Optional[Port],
    ) -> Tuple[bool, Optional[Union[str, ACLRule]]]:
        if not isinstance(src_ip, IPv4Address):
            src_ip = IPv4Address(src_ip)
        if not isinstance(dst_ip, IPv4Address):
            dst_ip = IPv4Address(dst_ip)
        for rule in self._acl:
            if not rule:
                continue

            if (
                    (rule.src_ip == src_ip or rule.src_ip is None)
                    and (rule.dst_ip == dst_ip or rule.dst_ip is None)
                    and (rule.protocol == protocol or rule.protocol is None)
                    and (rule.src_port == src_port or rule.src_port is None)
                    and (rule.dst_port == dst_port or rule.dst_port is None)
            ):
                return rule.action == ACLAction.PERMIT, rule

        return self.implicit_action == ACLAction.PERMIT, f"Implicit {self.implicit_action.name}"

    def get_relevant_rules(
            self,
            protocol: IPProtocol,
            src_ip: Union[str, IPv4Address],
            src_port: Port,
            dst_ip: Union[str, IPv4Address],
            dst_port: Port,
    ) -> List[ACLRule]:
        if not isinstance(src_ip, IPv4Address):
            src_ip = IPv4Address(src_ip)
        if not isinstance(dst_ip, IPv4Address):
            dst_ip = IPv4Address(dst_ip)
        relevant_rules = []
        for rule in self._acl:
            if rule is None:
                continue

            if (
                    (rule.src_ip == src_ip or rule.src_ip is None)
                    or (rule.dst_ip == dst_ip or rule.dst_ip is None)
                    or (rule.protocol == protocol or rule.protocol is None)
                    or (rule.src_port == src_port or rule.src_port is None)
                    or (rule.dst_port == dst_port or rule.dst_port is None)
            ):
                relevant_rules.append(rule)

        return relevant_rules

    def show(self):
        """Prints a table of the routes in the RouteTable."""
        """
            action: ACLAction
    protocol: Optional[IPProtocol]
    src_ip: Optional[IPv4Address]
    src_port: Optional[Port]
    dst_ip: Optional[IPv4Address]
    dst_port: Optional[Port]
    """
        table = PrettyTable(["Index", "Action", "Protocol", "Src IP", "Src Port", "Dst IP", "Dst Port"])
        table.title = f"{self.sys_log.hostname} Access Control List"
        for index, rule in enumerate(self.acl + [self.implicit_rule]):
            if rule:
                table.add_row(
                    [
                        index,
                        rule.action.name if rule.action else "ANY",
                        rule.protocol.name if rule.protocol else "ANY",
                        rule.src_ip if rule.src_ip else "ANY",
                        f"{rule.src_port.value} ({rule.src_port.name})" if rule.src_port else "ANY",
                        rule.dst_ip if rule.dst_ip else "ANY",
                        f"{rule.dst_port.value} ({rule.dst_port.name})" if rule.dst_port else "ANY",
                    ]
                )
        print(table)


class RouteEntry(SimComponent):
    """
    Represents a single entry in a routing table.

    Attributes:
        address (IPv4Address): The destination IP address or network address.
        subnet_mask (IPv4Address): The subnet mask for the network.
        next_hop (IPv4Address): The next hop IP address to which packets should be forwarded.
        metric (int): The cost metric for this route. Default is 0.0.

    Example:
        >>> entry = RouteEntry(
        ...     IPv4Address("192.168.1.0"),
        ...     IPv4Address("255.255.255.0"),
        ...     IPv4Address("192.168.2.1"),
        ...     metric=5
        ... )
    """

    address: IPv4Address
    "The destination IP address or network address."
    subnet_mask: IPv4Address
    "The subnet mask for the network."
    next_hop: IPv4Address
    "The next hop IP address to which packets should be forwarded."
    metric: float = 0.0
    "The cost metric for this route. Default is 0.0."

    def __init__(self, **kwargs):
        for key in {"address", "subnet_mask", "next_hop"}:
            if not isinstance(kwargs[key], IPv4Address):
                kwargs[key] = IPv4Address(kwargs[key])
        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        pass


class RouteTable(SimComponent):
    """
    Represents a routing table holding multiple route entries.

    Attributes:
        routes (List[RouteEntry]): A list of RouteEntry objects.

    Methods:
        add_route: Add a route to the routing table.
        find_best_route: Find the best route for a given destination IP.

    Example:
        >>> rt = RouteTable()
        >>> rt.add_route(
        ...     RouteEntry(
        ...         IPv4Address("192.168.1.0"),
        ...         IPv4Address("255.255.255.0"),
        ...         IPv4Address("192.168.2.1"),
        ...         metric=5
        ...     )
        ... )
        >>> best_route = rt.find_best_route(IPv4Address("192.168.1.34"))
    """

    routes: List[RouteEntry] = []
    sys_log: SysLog

    def describe_state(self) -> Dict:
        pass

    def add_route(
            self,
            address: Union[IPv4Address, str],
            subnet_mask: Union[IPv4Address, str],
            next_hop: Union[IPv4Address, str],
            metric: float = 0.0,
    ):
        """Add a route to the routing table.

        :param route: A RouteEntry object representing the route.
        """
        for key in {address, subnet_mask, next_hop}:
            if not isinstance(key, IPv4Address):
                key = IPv4Address(key)
        route = RouteEntry(address=address, subnet_mask=subnet_mask, next_hop=next_hop, metric=metric)
        self.routes.append(route)

    def find_best_route(self, destination_ip: Union[str, IPv4Address]) -> Optional[RouteEntry]:
        """
        Find the best route for a given destination IP.

        :param destination_ip: The destination IPv4Address to find the route for.
        :return: The best matching RouteEntry, or None if no route matches.

        The algorithm uses Longest Prefix Match and considers metrics to find the best route.
        """
        if not isinstance(destination_ip, IPv4Address):
            destination_ip = IPv4Address(destination_ip)
        best_route = None
        longest_prefix = -1
        lowest_metric = float("inf")  # Initialise at infinity as any other number we compare to it will be smaller

        for route in self.routes:
            route_network = IPv4Network(f"{route.address}/{route.subnet_mask}", strict=False)
            prefix_len = route_network.prefixlen

            if destination_ip in route_network:
                if prefix_len > longest_prefix or (prefix_len == longest_prefix and route.metric < lowest_metric):
                    best_route = route
                    longest_prefix = prefix_len
                    lowest_metric = route.metric

        return best_route

    def show(self):
        """Prints a table of the routes in the RouteTable."""
        table = PrettyTable(["Index", "Address", "Next Hop", "Metric"])
        table.title = f"{self.sys_log.hostname} Route Table"
        for index, route in enumerate(self.routes):
            network = IPv4Network(f"{route.address}/{route.subnet_mask}")
            table.add_row([index, f"{route.address}/{network.prefixlen}", route.next_hop, route.metric])
        print(table)


class RouterARPCache(ARPCache):
    def __init__(self, sys_log: SysLog, router: Router):
        super().__init__(sys_log)
        self.router: Router = router

    def process_arp_packet(self, from_nic: NIC, frame: Frame):
        """
        Overridden method to process a received ARP packet in a router-specific way.

        :param from_nic: The NIC that received the ARP packet.
        :param frame: The original arp frame.
        """
        arp_packet = frame.arp

        # ARP Reply
        if not arp_packet.request:
            for nic in self.router.nics.values():
                if arp_packet.target_ip == nic.ip_address:
                    # reply to the Router specifically
                    self.sys_log.info(
                        f"Received ARP response for {arp_packet.sender_ip} from {arp_packet.sender_mac_addr} via NIC {from_nic}"
                    )
                    self.add_arp_cache_entry(
                        ip_address=arp_packet.sender_ip,
                        mac_address=arp_packet.sender_mac_addr,
                        nic=from_nic,
                    )
                    return

            # Reply for a connected requested
            nic = self.get_arp_cache_nic(arp_packet.target_ip)
            if nic:
                self.sys_log.info(f"Forwarding arp reply for {arp_packet.target_ip}, from {arp_packet.sender_ip}")
                arp_packet.sender_mac_addr = nic.mac_address
                frame.decrement_ttl()
                nic.send_frame(frame)

        # ARP Request
        self.sys_log.info(
            f"Received ARP request for {arp_packet.target_ip} from "
            f"{arp_packet.sender_mac_addr}/{arp_packet.sender_ip} "
        )
        # Matched ARP request
        self.add_arp_cache_entry(ip_address=arp_packet.sender_ip, mac_address=arp_packet.sender_mac_addr, nic=from_nic)
        arp_packet = arp_packet.generate_reply(from_nic.mac_address)
        self.send_arp_reply(arp_packet, from_nic)

        # If the target IP matches one of the router's NICs
        for nic in self.nics.values():
            if nic.enabled and nic.ip_address == arp_packet.target_ip:
                arp_reply = arp_packet.generate_reply(from_nic.mac_address)
                self.send_arp_reply(arp_reply, from_nic)
                return


class RouterICMP(ICMP):
    router: Router

    def __init__(self, sys_log: SysLog, arp_cache: ARPCache, router: Router):
        super().__init__(sys_log, arp_cache)
        self.router = router

    def process_icmp(self, frame: Frame, from_nic: NIC, is_reattempt: bool = False):
        if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
            # determine if request is for router interface or whether it needs to be routed

            for nic in self.router.nics.values():
                if nic.ip_address == frame.ip.dst_ip:
                    if nic.enabled:
                        # reply to the request
                        if not is_reattempt:
                            self.sys_log.info(f"Received echo request from {frame.ip.src_ip}")
                        target_mac_address = self.arp.get_arp_cache_mac_address(frame.ip.src_ip)
                        src_nic = self.arp.get_arp_cache_nic(frame.ip.src_ip)
                        tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

                        # Network Layer
                        ip_packet = IPPacket(src_ip=nic.ip_address, dst_ip=frame.ip.src_ip, protocol=IPProtocol.ICMP)
                        # Data Link Layer
                        ethernet_header = EthernetHeader(src_mac_addr=src_nic.mac_address, dst_mac_addr=target_mac_address)
                        icmp_reply_packet = ICMPPacket(
                            icmp_type=ICMPType.ECHO_REPLY,
                            icmp_code=0,
                            identifier=frame.icmp.identifier,
                            sequence=frame.icmp.sequence + 1,
                        )
                        frame = Frame(ethernet=ethernet_header, ip=ip_packet, tcp=tcp_header, icmp=icmp_reply_packet)
                        self.sys_log.info(f"Sending echo reply to {frame.ip.dst_ip}")

                        src_nic.send_frame(frame)
                    return

            # Route the frame
            self.router.route_frame(frame, from_nic)

        elif frame.icmp.icmp_type == ICMPType.ECHO_REPLY:
            for nic in self.router.nics.values():
                if nic.ip_address == frame.ip.dst_ip:
                    if nic.enabled:
                        self.sys_log.info(f"Received echo reply from {frame.ip.src_ip}")
                        if not self.request_replies.get(frame.icmp.identifier):
                            self.request_replies[frame.icmp.identifier] = 0
                        self.request_replies[frame.icmp.identifier] += 1

                    return
            # Route the frame
            self.router.route_frame(frame, from_nic)


class Router(Node):
    num_ports: int
    ethernet_ports: Dict[int, NIC] = {}
    acl: AccessControlList
    route_table: RouteTable
    arp: RouterARPCache
    icmp: RouterICMP

    def __init__(self, hostname: str, num_ports: int = 5, **kwargs):
        if not kwargs.get("sys_log"):
            kwargs["sys_log"] = SysLog(hostname)
        if not kwargs.get("acl"):
            kwargs["acl"] = AccessControlList(sys_log=kwargs["sys_log"], implicit_action=ACLAction.DENY)
        if not kwargs.get("route_table"):
            kwargs["route_table"] = RouteTable(sys_log=kwargs["sys_log"])
        if not kwargs.get("arp"):
            kwargs["arp"] = RouterARPCache(sys_log=kwargs.get("sys_log"), router=self)
        if not kwargs.get("icmp"):
            kwargs["icmp"] = RouterICMP(sys_log=kwargs.get("sys_log"), arp_cache=kwargs.get("arp"), router=self)
        super().__init__(hostname=hostname, num_ports=num_ports, **kwargs)
        for i in range(1, self.num_ports + 1):
            nic = NIC(ip_address="127.0.0.1", subnet_mask="255.0.0.0", gateway="0.0.0.0")
            self.connect_nic(nic)
            self.ethernet_ports[i] = nic

        self.arp.nics = self.nics
        self.icmp.arp = self.arp

    def _get_port_of_nic(self, target_nic: NIC) -> Optional[int]:
        for port, nic in self.ethernet_ports.items():
            if nic == target_nic:
                return port

    def describe_state(self) -> Dict:
        pass

    def route_frame(self, frame: Frame, from_nic: NIC, re_attempt: bool = False) -> None:
        # Check if src ip is on network of one of the NICs
        nic = self.arp.get_arp_cache_nic(frame.ip.dst_ip)
        target_mac = self.arp.get_arp_cache_mac_address(frame.ip.dst_ip)

        if re_attempt and not nic:
            self.sys_log.info(f"Destination {frame.ip.dst_ip} is unreachable")
            return

        if not nic:
            self.arp.send_arp_request(frame.ip.dst_ip)
            return self.route_frame(frame=frame, from_nic=from_nic, re_attempt=True)

        if not nic.enabled:
            # TODO: Add sys_log here
            return

        if frame.ip.dst_ip in nic.ip_network:
            from_port = self._get_port_of_nic(from_nic)
            to_port = self._get_port_of_nic(nic)
            self.sys_log.info(f"Routing frame to internally from port {from_port} to port {to_port}")
            frame.decrement_ttl()
            frame.ethernet.src_mac_addr = nic.mac_address
            frame.ethernet.dst_mac_addr = target_mac
            nic.send_frame(frame)
            return
        else:
            pass
            # TODO: Deal with routing from route tables

    def receive_frame(self, frame: Frame, from_nic: NIC):
        """
        Receive a Frame from the connected NIC and process it.

        Depending on the protocol, the frame is passed to the appropriate handler such as ARP or ICMP, or up to the
        SessionManager if no code manager exists.

        :param frame: The Frame being received.
        :param from_nic: The NIC that received the frame.
        """
        route_frame = False
        protocol = frame.ip.protocol
        src_ip = frame.ip.src_ip
        dst_ip = frame.ip.dst_ip
        src_port = None
        dst_port = None
        if frame.ip.protocol == IPProtocol.TCP:
            src_port = frame.tcp.src_port
            dst_port = frame.tcp.dst_port
        elif frame.ip.protocol == IPProtocol.UDP:
            src_port = frame.udp.src_port
            dst_port = frame.udp.dst_port

        # Check if it's permitted
        permitted, rule = self.acl.is_permitted(
            protocol=protocol, src_ip=src_ip, src_port=src_port, dst_ip=dst_ip, dst_port=dst_port
        )
        if not permitted:
            at_port = self._get_port_of_nic(from_nic)
            self.sys_log.info(f"Frame blocked at port {at_port} by rule {rule}")
            return
        if not self.arp.get_arp_cache_nic(src_ip):
            self.arp.add_arp_cache_entry(src_ip, frame.ethernet.src_mac_addr, from_nic)
        if frame.ip.protocol == IPProtocol.ICMP:
            self.icmp.process_icmp(frame=frame, from_nic=from_nic)
        else:
            if src_port == Port.ARP:
                self.arp.process_arp_packet(from_nic=from_nic, frame=frame)
            else:
                # All other traffic
                route_frame = True
        if route_frame:
            self.route_frame(frame, from_nic)

    def configure_port(self, port: int, ip_address: Union[IPv4Address, str], subnet_mask: Union[IPv4Address, str]):
        if not isinstance(ip_address, IPv4Address):
            ip_address = IPv4Address(ip_address)
        if not isinstance(subnet_mask, IPv4Address):
            subnet_mask = IPv4Address(subnet_mask)
        nic = self.ethernet_ports[port]
        nic.ip_address = ip_address
        nic.subnet_mask = subnet_mask
        self.sys_log.info(f"Configured port {port} with ip_address={ip_address}/{nic.ip_network.prefixlen}")

    def enable_port(self, port: int):
        nic = self.ethernet_ports.get(port)
        if nic:
            nic.enable()

    def disable_port(self, port: int):
        nic = self.ethernet_ports.get(port)
        if nic:
            nic.disable()

    def show(self):
        """Prints a table of the NICs on the Node."""
        table = PrettyTable(["Port", "MAC Address", "Address", "Speed", "Status"])
        table.title = f"{self.hostname} Ethernet Interfaces"
        for port, nic in self.ethernet_ports.items():
            table.add_row(
                [
                    port,
                    nic.mac_address,
                    f"{nic.ip_address}/{nic.ip_network.prefixlen}",
                    nic.speed,
                    "Enabled" if nic.enabled else "Disabled",
                ]
            )
        print(table)
