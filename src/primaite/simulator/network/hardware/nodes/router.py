from __future__ import annotations

import secrets
from enum import Enum
from ipaddress import IPv4Address, IPv4Network
from typing import Dict, List, Optional, Tuple, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.network.hardware.base import ARPCache, ICMP, NIC, Node
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.transmission.data_link_layer import EthernetHeader, Frame
from primaite.simulator.network.transmission.network_layer import ICMPPacket, ICMPType, IPPacket, IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port, TCPHeader
from primaite.simulator.system.core.sys_log import SysLog


class ACLAction(Enum):
    """Enum for defining the ACL action types."""

    PERMIT = 1
    DENY = 2


class ACLRule(SimComponent):
    """
    Represents an Access Control List (ACL) rule.

    :ivar ACLAction action: Action to be performed (Permit/Deny). Default is DENY.
    :ivar Optional[IPProtocol] protocol: Network protocol. Default is None.
    :ivar Optional[IPv4Address] src_ip_address: Source IP address. Default is None.
    :ivar Optional[Port] src_port: Source port number. Default is None.
    :ivar Optional[IPv4Address] dst_ip_address: Destination IP address. Default is None.
    :ivar Optional[Port] dst_port: Destination port number. Default is None.
    """

    action: ACLAction = ACLAction.DENY
    protocol: Optional[IPProtocol] = None
    src_ip_address: Optional[IPv4Address] = None
    src_port: Optional[Port] = None
    dst_ip_address: Optional[IPv4Address] = None
    dst_port: Optional[Port] = None

    def __str__(self) -> str:
        rule_strings = []
        for key, value in self.model_dump(exclude={"uuid", "request_manager"}).items():
            if value is None:
                value = "ANY"
            if isinstance(value, Enum):
                rule_strings.append(f"{key}={value.name}")
            else:
                rule_strings.append(f"{key}={value}")
        return ", ".join(rule_strings)

    def describe_state(self) -> Dict:
        """
        Describes the current state of the ACLRule.

        :return: A dictionary representing the current state.
        """
        state = super().describe_state()
        state["action"] = self.action.value
        state["protocol"] = self.protocol.name if self.protocol else None
        state["src_ip_address"] = str(self.src_ip_address) if self.src_ip_address else None
        state["src_port"] = self.src_port.name if self.src_port else None
        state["dst_ip_address"] = str(self.dst_ip_address) if self.dst_ip_address else None
        state["dst_port"] = self.dst_port.name if self.dst_port else None
        return state


class AccessControlList(SimComponent):
    """
    Manages a list of ACLRules to filter network traffic.

    :ivar SysLog sys_log: System logging instance.
    :ivar ACLAction implicit_action: Default action for rules.
    :ivar ACLRule implicit_rule: Implicit ACL rule, created based on implicit_action.
    :ivar int max_acl_rules: Maximum number of ACL rules that can be added. Default is 25.
    :ivar List[Optional[ACLRule]] _acl: A list containing the ACL rules.
    """

    sys_log: SysLog
    implicit_action: ACLAction
    implicit_rule: ACLRule
    max_acl_rules: int = 25
    _acl: List[Optional[ACLRule]] = [None] * 24
    _default_config: Dict[int, dict] = {}
    """Config dict describing how the ACL list should look at episode start"""

    def __init__(self, **kwargs) -> None:
        if not kwargs.get("implicit_action"):
            kwargs["implicit_action"] = ACLAction.DENY

        kwargs["implicit_rule"] = ACLRule(action=kwargs["implicit_action"])

        super().__init__(**kwargs)
        self._acl = [None] * (self.max_acl_rules - 1)

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        self.implicit_rule.reset_component_for_episode(episode)
        super().reset_component_for_episode(episode)
        self._reset_rules_to_default()

    def _reset_rules_to_default(self) -> None:
        """Clear all ACL rules and set them to the default rules config."""
        self._acl = [None] * (self.max_acl_rules - 1)
        for r_num, r_cfg in self._default_config.items():
            self.add_rule(
                action=ACLAction[r_cfg["action"]],
                src_port=None if not (p := r_cfg.get("src_port")) else Port[p],
                dst_port=None if not (p := r_cfg.get("dst_port")) else Port[p],
                protocol=None if not (p := r_cfg.get("protocol")) else IPProtocol[p],
                src_ip_address=r_cfg.get("src_ip"),
                dst_ip_address=r_cfg.get("dst_ip"),
                position=r_num,
            )

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()

        # When the request reaches this action, it should now contain solely positional args for the 'add_rule' action.
        # POSITIONAL ARGUMENTS:
        # 0: action (str name of an ACLAction)
        # 1: protocol (str name of an IPProtocol)
        # 2: source ip address (str castable to IPV4Address (e.g. '10.10.1.2'))
        # 3: source port (str name of a Port (e.g. "HTTP"))  # should we be using value, such as 80 or 443?
        # 4: destination ip address (str castable to IPV4Address (e.g. '10.10.1.2'))
        # 5: destination port (str name of a Port (e.g. "HTTP"))
        # 6: position (int)
        rm.add_request(
            "add_rule",
            RequestType(
                func=lambda request, context: self.add_rule(
                    ACLAction[request[0]],
                    None if request[1] == "ALL" else IPProtocol[request[1]],
                    None if request[2] == "ALL" else IPv4Address(request[2]),
                    None if request[3] == "ALL" else Port[request[3]],
                    None if request[4] == "ALL" else IPv4Address(request[4]),
                    None if request[5] == "ALL" else Port[request[5]],
                    int(request[6]),
                )
            ),
        )

        rm.add_request("remove_rule", RequestType(func=lambda request, context: self.remove_rule(int(request[0]))))
        return rm

    def describe_state(self) -> Dict:
        """
        Describes the current state of the AccessControlList.

        :return: A dictionary representing the current state.
        """
        state = super().describe_state()
        state["implicit_action"] = self.implicit_action.value
        state["implicit_rule"] = self.implicit_rule.describe_state()
        state["max_acl_rules"] = self.max_acl_rules
        state["acl"] = {i: r.describe_state() if isinstance(r, ACLRule) else None for i, r in enumerate(self._acl)}
        return state

    @property
    def acl(self) -> List[Optional[ACLRule]]:
        """
        Get the list of ACL rules.

        :return: The list of ACL rules.
        """
        return self._acl

    def add_rule(
        self,
        action: ACLAction,
        protocol: Optional[IPProtocol] = None,
        src_ip_address: Optional[Union[str, IPv4Address]] = None,
        src_port: Optional[Port] = None,
        dst_ip_address: Optional[Union[str, IPv4Address]] = None,
        dst_port: Optional[Port] = None,
        position: int = 0,
    ) -> None:
        """
        Add a new ACL rule.

        :param ACLAction action: Action to be performed (Permit/Deny).
        :param Optional[IPProtocol] protocol: Network protocol.
        :param Optional[Union[str, IPv4Address]] src_ip_address: Source IP address.
        :param Optional[Port] src_port: Source port number.
        :param Optional[Union[str, IPv4Address]] dst_ip_address: Destination IP address.
        :param Optional[Port] dst_port: Destination port number.
        :param int position: Position in the ACL list to insert the rule.
        :raises ValueError: When the position is out of bounds.
        """
        if isinstance(src_ip_address, str):
            src_ip_address = IPv4Address(src_ip_address)
        if isinstance(dst_ip_address, str):
            dst_ip_address = IPv4Address(dst_ip_address)
        if 0 <= position < self.max_acl_rules:
            if self._acl[position]:
                self.sys_log.info(f"Overwriting ACL rule at position {position}")
            self._acl[position] = ACLRule(
                action=action,
                src_ip_address=src_ip_address,
                dst_ip_address=dst_ip_address,
                protocol=protocol,
                src_port=src_port,
                dst_port=dst_port,
            )
        else:
            raise ValueError(f"Cannot add ACL rule, position {position} is out of bounds.")

    def remove_rule(self, position: int) -> None:
        """
        Remove an ACL rule from a specific position.

        :param int position: The position of the rule to be removed.
        :raises ValueError: When the position is out of bounds.
        """
        if 0 <= position < self.max_acl_rules - 1:
            rule = self._acl[position]  # noqa
            self._acl[position] = None
            del rule
        else:
            raise ValueError(f"Cannot remove ACL rule, position {position} is out of bounds.")

    def is_permitted(
        self,
        protocol: IPProtocol,
        src_ip_address: Union[str, IPv4Address],
        src_port: Optional[Port],
        dst_ip_address: Union[str, IPv4Address],
        dst_port: Optional[Port],
    ) -> Tuple[bool, Optional[Union[str, ACLRule]]]:
        """
        Check if a packet with the given properties is permitted through the ACL.

        :param protocol: The protocol of the packet.
        :param src_ip_address: Source IP address of the packet. Accepts string and IPv4Address.
        :param src_port: Source port of the packet. Optional.
        :param dst_ip_address: Destination IP address of the packet. Accepts string and IPv4Address.
        :param dst_port: Destination port of the packet. Optional.
        :return: A tuple with a boolean indicating if the packet is permitted and an optional rule or implicit action
            string.
        """
        if not isinstance(src_ip_address, IPv4Address):
            src_ip_address = IPv4Address(src_ip_address)
        if not isinstance(dst_ip_address, IPv4Address):
            dst_ip_address = IPv4Address(dst_ip_address)
        for rule in self._acl:
            if not rule:
                continue

            if (
                (rule.src_ip_address == src_ip_address or rule.src_ip_address is None)
                and (rule.dst_ip_address == dst_ip_address or rule.dst_ip_address is None)
                and (rule.protocol == protocol or rule.protocol is None)
                and (rule.src_port == src_port or rule.src_port is None)
                and (rule.dst_port == dst_port or rule.dst_port is None)
            ):
                return rule.action == ACLAction.PERMIT, rule

        return self.implicit_action == ACLAction.PERMIT, f"Implicit {self.implicit_action.name}"

    def get_relevant_rules(
        self,
        protocol: IPProtocol,
        src_ip_address: Union[str, IPv4Address],
        src_port: Port,
        dst_ip_address: Union[str, IPv4Address],
        dst_port: Port,
    ) -> List[ACLRule]:
        """
        Get the list of relevant rules for a packet with given properties.

        :param protocol: The protocol of the packet.
        :param src_ip_address: Source IP address of the packet. Accepts string and IPv4Address.
        :param src_port: Source port of the packet.
        :param dst_ip_address: Destination IP address of the packet. Accepts string and IPv4Address.
        :param dst_port: Destination port of the packet.
        :return: A list of relevant ACLRules.
        """
        if not isinstance(src_ip_address, IPv4Address):
            src_ip_address = IPv4Address(src_ip_address)
        if not isinstance(dst_ip_address, IPv4Address):
            dst_ip_address = IPv4Address(dst_ip_address)
        relevant_rules = []
        for rule in self._acl:
            if rule is None:
                continue

            if (
                (rule.src_ip_address == src_ip_address or rule.src_ip_address is None)
                or (rule.dst_ip_address == dst_ip_address or rule.dst_ip_address is None)
                or (rule.protocol == protocol or rule.protocol is None)
                or (rule.src_port == src_port or rule.src_port is None)
                or (rule.dst_port == dst_port or rule.dst_port is None)
            ):
                relevant_rules.append(rule)

        return relevant_rules

    def show(self, markdown: bool = False):
        """
        Display the current ACL rules as a table.

        :param markdown: Whether to display the table in Markdown format. Defaults to False.
        """
        table = PrettyTable(["Index", "Action", "Protocol", "Src IP", "Src Port", "Dst IP", "Dst Port"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} Access Control List"
        for index, rule in enumerate(self.acl + [self.implicit_rule]):
            if rule:
                table.add_row(
                    [
                        index,
                        rule.action.name if rule.action else "ANY",
                        rule.protocol.name if rule.protocol else "ANY",
                        rule.src_ip_address if rule.src_ip_address else "ANY",
                        f"{rule.src_port.value} ({rule.src_port.name})" if rule.src_port else "ANY",
                        rule.dst_ip_address if rule.dst_ip_address else "ANY",
                        f"{rule.dst_port.value} ({rule.dst_port.name})" if rule.dst_port else "ANY",
                    ]
                )
        print(table)

    @property
    def num_rules(self) -> int:
        """
        Get the number of rules in the ACL.

        :return: The number of rules in the ACL.
        """
        return len([rule for rule in self._acl if rule is not None])


class RouteEntry(SimComponent):
    """
    Represents a single entry in a routing table.

    :ivar address: The destination IP address or network address.
    :ivar subnet_mask: The subnet mask for the network.
    :ivar next_hop_ip_address: The next hop IP address to which packets should be forwarded.
    :ivar metric: The cost metric for this route. Default is 0.0.

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
    next_hop_ip_address: IPv4Address
    "The next hop IP address to which packets should be forwarded."
    metric: float = 0.0
    "The cost metric for this route. Default is 0.0."

    def describe_state(self) -> Dict:
        """
        Describes the current state of the RouteEntry.

        :return: A dictionary representing the current state.
        """
        pass


class RouteTable(SimComponent):
    """
    Represents a routing table holding multiple route entries.

    :ivar List[RouteEntry] routes: A list of RouteEntry objects.

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
    default_route: Optional[RouteEntry] = None
    sys_log: SysLog

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        self.routes.clear()
        self.routes = self._original_state["routes_orig"]
        super().reset_component_for_episode(episode)

    def describe_state(self) -> Dict:
        """
        Describes the current state of the RouteTable.

        :return: A dictionary representing the current state.
        """
        pass

    def add_route(
        self,
        address: Union[IPv4Address, str],
        subnet_mask: Union[IPv4Address, str],
        next_hop_ip_address: Union[IPv4Address, str],
        metric: float = 0.0,
    ):
        """
        Add a route to the routing table.

        :param address: The destination address of the route.
        :param subnet_mask: The subnet mask of the route.
        :param next_hop_ip_address: The next hop IP for the route.
        :param metric: The metric of the route, default is 0.0.
        """
        for key in {address, subnet_mask, next_hop_ip_address}:
            if not isinstance(key, IPv4Address):
                key = IPv4Address(key)
        route = RouteEntry(
            address=address, subnet_mask=subnet_mask, next_hop_ip_address=next_hop_ip_address, metric=metric
        )
        self.routes.append(route)

    def set_default_route_next_hop_ip_address(self, ip_address: IPv4Address):
        """
        Sets the next-hop IP address for the default route in a routing table.

        This method checks if a default route (0.0.0.0/0) exists in the routing table. If it does not exist,
         the method creates a new default route with the specified next-hop IP address. If a default route already
         exists, it updates the next-hop IP address of the existing default route. After setting the next-hop
         IP address, the method logs this action.

        :param ip_address: The next-hop IP address to be set for the default route.
        """
        if not self.default_route:
            self.default_route = RouteEntry(
                ip_address=IPv4Address("0.0.0.0"),
                subnet_mask=IPv4Address("0.0.0.0"),
                next_hop_ip_address=ip_address,
            )
        else:
            self.default_route.next_hop_ip_address = ip_address
        self.sys_log.info(f"Default configured to use {ip_address} as the next-hop")

    def find_best_route(self, destination_ip: Union[str, IPv4Address]) -> Optional[RouteEntry]:
        """
        Find the best route for a given destination IP.

        This method uses the Longest Prefix Match algorithm and considers metrics to find the best route.

        If no dedicated route exists but a default route does, then the default route is returned as a last resort.

        :param destination_ip: The destination IP to find the route for.
        :return: The best matching RouteEntry, or None if no route matches.
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

        if not best_route and self.default_route:
            best_route = self.default_route

        return best_route

    def show(self, markdown: bool = False):
        """
        Display the current routing table as a table.

        :param markdown: Whether to display the table in Markdown format. Defaults to False.
        """
        table = PrettyTable(["Index", "Address", "Next Hop", "Metric"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} Route Table"
        for index, route in enumerate(self.routes):
            network = IPv4Network(f"{route.address}/{route.subnet_mask}")
            table.add_row([index, f"{route.address}/{network.prefixlen}", route.next_hop_ip_address, route.metric])
        print(table)


class RouterARPCache(ARPCache):
    """
    Inherits from ARPCache and adds router-specific ARP packet processing.

    :ivar SysLog sys_log: A system log for logging messages.
    :ivar Router router: The router to which this ARP cache belongs.
    """

    def __init__(self, sys_log: SysLog, router: Router):
        super().__init__(sys_log)
        self.router: Router = router

    def process_arp_packet(
        self, from_nic: NIC, frame: Frame, route_table: RouteTable, is_reattempt: bool = False
    ) -> None:
        """
        Processes a received ARP (Address Resolution Protocol) packet in a router-specific way.

        This method is responsible for handling both ARP requests and responses. It processes ARP packets received on a
        Network Interface Card (NIC) and performs actions based on whether the packet is a request or a reply. This
        includes updating the ARP cache, forwarding ARP replies, sending ARP requests for unknown destinations, and
        handling packet TTL (Time To Live).

        The method first checks if the ARP packet is a request or a reply. For ARP replies, it updates the ARP cache
        and forwards the reply if necessary. For ARP requests, it checks if the target IP matches one of the router's
        NICs and sends an ARP reply if so. If the destination is not directly connected, it consults the routing table
        to find the best route and reattempts ARP request processing if needed.

        :param from_nic: The NIC that received the ARP packet.
        :param frame: The frame containing the ARP packet.
        :param route_table: The routing table of the router.
        :param is_reattempt: Flag to indicate if this is a reattempt of processing the ARP packet, defaults to False.
        """
        arp_packet = frame.arp

        # ARP Reply
        if not arp_packet.request:
            for nic in self.router.nics.values():
                if arp_packet.target_ip_address == nic.ip_address:
                    # reply to the Router specifically
                    self.sys_log.info(
                        f"Received ARP response for {arp_packet.sender_ip_address} "
                        f"from {arp_packet.sender_mac_addr} via NIC {from_nic}"
                    )
                    self.add_arp_cache_entry(
                        ip_address=arp_packet.sender_ip_address,
                        mac_address=arp_packet.sender_mac_addr,
                        nic=from_nic,
                    )
                    return

            # Reply for a connected requested
            nic = self.get_arp_cache_nic(arp_packet.target_ip_address)
            if nic:
                self.sys_log.info(
                    f"Forwarding arp reply for {arp_packet.target_ip_address}, from {arp_packet.sender_ip_address}"
                )
                arp_packet.sender_mac_addr = nic.mac_address
                frame.decrement_ttl()
                if frame.ip and frame.ip.ttl < 1:
                    self.sys_log.info("Frame discarded as TTL limit reached")
                    return
                nic.send_frame(frame)
            return

        # ARP Request
        self.sys_log.info(
            f"Received ARP request for {arp_packet.target_ip_address} from "
            f"{arp_packet.sender_mac_addr}/{arp_packet.sender_ip_address} "
        )
        # Matched ARP request
        self.add_arp_cache_entry(
            ip_address=arp_packet.sender_ip_address, mac_address=arp_packet.sender_mac_addr, nic=from_nic
        )

        # If the target IP matches one of the router's NICs
        for nic in self.nics.values():
            if arp_packet.target_ip_address in nic.ip_network:
                # if nic.enabled and nic.ip_address == arp_packet.target_ip_address:
                arp_reply = arp_packet.generate_reply(from_nic.mac_address)
                self.send_arp_reply(arp_reply, from_nic)
                return

        # Check Route Table
        route = route_table.find_best_route(arp_packet.target_ip_address)
        if route:
            nic = self.get_arp_cache_nic(route.next_hop_ip_address)

            if not nic:
                if not is_reattempt:
                    self.send_arp_request(route.next_hop_ip_address, ignore_networks=[frame.ip.src_ip_address])
                    return self.process_arp_packet(from_nic, frame, route_table, is_reattempt=True)
                else:
                    self.sys_log.info("Ignoring ARP request as destination unavailable/No ARP entry found")
                    return
            else:
                arp_reply = arp_packet.generate_reply(from_nic.mac_address)
                self.send_arp_reply(arp_reply, from_nic)
            return


class RouterICMP(ICMP):
    """
    A class to represent a router's Internet Control Message Protocol (ICMP) handler.

    :param sys_log: System log for logging network events and errors.
    :type sys_log: SysLog
    :param arp_cache: The ARP cache for resolving MAC addresses.
    :type arp_cache: ARPCache
    :param router: The router to which this ICMP handler belongs.
    :type router: Router
    """

    router: Router

    def __init__(self, sys_log: SysLog, arp_cache: ARPCache, router: Router):
        super().__init__(sys_log, arp_cache)
        self.router = router

    def process_icmp(self, frame: Frame, from_nic: NIC, is_reattempt: bool = False):
        """
        Process incoming ICMP frames based on ICMP type.

        :param frame: The incoming frame to process.
        :param from_nic: The network interface where the frame is coming from.
        :param is_reattempt: Flag to indicate if the process is a reattempt.
        """
        if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
            # determine if request is for router interface or whether it needs to be routed

            for nic in self.router.nics.values():
                if nic.ip_address == frame.ip.dst_ip_address:
                    if nic.enabled:
                        # reply to the request
                        if not is_reattempt:
                            self.sys_log.info(f"Received echo request from {frame.ip.src_ip_address}")
                        target_mac_address = self.arp.get_arp_cache_mac_address(frame.ip.src_ip_address)
                        src_nic = self.arp.get_arp_cache_nic(frame.ip.src_ip_address)
                        tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)

                        # Network Layer
                        ip_packet = IPPacket(
                            src_ip_address=nic.ip_address,
                            dst_ip_address=frame.ip.src_ip_address,
                            protocol=IPProtocol.ICMP,
                        )
                        # Data Link Layer
                        ethernet_header = EthernetHeader(
                            src_mac_addr=src_nic.mac_address, dst_mac_addr=target_mac_address
                        )
                        icmp_reply_packet = ICMPPacket(
                            icmp_type=ICMPType.ECHO_REPLY,
                            icmp_code=0,
                            identifier=frame.icmp.identifier,
                            sequence=frame.icmp.sequence + 1,
                        )
                        payload = secrets.token_urlsafe(int(32 / 1.3))  # Standard ICMP 32 bytes size
                        frame = Frame(
                            ethernet=ethernet_header,
                            ip=ip_packet,
                            tcp=tcp_header,
                            icmp=icmp_reply_packet,
                            payload=payload,
                        )
                        self.sys_log.info(f"Sending echo reply to {frame.ip.dst_ip_address}")

                        src_nic.send_frame(frame)
                    return

            # Route the frame
            self.router.process_frame(frame, from_nic)

        elif frame.icmp.icmp_type == ICMPType.ECHO_REPLY:
            for nic in self.router.nics.values():
                if nic.ip_address == frame.ip.dst_ip_address:
                    if nic.enabled:
                        time = frame.transmission_duration()
                        time_str = f"{time}ms" if time > 0 else "<1ms"
                        self.sys_log.info(
                            f"Reply from {frame.ip.src_ip_address}: "
                            f"bytes={len(frame.payload)}, "
                            f"time={time_str}, "
                            f"TTL={frame.ip.ttl}"
                        )
                        if not self.request_replies.get(frame.icmp.identifier):
                            self.request_replies[frame.icmp.identifier] = 0
                        self.request_replies[frame.icmp.identifier] += 1

                    return
            # Route the frame
            self.router.process_frame(frame, from_nic)


class RouterNIC(NIC):
    """
    A Router-specific Network Interface Card (NIC) that extends the standard NIC functionality.

    This class overrides the standard Node NIC's Layer 3 (L3) broadcast/unicast checks. It is designed
    to handle network frames in a manner specific to routers, allowing them to efficiently process
    and route network traffic.
    """

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receive and process a network frame from the connected link, provided the NIC is enabled.

        This method is tailored for router behavior. It decrements the frame's Time To Live (TTL), checks for TTL
        expiration, and captures the frame using PCAP (Packet Capture). The frame is accepted if it is destined for
        this NIC's MAC address or is a broadcast frame.

        Key Differences from Standard NIC:
        - Does not perform Layer 3 (IP-based) broadcast checks.
        - Only checks for Layer 2 (Ethernet) destination MAC address and broadcast frames.

        :param frame: The network frame being received. This should be an instance of the Frame class.
        :return: Returns True if the frame is processed and passed to the connected node, False otherwise.
        """
        if self.enabled:
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self._connected_node.sys_log.info("Frame discarded as TTL limit reached")
                return False
            frame.set_received_timestamp()
            self.pcap.capture(frame)
            # If this destination or is broadcast
            if frame.ethernet.dst_mac_addr == self.mac_address or frame.ethernet.dst_mac_addr == "ff:ff:ff:ff:ff:ff":
                self._connected_node.receive_frame(frame=frame, from_nic=self)
                return True
        return False

    def __str__(self) -> str:
        return f"{self.mac_address}/{self.ip_address}"


class Router(Node):
    """
    A class to represent a network router node.

    :ivar str hostname: The name of the router node.
    :ivar int num_ports: The number of ports in the router.
    :ivar dict kwargs: Optional keyword arguments for SysLog, ACL, RouteTable, RouterARPCache, RouterICMP.
    """

    num_ports: int
    ethernet_ports: Dict[int, RouterNIC] = {}
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
            nic = RouterNIC(ip_address="127.0.0.1", subnet_mask="255.0.0.0", gateway="0.0.0.0")
            self.connect_nic(nic)
            self.ethernet_ports[i] = nic

        self.arp.nics = self.nics
        self.icmp.arp = self.arp

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        self.arp.clear()
        self.acl.reset_component_for_episode(episode)
        self.route_table.reset_component_for_episode(episode)
        for i, nic in self.ethernet_ports.items():
            nic.reset_component_for_episode(episode)
            self.enable_port(i)

        super().reset_component_for_episode(episode)

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()
        rm.add_request("acl", RequestType(func=self.acl._request_manager))
        return rm

    def _get_port_of_nic(self, target_nic: NIC) -> Optional[int]:
        """
        Retrieve the port number for a given NIC.

        :param target_nic: Target network interface.
        :return: The port number if NIC is found, otherwise None.
        """
        for port, nic in self.ethernet_ports.items():
            if nic == target_nic:
                return port

    def describe_state(self) -> Dict:
        """
        Describes the current state of the Router.

        :return: A dictionary representing the current state.
        """
        state = super().describe_state()
        state["num_ports"] = self.num_ports
        state["acl"] = self.acl.describe_state()
        return state

    def process_frame(self, frame: Frame, from_nic: NIC, re_attempt: bool = False) -> None:
        """
        Process a Frame.

        :param frame: The frame to be routed.
        :param from_nic: The source network interface.
        :param re_attempt: Flag to indicate if the routing is a reattempt.
        """
        # Check if src ip is on network of one of the NICs
        nic = self.arp.get_arp_cache_nic(frame.ip.dst_ip_address)
        target_mac = self.arp.get_arp_cache_mac_address(frame.ip.dst_ip_address)

        if re_attempt and not nic:
            self.sys_log.info(f"Destination {frame.ip.dst_ip_address} is unreachable")
            return

        if not nic:
            self.arp.send_arp_request(
                frame.ip.dst_ip_address, ignore_networks=[frame.ip.src_ip_address, from_nic.ip_address]
            )
            return self.process_frame(frame=frame, from_nic=from_nic, re_attempt=True)

        if not nic.enabled:
            self.sys_log.info(f"Frame dropped as NIC {nic} is not enabled")
            return

        if frame.ip.dst_ip_address in nic.ip_network:
            from_port = self._get_port_of_nic(from_nic)
            to_port = self._get_port_of_nic(nic)
            self.sys_log.info(f"Forwarding frame to internally from port {from_port} to port {to_port}")
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self.sys_log.info("Frame discarded as TTL limit reached")
                return
            frame.ethernet.src_mac_addr = nic.mac_address
            frame.ethernet.dst_mac_addr = target_mac
            nic.send_frame(frame)
            return
        else:
            self._route_frame(frame, from_nic)

    def _route_frame(self, frame: Frame, from_nic: NIC, re_attempt: bool = False) -> None:
        route = self.route_table.find_best_route(frame.ip.dst_ip_address)
        if route:
            nic = self.arp.get_arp_cache_nic(route.next_hop_ip_address)
            target_mac = self.arp.get_arp_cache_mac_address(route.next_hop_ip_address)
            if re_attempt and not nic:
                self.sys_log.info(f"Destination {frame.ip.dst_ip_address} is unreachable")
                return

            if not nic:
                self.arp.send_arp_request(frame.ip.dst_ip_address, ignore_networks=[frame.ip.src_ip_address])
                return self.process_frame(frame=frame, from_nic=from_nic, re_attempt=True)

            if not nic.enabled:
                self.sys_log.info(f"Frame dropped as NIC {nic} is not enabled")
                return

            from_port = self._get_port_of_nic(from_nic)
            to_port = self._get_port_of_nic(nic)
            self.sys_log.info(f"Routing frame to internally from port {from_port} to port {to_port}")
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self.sys_log.info("Frame discarded as TTL limit reached")
                return
            frame.ethernet.src_mac_addr = nic.mac_address
            frame.ethernet.dst_mac_addr = target_mac
            nic.send_frame(frame)

    def receive_frame(self, frame: Frame, from_nic: NIC):
        """
        Receive a frame from a NIC and processes it based on its protocol.

        :param frame: The incoming frame.
        :param from_nic: The network interface where the frame is coming from.
        """
        process_frame = False
        protocol = frame.ip.protocol
        src_ip_address = frame.ip.src_ip_address
        dst_ip_address = frame.ip.dst_ip_address
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
            protocol=protocol,
            src_ip_address=src_ip_address,
            src_port=src_port,
            dst_ip_address=dst_ip_address,
            dst_port=dst_port,
        )

        if not permitted:
            at_port = self._get_port_of_nic(from_nic)
            self.sys_log.info(f"Frame blocked at port {at_port} by rule {rule}")
            return
        if not self.arp.get_arp_cache_nic(src_ip_address):
            self.arp.add_arp_cache_entry(src_ip_address, frame.ethernet.src_mac_addr, from_nic)
        if frame.ip.protocol == IPProtocol.ICMP:
            self.icmp.process_icmp(frame=frame, from_nic=from_nic)
        else:
            if src_port == Port.ARP:
                self.arp.process_arp_packet(from_nic=from_nic, frame=frame, route_table=self.route_table)
            else:
                # All other traffic
                process_frame = True
        if process_frame:
            self.process_frame(frame, from_nic)

    def configure_port(self, port: int, ip_address: Union[IPv4Address, str], subnet_mask: Union[IPv4Address, str]):
        """
        Configure the IP settings of a given port.

        :param port: The port to configure.
        :param ip_address: The IP address to set.
        :param subnet_mask: The subnet mask to set.
        """
        if not isinstance(ip_address, IPv4Address):
            ip_address = IPv4Address(ip_address)
        if not isinstance(subnet_mask, IPv4Address):
            subnet_mask = IPv4Address(subnet_mask)
        nic = self.ethernet_ports[port]
        nic.ip_address = ip_address
        nic.subnet_mask = subnet_mask
        self.sys_log.info(f"Configured port {port} with ip_address={ip_address}/{nic.ip_network.prefixlen}")

    def enable_port(self, port: int):
        """
        Enable a given port on the router.

        :param port: The port to enable.
        """
        nic = self.ethernet_ports.get(port)
        if nic:
            nic.enable()

    def disable_port(self, port: int):
        """
        Disable a given port on the router.

        :param port: The port to disable.
        """
        nic = self.ethernet_ports.get(port)
        if nic:
            nic.disable()

    def show(self, markdown: bool = False):
        """
        Prints the state of the Ethernet interfaces on the Router.

        :param markdown: Flag to indicate if the output should be in markdown format.
        """
        """Prints a table of the NICs on the Node."""
        table = PrettyTable(["Port", "MAC Address", "Address", "Speed", "Status"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
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

    @classmethod
    def from_config(cls, cfg: dict) -> "Router":
        """Create a router based on a config dict.

        Schema:
          - hostname (str): unique name for this router.
          - num_ports (int, optional): Number of network ports on the router. 8 by default
          - ports (dict): Dict with integers from 1 - num_ports as keys. The values should be another dict specifying
                ip_address and subnet_mask assigned to that ports (as strings)
          - acl (dict): Dict with integers from 1 - max_acl_rules as keys. The key defines the position within the ACL
                where the rule will be added (lower number is resolved first). The values should describe valid ACL
                Rules as:
              - action (str): either PERMIT or DENY
              - src_port (str, optional): the named port such as HTTP, HTTPS, or POSTGRES_SERVER
              - dst_port (str, optional): the named port such as HTTP, HTTPS, or POSTGRES_SERVER
              - protocol (str, optional): the named IP protocol such as ICMP, TCP, or UDP
              - src_ip_address (str, optional): IP address octet written in base 10
              - dst_ip_address (str, optional): IP address octet written in base 10

        Example config:
        ```
        {
            'hostname': 'router_1',
            'num_ports': 5,
            'ports': {
                1: {
                    'ip_address' : '192.168.1.1',
                    'subnet_mask' : '255.255.255.0',
                }
            },
            'acl' : {
                21: {'action': 'PERMIT', 'src_port': 'HTTP', dst_port: 'HTTP'},
                22: {'action': 'PERMIT', 'src_port': 'ARP', 'dst_port': 'ARP'},
                23: {'action': 'PERMIT', 'protocol': 'ICMP'},
            },
        }
        ```

        :param cfg: Router config adhering to schema described in main docstring body
        :type cfg: dict
        :return: Configured router.
        :rtype: Router
        """
        new = Router(
            hostname=cfg["hostname"],
            num_ports=cfg.get("num_ports"),
            operating_state=NodeOperatingState.ON,
        )
        if "ports" in cfg:
            for port_num, port_cfg in cfg["ports"].items():
                new.configure_port(
                    port=port_num,
                    ip_address=port_cfg["ip_address"],
                    subnet_mask=port_cfg["subnet_mask"],
                )
        if "acl" in cfg:
            new.acl._default_config = cfg["acl"]  # save the config to allow resetting
            new.acl._reset_rules_to_default()  # read the config and apply rules
        return new
