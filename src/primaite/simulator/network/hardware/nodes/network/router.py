from __future__ import annotations

import secrets
from enum import Enum
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Dict, List, Optional, Tuple, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.network.hardware.base import IPWiredNetworkInterface
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.network.network_node import NetworkNode
from primaite.simulator.network.protocols.arp import ARPPacket
from primaite.simulator.network.protocols.icmp import ICMPPacket, ICMPType
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.arp.arp import ARP
from primaite.simulator.system.services.icmp.icmp import ICMP


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

    def set_original_state(self):
        """Sets the original state."""
        vals_to_keep = {"action", "protocol", "src_ip_address", "src_port", "dst_ip_address", "dst_port"}
        self._original_state = self.model_dump(include=vals_to_keep, exclude_none=True)

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
        self.set_original_state()

    def set_original_state(self):
        """Sets the original state."""
        self.implicit_rule.set_original_state()
        vals_to_keep = {"implicit_action", "max_acl_rules", "acl"}
        self._original_state = self.model_dump(include=vals_to_keep, exclude_none=True)

        for i, rule in enumerate(self._acl):
            if not rule:
                continue
            self._default_config[i] = {"action": rule.action.name}
            if rule.src_ip_address:
                self._default_config[i]["src_ip"] = str(rule.src_ip_address)
            if rule.dst_ip_address:
                self._default_config[i]["dst_ip"] = str(rule.dst_ip_address)
            if rule.src_port:
                self._default_config[i]["src_port"] = rule.src_port.name
            if rule.dst_port:
                self._default_config[i]["dst_port"] = rule.dst_port.name
            if rule.protocol:
                self._default_config[i]["protocol"] = rule.protocol.name

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

    @property
    def num_rules(self) -> int:
        """
        Get the number of rules in the ACL.

        :return: The number of rules in the ACL.
        """
        return len([rule for rule in self._acl if rule is not None])

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

    def set_original_state(self):
        """Sets the original state."""
        vals_to_include = {"address", "subnet_mask", "next_hop_ip_address", "metric"}
        self._original_values = self.model_dump(include=vals_to_include)

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

    def set_original_state(self):
        """Sets the original state."""
        super().set_original_state()
        self._original_state["routes_orig"] = self.routes

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


class RouterARP(ARP):
    """
    Extends ARP functionality with router-specific ARP packet processing capabilities.

    This class is designed to manage ARP requests and replies within a router, handling both the resolution of MAC
    addresses for IP addresses within the router's networks and the forwarding of ARP requests to other networks
    based on routing information.
    """

    router: Optional[Router] = None

    def _get_arp_cache_mac_address(
        self, ip_address: IPv4Address, is_reattempt: bool = False, is_default_route_attempt: bool = False
    ) -> Optional[str]:
        """
        Attempts to retrieve the MAC address associated with the given IP address from the ARP cache.

        If the address is not in the cache, an ARP request may be sent, and the method may reattempt the lookup.

        :param ip_address: The IP address for which to find the corresponding MAC address.
        :type ip_address: IPv4Address
        :param is_reattempt: Indicates whether this call is a reattempt after a failed initial attempt to find the MAC
            address.
        :type is_reattempt: bool
        :param is_default_route_attempt: Indicates whether the attempt is being made to resolve the MAC address for the
            default route.
        :type is_default_route_attempt: bool
        :return: The MAC address associated with the given IP address, if found; otherwise, None.
        :rtype: Optional[str]
        """
        arp_entry = self.arp.get(ip_address)

        if arp_entry:
            return arp_entry.mac_address

        if not is_reattempt:
            if self.router.ip_is_in_router_interface_subnet(ip_address):
                self.send_arp_request(ip_address)
                return self._get_arp_cache_mac_address(
                    ip_address=ip_address, is_reattempt=True, is_default_route_attempt=is_default_route_attempt
                )

            route = self.router.route_table.find_best_route(ip_address)
            if route and route != self.router.route_table.default_route:
                self.send_arp_request(route.next_hop_ip_address)
                return self._get_arp_cache_mac_address(
                    ip_address=route.next_hop_ip_address,
                    is_reattempt=True,
                    is_default_route_attempt=is_default_route_attempt,
                )
        else:
            if self.router.route_table.default_route:
                if not is_default_route_attempt:
                    self.send_arp_request(self.router.route_table.default_route.next_hop_ip_address)
                    return self._get_arp_cache_mac_address(
                        ip_address=self.router.route_table.default_route.next_hop_ip_address,
                        is_reattempt=True,
                        is_default_route_attempt=True,
                    )
        return None

    def get_arp_cache_mac_address(self, ip_address: IPv4Address) -> Optional[str]:
        """
        Public interface to retrieve the MAC address associated with the given IP address from the ARP cache.

        :param ip_address: The IP address for which to find the corresponding MAC address.
        :type ip_address: IPv4Address
        :return: The MAC address associated with the given IP address, if found; otherwise, None.
        :rtype: Optional[str]
        """
        return self._get_arp_cache_mac_address(ip_address)

    def _get_arp_cache_network_interface(
        self, ip_address: IPv4Address, is_reattempt: bool = False, is_default_route_attempt: bool = False
    ) -> Optional[RouterInterface]:
        """
        Attempts to retrieve the router interface associated with the given IP address.

        If the address is not directly associated with a router interface, it may send an ARP request based on
        routing information.

        :param ip_address: The IP address for which to find the corresponding router interface.
        :type ip_address: IPv4Address
        :param is_reattempt: Indicates whether this call is a reattempt after a failed initial attempt.
        :type is_reattempt: bool
        :param is_default_route_attempt: Indicates whether the attempt is being made for the default route's next-hop
            IP address.
        :type is_default_route_attempt: bool
        :return: The router interface associated with the given IP address, if applicable; otherwise, None.
        :rtype: Optional[RouterInterface]
        """
        arp_entry = self.arp.get(ip_address)
        if arp_entry:
            return self.software_manager.node.network_interfaces[arp_entry.network_interface_uuid]

        for network_interface in self.router.network_interfaces.values():
            if ip_address in network_interface.ip_network:
                return network_interface

        if not is_reattempt:
            route = self.router.route_table.find_best_route(ip_address)
            if route and route != self.router.route_table.default_route:
                self.send_arp_request(route.next_hop_ip_address)
                return self._get_arp_cache_network_interface(
                    ip_address=route.next_hop_ip_address,
                    is_reattempt=True,
                    is_default_route_attempt=is_default_route_attempt,
                )
        else:
            if self.router.route_table.default_route:
                if not is_default_route_attempt:
                    self.send_arp_request(self.router.route_table.default_route.next_hop_ip_address)
                    return self._get_arp_cache_network_interface(
                        ip_address=self.router.route_table.default_route.next_hop_ip_address,
                        is_reattempt=True,
                        is_default_route_attempt=True,
                    )
        return None

    def get_arp_cache_network_interface(self, ip_address: IPv4Address) -> Optional[RouterInterface]:
        """
        Public interface to retrieve the router interface associated with the given IP address.

        :param ip_address: The IP address for which to find the corresponding router interface.
        :type ip_address: IPv4Address
        :return: The router interface associated with the given IP address, if found; otherwise, None.
        :rtype: Optional[RouterInterface]
        """
        return self._get_arp_cache_network_interface(ip_address)

    def _process_arp_request(self, arp_packet: ARPPacket, from_network_interface: RouterInterface):
        """
        Processes an ARP request packet received on a router interface.

        If the target IP address matches the interface's IP address, generates and sends an ARP reply.

        :param arp_packet: The received ARP request packet.
        :type arp_packet: ARPPacket
        :param from_network_interface: The router interface on which the ARP request was received.
        :type from_network_interface: RouterInterface
        """
        super()._process_arp_request(arp_packet, from_network_interface)

        # If the target IP matches one of the router's NICs
        if from_network_interface.enabled and from_network_interface.ip_address == arp_packet.target_ip_address:
            arp_reply = arp_packet.generate_reply(from_network_interface.mac_address)
            self.send_arp_reply(arp_reply)
            return

    def _process_arp_reply(self, arp_packet: ARPPacket, from_network_interface: RouterInterface):
        """
        Processes an ARP reply packet received on a router interface. Updates the ARP cache with the new information.

        :param arp_packet: The received ARP reply packet.
        :type arp_packet: ARPPacket
        :param from_network_interface: The router interface on which the ARP reply was received.
        :type from_network_interface: RouterInterface
        """
        if arp_packet.target_ip_address == from_network_interface.ip_address:
            super()._process_arp_reply(arp_packet, from_network_interface)


class RouterICMP(ICMP):
    """
    The Router Internet Control Message Protocol (ICMP) service.

    Extends the ICMP service to provide router-specific functionalities for processing ICMP packets. This class is
    responsible for handling ICMP operations such as echo requests and replies in the context of a router.

    Inherits from:
        ICMP: Inherits core functionalities for handling ICMP operations, including the processing of echo requests
              and replies.
    """

    router: Optional[Router] = None

    def _process_icmp_echo_request(self, frame: Frame, from_network_interface: RouterInterface):
        """
        Processes an ICMP echo request received by the service.

        :param frame: The network frame containing the ICMP echo request.
        """
        self.sys_log.info(f"Received echo request from {frame.ip.src_ip_address}")

        network_interface = self.software_manager.session_manager.resolve_outbound_network_interface(
            frame.ip.src_ip_address
        )

        if not network_interface:
            self.sys_log.error(
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

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Processes received data, specifically handling ICMP echo requests and replies.

        This method determines the appropriate action based on the packet type and the destination IP address's
        association with the router interfaces.

        Initially, it checks if the destination IP address of the ICMP packet corresponds to any router interface. If
        the packet is not destined for an enabled interface but still matches a router interface, it is redirected
        back to the router for further processing. This ensures proper handling of packets intended for the router
        itself or needing to be routed to other destinations.

        :param payload: The payload received, expected to be an ICMP packet.
        :param session_id: The session ID associated with the received data.
        :param kwargs: Additional keyword arguments, including 'frame' (the received network frame) and
            'from_network_interface' (the router interface that received the frame).
        :return: True if the ICMP packet was processed successfully, False otherwise. False indicates either the packet
            was not ICMP, the destination IP does not correspond to an enabled router interface (and no further action
            was required), or the ICMP packet type is not handled by this method.
        """
        frame: Frame = kwargs["frame"]
        from_network_interface = kwargs["from_network_interface"]

        # Check for the presence of an ICMP payload in the frame.
        if not frame.icmp:
            return False

        # If the frame's destination IP address corresponds to any router interface, not just enabled ones.
        if not self.router.ip_is_router_interface(frame.ip.dst_ip_address):
            # If the frame is not for this router, pass it back down to the Router for potential further routing.
            self.router.process_frame(frame=frame, from_network_interface=from_network_interface)
            return True

        # Ensure the destination IP address corresponds to an enabled router interface.
        if not self.router.ip_is_router_interface(frame.ip.dst_ip_address, enabled_only=True):
            return False

        # Process ICMP echo requests and replies.
        if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
            self._process_icmp_echo_request(frame, from_network_interface)
        elif frame.icmp.icmp_type == ICMPType.ECHO_REPLY:
            self._process_icmp_echo_reply(frame)

        return True


class RouterInterface(IPWiredNetworkInterface):
    """
    Represents a Router Interface.

    Router interfaces are used to connect routers to networks. They can route packets across different networks,
    hence have IP addressing information.

    Inherits from:
    - WiredNetworkInterface: Provides properties and methods specific to wired connections.
    - Layer3Interface: Provides Layer 3 properties like ip_address and subnet_mask.
    """

    def receive_frame(self, frame: Frame) -> bool:
        """
        Receives a network frame on the interface.

        :param frame: The network frame being received.
        :return: A boolean indicating whether the frame was successfully received.
        """
        if self.enabled:
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self._connected_node.sys_log.info("Frame discarded as TTL limit reached")
                return False
            frame.set_received_timestamp()
            self.pcap.capture_inbound(frame)
            # If this destination or is broadcast
            if frame.ethernet.dst_mac_addr == self.mac_address or frame.ethernet.dst_mac_addr == "ff:ff:ff:ff:ff:ff":
                self._connected_node.receive_frame(frame=frame, from_network_interface=self)
                return True
        return False

    def __str__(self) -> str:
        """
        String representation of the NIC.

        :return: A string combining the port number, MAC address and IP address of the NIC.
        """
        return f"Port {self.port_num}: {self.mac_address}/{self.ip_address}"


class Router(NetworkNode):
    """
    Represents a network router, managing routing and forwarding of IP packets across network interfaces.

    A router operates at the network layer and is responsible for receiving, processing, and forwarding data packets
    between computer networks. It examines the destination IP address of incoming packets and determines the best way
    to route them towards their destination.

    The router integrates various network services and protocols to facilitate IP routing, including ARP (Address
    Resolution Protocol) and ICMP (Internet Control Message Protocol) for handling network diagnostics and errors.

    :ivar str hostname: The name of the router, used for identification and logging.
    :ivar int num_ports: The number of physical or logical ports on the router.
    :ivar dict kwargs: Optional keyword arguments for initializing components like SysLog, ACL (Access Control List),
        RouteTable, RouterARP, and RouterICMP services.
    """

    num_ports: int
    network_interfaces: Dict[str, RouterInterface] = {}
    "The Router Interfaces on the node."
    network_interface: Dict[int, RouterInterface] = {}
    "The Router Interfaces on the node by port id."
    acl: AccessControlList
    route_table: RouteTable

    def __init__(self, hostname: str, num_ports: int = 5, **kwargs):
        if not kwargs.get("sys_log"):
            kwargs["sys_log"] = SysLog(hostname)
        if not kwargs.get("acl"):
            kwargs["acl"] = AccessControlList(sys_log=kwargs["sys_log"], implicit_action=ACLAction.DENY)
        if not kwargs.get("route_table"):
            kwargs["route_table"] = RouteTable(sys_log=kwargs["sys_log"])
        super().__init__(hostname=hostname, num_ports=num_ports, **kwargs)
        for i in range(1, self.num_ports + 1):
            network_interface = RouterInterface(ip_address="127.0.0.1", subnet_mask="255.0.0.0", gateway="0.0.0.0")
            self.connect_nic(network_interface)
            self.network_interface[i] = network_interface

        self._set_default_acl()

        self.set_original_state()

    def _install_system_software(self):
        """
        Installs essential system software and network services on the router.

        This includes initializing and setting up RouterICMP for handling ICMP packets and RouterARP for address
        resolution within the network. These services are crucial for the router's operation, enabling it to manage
        network traffic efficiently.
        """
        self.software_manager.install(RouterICMP)
        icmp: RouterICMP = self.software_manager.icmp  # noqa
        icmp.router = self
        self.software_manager.install(RouterARP)
        arp: RouterARP = self.software_manager.arp  # noqa
        arp.router = self

    def _set_default_acl(self):
        """
        Sets default access control rules for the router.

        Initializes the router's ACL (Access Control List) with default rules, permitting essential protocols like ARP
        and ICMP, which are necessary for basic network operations and diagnostics.
        """
        self.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)
        self.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)

    def set_original_state(self):
        """
        Sets or resets the router to its original configuration state.

        This method is called to initialize the router's state or to revert it to a known good configuration during
        network simulations or after configuration changes.
        """
        self.acl.set_original_state()
        self.route_table.set_original_state()
        super().set_original_state()
        vals_to_include = {"num_ports"}
        self._original_state.update(self.model_dump(include=vals_to_include))

    def reset_component_for_episode(self, episode: int):
        """
        Resets the router's components for a new network simulation episode.

        Clears ARP cache, resets ACL and route table to their original states, and re-enables all network interfaces.
        This ensures that the router starts from a clean state for each simulation episode.

        :param episode: The episode number for which the router is being reset.
        """
        self.software_manager.arp.clear()
        self.acl.reset_component_for_episode(episode)
        self.route_table.reset_component_for_episode(episode)
        for i, network_interface in self.network_interface.items():
            network_interface.reset_component_for_episode(episode)
            self.enable_port(i)

        super().reset_component_for_episode(episode)

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()
        rm.add_request("acl", RequestType(func=self.acl._request_manager))
        return rm

    def ip_is_router_interface(self, ip_address: IPv4Address, enabled_only: bool = False) -> bool:
        """
        Checks if a given IP address belongs to any of the router's interfaces.

        :param ip_address: The IP address to check.
        :param enabled_only: If True, only considers enabled network interfaces.
        :return: True if the IP address is assigned to one of the router's interfaces; False otherwise.
        """
        for router_interface in self.network_interface.values():
            if router_interface.ip_address == ip_address:
                if enabled_only:
                    return router_interface.enabled
                else:
                    return True
        return False

    def ip_is_in_router_interface_subnet(self, ip_address: IPv4Address, enabled_only: bool = False) -> bool:
        """
        Determines if a given IP address falls within the subnet of any router interface.

        :param ip_address: The IP address to check.
        :param enabled_only: If True, only considers enabled network interfaces.
        :return: True if the IP address is within the subnet of any router's interface; False otherwise.
        """
        for router_interface in self.network_interface.values():
            if ip_address in router_interface.ip_network:
                if enabled_only:
                    return router_interface.enabled
                else:
                    return True
        return False

    def _get_port_of_nic(self, target_nic: RouterInterface) -> Optional[int]:
        """
        Retrieves the port number associated with a given network interface controller (NIC).

        :param target_nic: The NIC whose port number is being queried.
        :return: The port number if the NIC is found; otherwise, None.
        """
        for port, network_interface in self.network_interface.items():
            if network_interface == target_nic:
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

    def receive_frame(self, frame: Frame, from_network_interface: RouterInterface):
        """
        Processes an incoming frame received on one of the router's interfaces.

        Examines the frame's destination and protocol, applies ACL rules, and either forwards or drops the frame based
        on routing decisions and ACL permissions.

        :param frame: The incoming frame to be processed.
        :param from_network_interface: The router interface on which the frame was received.
        """
        if self.operating_state != NodeOperatingState.ON:
            return

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
            at_port = self._get_port_of_nic(from_network_interface)
            self.sys_log.info(f"Frame blocked at port {at_port} by rule {rule}")
            return

        if frame.ip and self.software_manager.arp:
            self.software_manager.arp.add_arp_cache_entry(
                ip_address=frame.ip.src_ip_address,
                mac_address=frame.ethernet.src_mac_addr,
                network_interface=from_network_interface,
            )

        send_to_session_manager = False
        if (frame.icmp and self.ip_is_router_interface(dst_ip_address)) or (
            dst_port in self.software_manager.get_open_ports()
        ):
            send_to_session_manager = True

        if send_to_session_manager:
            # Port is open on this Router so pass Frame up to session manager first
            self.session_manager.receive_frame(frame, from_network_interface)
        else:
            self.process_frame(frame, from_network_interface)

    def process_frame(self, frame: Frame, from_network_interface: RouterInterface) -> None:
        """
        Routes or forwards a frame based on the router's routing table and interface configurations.

        This method is called if a frame is not directly addressed to the router or does not match any open service
        ports. It determines the next hop for the frame and forwards it accordingly.

        :param frame: The frame to be routed or forwarded.
        :param from_network_interface: The network interface from which the frame originated.
        """
        # check if frame is addressed to this Router but has failed to be received by a service of application at the
        # receive_frame stage
        if frame.ip:
            for network_interface in self.network_interfaces.values():
                if network_interface.ip_address == frame.ip.dst_ip_address:
                    self.sys_log.info("Dropping frame destined for this router on a port that isn't open.")
                    return

        network_interface: RouterInterface = self.software_manager.arp.get_arp_cache_network_interface(
            frame.ip.dst_ip_address
        )
        target_mac = self.software_manager.arp.get_arp_cache_mac_address(frame.ip.dst_ip_address)

        if not target_mac:
            self.sys_log.info(f"Frame dropped as ARP cannot be resolved for {frame.ip.dst_ip_address}")
            # TODO: Send something back to src, is it some sort of ICMP?
            return

        if not network_interface:
            self.sys_log.info(f"Destination {frame.ip.dst_ip_address} is unreachable")
            # TODO: Send something back to src, is it some sort of ICMP?
            return

        if not network_interface.enabled:
            self.sys_log.info(f"Frame dropped as NIC {network_interface} is not enabled")
            # TODO: Send something back to src, is it some sort of ICMP?
            return

        if frame.ip.dst_ip_address in network_interface.ip_network:
            from_port = self._get_port_of_nic(from_network_interface)
            to_port = self._get_port_of_nic(network_interface)
            self.sys_log.info(f"Forwarding frame to internally from port {from_port} to port {to_port}")
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self.sys_log.info("Frame discarded as TTL limit reached")
                # TODO: Send something back to src, is it some sort of ICMP?
                return
            frame.ethernet.src_mac_addr = network_interface.mac_address
            frame.ethernet.dst_mac_addr = target_mac
            network_interface.send_frame(frame)
            return
        else:
            self.route_frame(frame, from_network_interface)

    def route_frame(self, frame: Frame, from_network_interface: RouterInterface) -> None:
        """
        Determines the best route for a frame and forwards it towards its destination.

        Uses the router's routing table to find the best route for the frame's destination IP address and forwards the
        frame through the appropriate interface.

        :param frame: The frame to be routed.
        :param from_network_interface: The source network interface.
        """
        route = self.route_table.find_best_route(frame.ip.dst_ip_address)
        if route:
            network_interface = self.software_manager.arp.get_arp_cache_network_interface(route.next_hop_ip_address)
            target_mac = self.software_manager.arp.get_arp_cache_mac_address(route.next_hop_ip_address)
            if not network_interface:
                self.sys_log.info(f"Destination {frame.ip.dst_ip_address} is unreachable")
                # TODO: Send something back to src, is it some sort of ICMP?
                return

            if not network_interface.enabled:
                self.sys_log.info(f"Frame dropped as NIC {network_interface} is not enabled")
                # TODO: Send something back to src, is it some sort of ICMP?
                return

            from_port = self._get_port_of_nic(from_network_interface)
            to_port = self._get_port_of_nic(network_interface)
            self.sys_log.info(f"Routing frame to internally from port {from_port} to port {to_port}")
            frame.decrement_ttl()
            if frame.ip and frame.ip.ttl < 1:
                self.sys_log.info("Frame discarded as TTL limit reached")
                # TODO: Send something back to src, is it some sort of ICMP?
                return
            frame.ethernet.src_mac_addr = network_interface.mac_address
            frame.ethernet.dst_mac_addr = target_mac
            network_interface.send_frame(frame)

    def configure_port(self, port: int, ip_address: Union[IPv4Address, str], subnet_mask: Union[IPv4Address, str]):
        """
        Configures the IP settings for a specified router port.

        :param port: The port number to configure.
        :param ip_address: The IP address to assign to the port.
        :param subnet_mask: The subnet mask for the port.
        """
        if not isinstance(ip_address, IPv4Address):
            ip_address = IPv4Address(ip_address)
        if not isinstance(subnet_mask, IPv4Address):
            subnet_mask = IPv4Address(subnet_mask)
        network_interface = self.network_interface[port]
        network_interface.ip_address = ip_address
        network_interface.subnet_mask = subnet_mask
        self.sys_log.info(f"Configured Network Interface {network_interface}")
        self.set_original_state()

    def enable_port(self, port: int):
        """
        Enables a specified port on the router.

        :param port: The port number to enable.
        """
        network_interface = self.network_interface.get(port)
        if network_interface:
            network_interface.enable()

    def disable_port(self, port: int):
        """
        Disables a specified port on the router.

        :param port: The port number to disable.
        """
        network_interface = self.network_interface.get(port)
        if network_interface:
            network_interface.disable()

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
        for port, network_interface in self.network_interface.items():
            table.add_row(
                [
                    port,
                    network_interface.mac_address,
                    f"{network_interface.ip_address}/{network_interface.ip_network.prefixlen}",
                    network_interface.speed,
                    "Enabled" if network_interface.enabled else "Disabled",
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
