from typing import Dict, Final, Optional, Union

from prettytable import MARKDOWN, PrettyTable
from pydantic import validate_call

from primaite.simulator.network.hardware.nodes.network.router import (
    AccessControlList,
    ACLAction,
    Router,
    RouterInterface,
)
from primaite.simulator.network.transmission.data_link_layer import Frame
from primaite.simulator.system.core.sys_log import SysLog
from primaite.utils.validators import IPV4Address

EXTERNAL_PORT_ID: Final[int] = 1
"""The Firewall port ID of the external port."""
INTERNAL_PORT_ID: Final[int] = 2
"""The Firewall port ID of the internal port."""
DMZ_PORT_ID: Final[int] = 3
"""The Firewall port ID of the DMZ port."""


class Firewall(Router):
    """
    A Firewall class that extends the functionality of a Router.

    The Firewall class acts as a network security system that monitors and controls incoming and outgoing
    network traffic based on predetermined security rules. It is an intermediary between internal and external
    networks (including DMZ - De-Militarized Zone), ensuring that all inbound and outbound traffic complies with
    the security policies.

    The Firewall employs Access Control Lists (ACLs) to filter traffic. Both the internal and DMZ ports have both
    inbound and outbound ACLs that determine what traffic is allowed to pass.

    In addition to the security functions, the Firewall can also perform some routing functions similar to a Router,
    forwarding packets between its interfaces based on the destination IP address.

    Usage:
        To utilise the Firewall class, instantiate it with a hostname and optionally specify sys_log for logging.
        Configure the internal, external, and DMZ ports with IP addresses and subnet masks. Define ACL rules to
        permit or deny traffic based on your security policies. The Firewall will process frames based on these
        rules, determining whether to allow or block traffic at each network interface.

    Example:
        >>> from primaite.simulator.network.transmission.network_layer import IPProtocol
        >>> from primaite.simulator.network.transmission.transport_layer import Port
        >>> firewall = Firewall(hostname="Firewall1")
        >>> firewall.configure_internal_port(ip_address="192.168.1.1", subnet_mask="255.255.255.0")
        >>> firewall.configure_external_port(ip_address="10.0.0.1", subnet_mask="255.255.255.0")
        >>> firewall.configure_dmz_port(ip_address="172.16.0.1", subnet_mask="255.255.255.0")
        >>> # Permit HTTP traffic to the DMZ
        >>> firewall.dmz_inbound_acl.add_rule(
        ...    action=ACLAction.PERMIT,
        ...    protocol=IPProtocol.TCP,
        ...    dst_port=Port.HTTP,
        ...    src_ip_address="0.0.0.0",
        ...    src_wildcard_mask="0.0.0.0",
        ...    dst_ip_address="172.16.0.0",
        ...    dst_wildcard_mask="0.0.0.255"
        ... )

    :ivar str hostname: The Firewall hostname.
    """

    internal_inbound_acl: Optional[AccessControlList] = None
    """Access Control List for managing entering the internal network."""

    internal_outbound_acl: Optional[AccessControlList] = None
    """Access Control List for managing traffic leaving the internal network."""

    dmz_inbound_acl: Optional[AccessControlList] = None
    """Access Control List for managing traffic entering the DMZ."""

    dmz_outbound_acl: Optional[AccessControlList] = None
    """Access Control List for managing traffic leaving the DMZ."""

    external_inbound_acl: Optional[AccessControlList] = None
    """Access Control List for managing traffic entering from an external network."""

    external_outbound_acl: Optional[AccessControlList] = None
    """Access Control List for managing traffic leaving towards an external network."""

    def __init__(self, hostname: str, **kwargs):
        if not kwargs.get("sys_log"):
            kwargs["sys_log"] = SysLog(hostname)

        super().__init__(hostname=hostname, num_ports=3, **kwargs)

        # Initialise ACLs for internal and dmz interfaces with a default DENY policy
        self.internal_inbound_acl = AccessControlList(
            sys_log=kwargs["sys_log"], implicit_action=ACLAction.DENY, name=f"{hostname} - Internal Inbound"
        )
        self.internal_outbound_acl = AccessControlList(
            sys_log=kwargs["sys_log"], implicit_action=ACLAction.DENY, name=f"{hostname} - Internal Outbound"
        )
        self.dmz_inbound_acl = AccessControlList(
            sys_log=kwargs["sys_log"], implicit_action=ACLAction.DENY, name=f"{hostname} - DMZ Inbound"
        )
        self.dmz_outbound_acl = AccessControlList(
            sys_log=kwargs["sys_log"], implicit_action=ACLAction.DENY, name=f"{hostname} - DMZ Outbound"
        )

        # external ACLs should have a default PERMIT policy
        self.external_inbound_acl = AccessControlList(
            sys_log=kwargs["sys_log"], implicit_action=ACLAction.PERMIT, name=f"{hostname} - External Inbound"
        )
        self.external_outbound_acl = AccessControlList(
            sys_log=kwargs["sys_log"], implicit_action=ACLAction.PERMIT, name=f"{hostname} - External Outbound"
        )

        self.set_original_state()

    def set_original_state(self):
        """Set the original state for the Firewall."""
        super().set_original_state()
        vals_to_include = {
            "internal_port",
            "external_port",
            "dmz_port",
            "internal_inbound_acl",
            "internal_outbound_acl",
            "dmz_inbound_acl",
            "dmz_outbound_acl",
            "external_inbound_acl",
            "external_outbound_acl",
        }
        self._original_state.update(self.model_dump(include=vals_to_include))

    def describe_state(self) -> Dict:
        """
        Describes the current state of the Firewall.

        :return: A dictionary representing the current state.
        """
        state = super().describe_state()

        state.update(
            {
                "internal_port": self.internal_port.describe_state(),
                "external_port": self.external_port.describe_state(),
                "dmz_port": self.dmz_port.describe_state(),
                "internal_inbound_acl": self.internal_inbound_acl.describe_state(),
                "internal_outbound_acl": self.internal_outbound_acl.describe_state(),
                "dmz_inbound_acl": self.dmz_inbound_acl.describe_state(),
                "dmz_outbound_acl": self.dmz_outbound_acl.describe_state(),
                "external_inbound_acl": self.external_inbound_acl.describe_state(),
                "external_outbound_acl": self.external_outbound_acl.describe_state(),
            }
        )

        return state

    def show(self, markdown: bool = False):
        """
        Displays the current configuration of the firewall's network interfaces in a table format.

        The table includes information about each port (External, Internal, DMZ), their MAC addresses, IP
        configurations, link speeds, and operational status. The output can be formatted as Markdown if specified.

        :param markdown: If True, formats the output table in Markdown style. Useful for documentation or reporting
        purposes within Markdown-compatible platforms.
        """
        table = PrettyTable(["Port", "MAC Address", "Address", "Speed", "Status"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.hostname} Network Interfaces"
        ports = {"External": self.external_port, "Internal": self.internal_port, "DMZ": self.dmz_port}
        for port, network_interface in ports.items():
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

    def show_rules(self, external: bool = True, internal: bool = True, dmz: bool = True, markdown: bool = False):
        """
        Prints the configured ACL rules for each specified network zone of the firewall.

        This method allows selective viewing of ACL rules applied to external, internal, and DMZ interfaces, providing
        a clear overview of the firewall's current traffic filtering policies. Each section can be independently
        toggled.

        :param external: If True, shows ACL rules for external interfaces.
        :param internal: If True, shows ACL rules for internal interfaces.
        :param dmz: If True, shows ACL rules for DMZ interfaces.
        :param markdown: If True, formats the output in Markdown, enhancing readability in Markdown-compatible viewers.
        """
        print(f"{self.hostname} Firewall Rules")
        print()
        if external:
            self.external_inbound_acl.show(markdown)
            print()
            self.external_outbound_acl.show(markdown)
            print()
        if internal:
            self.internal_inbound_acl.show(markdown)
            print()
            self.internal_outbound_acl.show(markdown)
            print()
        if dmz:
            self.dmz_inbound_acl.show(markdown)
            print()
            self.dmz_outbound_acl.show(markdown)
            print()

    def receive_frame(self, frame: Frame, from_network_interface: RouterInterface):
        """
        Receive a frame and process it.

        Acts as the primary entry point for all network frames arriving at the Firewall, determining the flow of
        traffic based on the source network interface controller (NIC) and applying the appropriate Access Control
        List (ACL) rules.

        This method categorizes the incoming traffic into three main pathways based on the source NIC: external inbound,
        internal outbound, and DMZ (De-Militarized Zone) outbound. It plays a crucial role in enforcing the firewall's
        security policies by directing each frame to the corresponding processing method that evaluates it against
        specific ACL rules.

        Based on the originating NIC:
        - Frames from the external port are processed as external inbound traffic, potentially destined for either the
          DMZ or the internal network.
        - Frames from the internal port are treated as internal outbound traffic, aimed at reaching the external
          network or a service within the DMZ.
        - Frames from the DMZ port are handled as DMZ outbound traffic, with potential destinations including the
          internal network or the external network.

        :param frame: The network frame to be processed.
        :param from_network_interface: The network interface controller from which the frame is coming. Used to
            determine the direction of the traffic (inbound or outbound) and the zone (external, internal,
            DMZ) it belongs to.
        """
        # If the frame comes from the external port, it's considered as external inbound traffic
        if from_network_interface == self.external_port:
            self._process_external_inbound_frame(frame, from_network_interface)
            return
        # If the frame comes from the internal port, it's considered as internal outbound traffic
        elif from_network_interface == self.internal_port:
            self._process_internal_outbound_frame(frame, from_network_interface)
            return
        # If the frame comes from the DMZ port, it's considered as DMZ outbound traffic
        elif from_network_interface == self.dmz_port:
            self._process_dmz_outbound_frame(frame, from_network_interface)
            return

    def _process_external_inbound_frame(self, frame: Frame, from_network_interface: RouterInterface) -> None:
        """
        Process frames arriving from the external network.

        Determines the path for frames based on their destination IP addresses and ACL rules for the external inbound
        interface. Frames destined for the DMZ or internal network are forwarded accordingly, if allowed by the ACL.

        If a frame is permitted by the ACL, it is either passed to the session manager (if applicable) or forwarded to
        the appropriate network zone (DMZ/internal). Denied frames are logged and dropped.

        :param frame: The frame to be processed, containing network layer and transport layer information.
        :param from_network_interface: The interface on the firewall through which the frame was received.
        """
        # check if External Inbound ACL Rules permit frame
        permitted, rule = self.external_inbound_acl.is_permitted(frame)
        if not permitted:
            self.sys_log.info(f"Frame blocked at interface {from_network_interface} by rule {rule}")
            return
        self.software_manager.arp.add_arp_cache_entry(
            ip_address=frame.ip.src_ip_address,
            mac_address=frame.ethernet.src_mac_addr,
            network_interface=from_network_interface,
        )

        if self.check_send_frame_to_session_manager(frame):
            # Port is open on this Router so pass Frame up to session manager first
            self.session_manager.receive_frame(frame, from_network_interface)
        else:
            # If the destination IP is within the DMZ network, process the frame as DMZ inbound
            if frame.ip.dst_ip_address in self.dmz_port.ip_network:
                self._process_dmz_inbound_frame(frame, from_network_interface)
            else:
                # Otherwise, process the frame as internal inbound
                self._process_internal_inbound_frame(frame, from_network_interface)

    def _process_external_outbound_frame(self, frame: Frame, from_network_interface: RouterInterface) -> None:
        """
        Process frames that are outbound towards the external network.

        :param frame: The frame to be processed.
        :param from_network_interface: The network interface controller from which the frame is coming.
        :param re_attempt: Indicates if the processing is a re-attempt, defaults to False.
        """
        # check if External Outbound ACL Rules permit frame
        permitted, rule = self.external_outbound_acl.is_permitted(frame=frame)
        if not permitted:
            self.sys_log.info(f"Frame blocked at interface {from_network_interface} by rule {rule}")
            return

        self.process_frame(frame=frame, from_network_interface=from_network_interface)

    def _process_internal_inbound_frame(self, frame: Frame, from_network_interface: RouterInterface) -> None:
        """
        Process frames that are inbound towards the internal LAN.

        This method is responsible for handling frames coming from either the external network or the DMZ towards
        the internal LAN. It checks the frames against the internal inbound ACL to decide whether to allow or deny
        the traffic, and take appropriate actions.

        :param frame: The frame to be processed.
        :param from_network_interface: The network interface controller from which the frame is coming.
        :param re_attempt: Indicates if the processing is a re-attempt, defaults to False.
        """
        # check if Internal Inbound ACL Rules permit frame
        permitted, rule = self.internal_inbound_acl.is_permitted(frame=frame)
        if not permitted:
            self.sys_log.info(f"Frame blocked at interface {from_network_interface} by rule {rule}")
            return

        self.process_frame(frame=frame, from_network_interface=from_network_interface)

    def _process_internal_outbound_frame(self, frame: Frame, from_network_interface: RouterInterface) -> None:
        """
        Process frames that are outbound from the internal network.

        This method handles frames that are leaving the internal network. Depending on the destination IP address,
        the frame may be forwarded to the DMZ or to the external network.

        :param frame: The frame to be processed.
        :param from_network_interface: The network interface controller from which the frame is coming.
        :param re_attempt: Indicates if the processing is a re-attempt, defaults to False.
        """
        permitted, rule = self.internal_outbound_acl.is_permitted(frame)
        if not permitted:
            self.sys_log.info(f"Frame blocked at interface {from_network_interface} by rule {rule}")
            return
        self.software_manager.arp.add_arp_cache_entry(
            ip_address=frame.ip.src_ip_address,
            mac_address=frame.ethernet.src_mac_addr,
            network_interface=from_network_interface,
        )

        if self.check_send_frame_to_session_manager(frame):
            # Port is open on this Router so pass Frame up to session manager first
            self.session_manager.receive_frame(frame, from_network_interface)
        else:
            # If the destination IP is within the DMZ network, process the frame as DMZ inbound
            if frame.ip.dst_ip_address in self.dmz_port.ip_network:
                self._process_dmz_inbound_frame(frame, from_network_interface)
            else:
                # If the destination IP is not within the DMZ network, process the frame as external outbound
                self._process_external_outbound_frame(frame, from_network_interface)

    def _process_dmz_inbound_frame(self, frame: Frame, from_network_interface: RouterInterface) -> None:
        """
        Process frames that are inbound from the DMZ.

        This method is responsible for handling frames coming from either the external network or the internal LAN
        towards the DMZ. It checks the frames against the DMZ inbound ACL to decide whether to allow or deny the
        traffic, and take appropriate actions.

        :param frame: The frame to be processed.
        :param from_network_interface: The network interface controller from which the frame is coming.
        :param re_attempt: Indicates if the processing is a re-attempt, defaults to False.
        """
        # check if DMZ Inbound ACL Rules permit frame
        permitted, rule = self.dmz_inbound_acl.is_permitted(frame=frame)
        if not permitted:
            self.sys_log.info(f"Frame blocked at interface {from_network_interface} by rule {rule}")
            return

        self.process_frame(frame=frame, from_network_interface=from_network_interface)

    def _process_dmz_outbound_frame(self, frame: Frame, from_network_interface: RouterInterface) -> None:
        """
        Process frames that are outbound from the DMZ.

        This method handles frames originating from the DMZ and determines their appropriate path based on the
        destination IP address. It involves checking the DMZ outbound ACL, consulting the ARP cache and the routing
        table to find the correct outbound NIC, and then forwarding the frame to either the internal network or the
        external network.

        :param frame: The frame to be processed.
        :param from_network_interface: The network interface controller from which the frame is coming.
        :param re_attempt: Indicates if the processing is a re-attempt, defaults to False.
        """
        permitted, rule = self.dmz_outbound_acl.is_permitted(frame)
        if not permitted:
            self.sys_log.info(f"Frame blocked at interface {from_network_interface} by rule {rule}")
            return
        self.software_manager.arp.add_arp_cache_entry(
            ip_address=frame.ip.src_ip_address,
            mac_address=frame.ethernet.src_mac_addr,
            network_interface=from_network_interface,
        )

        if self.check_send_frame_to_session_manager(frame):
            # Port is open on this Router so pass Frame up to session manager first
            self.session_manager.receive_frame(frame, from_network_interface)
        else:
            # Attempt to get the outbound NIC from the ARP cache using the destination IP address
            outbound_nic = self.software_manager.arp.get_arp_cache_network_interface(frame.ip.dst_ip_address)

            # If outbound NIC is not found in the ARP cache, consult the routing table to find the best route
            if not outbound_nic:
                route = self.route_table.find_best_route(frame.ip.dst_ip_address)
                if route:
                    # If a route is found, get the corresponding outbound NIC from the ARP cache using the next-hop IP
                    # address
                    outbound_nic = self.software_manager.arp.get_arp_cache_network_interface(route.next_hop_ip_address)

            # If an outbound NIC is determined
            if outbound_nic:
                if outbound_nic == self.external_port:
                    # If the outbound NIC is the external port, check the frame against the DMZ outbound ACL and
                    # process it as an external outbound frame
                    self._process_external_outbound_frame(frame, from_network_interface)
                    return
                elif outbound_nic == self.internal_port:
                    # If the outbound NIC is the internal port, check the frame against the DMZ outbound ACL and
                    # process it as an internal inbound frame
                    self._process_internal_inbound_frame(frame, from_network_interface)
                    return
        # TODO: What to do here? Destination unreachable? Send ICMP back?
        return

    @property
    def external_port(self) -> RouterInterface:
        """
        The external port of the firewall.

        :return: The external port connecting the firewall to the external network.
        """
        return self.network_interface[EXTERNAL_PORT_ID]

    @validate_call()
    def configure_external_port(self, ip_address: Union[IPV4Address, str], subnet_mask: Union[IPV4Address, str]):
        """
        Configure the external port with an IP address and a subnet mask.

        Enables the port once configured.

        :param ip_address: The IP address to assign to the external port.
        :param subnet_mask: The subnet mask to assign to the external port.
        """
        # Configure the external port with the specified IP address and subnet mask
        self.configure_port(EXTERNAL_PORT_ID, ip_address, subnet_mask)
        self.external_port.enable()

    @property
    def internal_port(self) -> RouterInterface:
        """
        The internal port of the firewall.

        :return: The external port connecting the firewall to the internal LAN.
        """
        return self.network_interface[INTERNAL_PORT_ID]

    @validate_call()
    def configure_internal_port(self, ip_address: Union[IPV4Address, str], subnet_mask: Union[IPV4Address, str]):
        """
        Configure the internal port with an IP address and a subnet mask.

        Enables the port once configured.

        :param ip_address: The IP address to assign to the internal port.
        :param subnet_mask: The subnet mask to assign to the internal port.
        """
        self.configure_port(INTERNAL_PORT_ID, ip_address, subnet_mask)
        self.internal_port.enable()

    @property
    def dmz_port(self) -> RouterInterface:
        """
        The DMZ port of the firewall.

        :return: The external port connecting the firewall to the DMZ.
        """
        return self.network_interface[DMZ_PORT_ID]

    @validate_call()
    def configure_dmz_port(self, ip_address: Union[IPV4Address, str], subnet_mask: Union[IPV4Address, str]):
        """
        Configure the DMZ port with an IP address and a subnet mask.

        Enables the port once configured.

        :param ip_address: The IP address to assign to the DMZ port.
        :param subnet_mask: The subnet mask to assign to the DMZ port.
        """
        self.configure_port(DMZ_PORT_ID, ip_address, subnet_mask)
        self.dmz_port.enable()
