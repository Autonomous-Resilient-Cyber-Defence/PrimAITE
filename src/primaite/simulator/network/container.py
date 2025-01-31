# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import networkx as nx
from networkx import MultiGraph
from prettytable import MARKDOWN, PrettyTable
from pydantic import Field

from primaite import getLogger
from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.network.airspace import AirSpace
from primaite.simulator.network.hardware.base import Link, Node, WiredNetworkInterface
from primaite.simulator.network.hardware.nodes.host.host_node import HostNode
from primaite.simulator.network.hardware.nodes.host.server import Printer
from primaite.simulator.network.hardware.nodes.network.network_node import NetworkNode
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.services.service import Service

_LOGGER = getLogger(__name__)


class Network(SimComponent):
    """
    Top level container object representing the physical network.

    This class manages nodes, links, and other network components. It also
    offers methods for rendering the network topology and gathering states.

    :ivar Dict[str, Node] nodes: Dictionary mapping node UUIDs to Node instances.
    :ivar Dict[str, Link] links: Dictionary mapping link UUIDs to Link instances.
    """

    nodes: Dict[str, Node] = {}

    links: Dict[str, Link] = {}
    airspace: AirSpace = Field(default_factory=lambda: AirSpace())
    _node_id_map: Dict[int, Node] = {}
    _link_id_map: Dict[int, Node] = {}

    def __init__(self, **kwargs):
        """
        Initialise the network.

        Constructs the network and sets up its initial state including
        the request manager and an empty MultiGraph for topology representation.
        """
        super().__init__(**kwargs)

        self._nx_graph = MultiGraph()

    def setup_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        for node in self.nodes.values():
            node.setup_for_episode(episode=episode)
        for link in self.links.values():
            link.setup_for_episode(episode=episode)

        for node in self.nodes.values():
            node.power_on()

            for network_interface in node.network_interfaces.values():
                network_interface.enable()
            # Reset software
            for software in node.software_manager.software.values():
                if isinstance(software, Service):
                    software.start()
                elif isinstance(software, Application):
                    software.run()

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        self._node_request_manager = RequestManager()
        rm.add_request(
            "node",
            RequestType(func=self._node_request_manager),
        )
        return rm

    def apply_timestep(self, timestep: int) -> None:
        """Apply a timestep evolution to this the network and its nodes and links."""
        super().apply_timestep(timestep=timestep)
        # apply timestep to nodes
        for node_id in self.nodes:
            self.nodes[node_id].apply_timestep(timestep=timestep)

        # apply timestep to links
        for link_id in self.links:
            self.links[link_id].apply_timestep(timestep=timestep)

    def pre_timestep(self, timestep: int) -> None:
        """Apply pre-timestep logic."""
        super().pre_timestep(timestep)

        self.airspace.reset_bandwidth_load()

        for node in self.nodes.values():
            node.pre_timestep(timestep)

        for link in self.links.values():
            link.pre_timestep(timestep)

    @property
    def router_nodes(self) -> List[Node]:
        """The Routers in the Network."""
        return [node for node in self.nodes.values() if node.__class__.__name__ == "Router"]

    @property
    def switch_nodes(self) -> List[Node]:
        """The Switches in the Network."""
        return [node for node in self.nodes.values() if node.__class__.__name__ == "Switch"]

    @property
    def computer_nodes(self) -> List[Node]:
        """The Computers in the Network."""
        return [node for node in self.nodes.values() if node.__class__.__name__ == "Computer"]

    @property
    def server_nodes(self) -> List[Node]:
        """The Servers in the Network."""
        return [node for node in self.nodes.values() if node.__class__.__name__ == "Server"]

    @property
    def firewall_nodes(self) -> List[Node]:
        """The Firewalls in the Network."""
        return [node for node in self.nodes.values() if node.__class__.__name__ == "Firewall"]

    @property
    def extended_hostnodes(self) -> List[Node]:
        """Extended nodes that inherited HostNode in the network."""
        return [node for node in self.nodes.values() if node.__class__.__name__.lower() in HostNode._registry]

    @property
    def extended_networknodes(self) -> List[Node]:
        """Extended nodes that inherited NetworkNode in the network."""
        return [node for node in self.nodes.values() if node.__class__.__name__.lower() in NetworkNode._registry]

    @property
    def printer_nodes(self) -> List[Node]:
        """The printers on the network."""
        return [node for node in self.nodes.values() if isinstance(node, Printer)]

    @property
    def wireless_router_nodes(self) -> List[Node]:
        """The Routers in the Network."""
        return [node for node in self.nodes.values() if node.__class__.__name__ == "WirelessRouter"]

    def show(self, nodes: bool = True, ip_addresses: bool = True, links: bool = True, markdown: bool = False):
        """
        Print tables describing the Network.

        Generate and print PrettyTable instances that show details about nodes,
        IP addresses, and links in the network. Output can be in Markdown format.

        :param nodes: Include node details in the output. Defaults to True.
        :param ip_addresses: Include IP address details in the output. Defaults to True.
        :param links: Include link details in the output. Defaults to True.
        :param markdown: Use Markdown style in table output. Defaults to False.
        """
        nodes_type_map = {
            "Router": self.router_nodes,
            "Firewall": self.firewall_nodes,
            "Switch": self.switch_nodes,
            "Server": self.server_nodes,
            "Computer": self.computer_nodes,
            "Printer": self.printer_nodes,
            "Wireless Router": self.wireless_router_nodes,
        }

        if nodes:
            table = PrettyTable(["Node", "Type", "Operating State"])
            if markdown:
                table.set_style(MARKDOWN)
            table.align = "l"
            table.title = "Nodes"
            for node in self.nodes.values():
                table.add_row((node.hostname, type(node)._discriminator, node.operating_state.name))
            print(table)

        if ip_addresses:
            table = PrettyTable(["Node", "Port", "IP Address", "Subnet Mask", "Default Gateway"])
            if markdown:
                table.set_style(MARKDOWN)
            table.align = "l"
            table.title = "IP Addresses"
            for nodes in nodes_type_map.values():
                for node in nodes:
                    for i, port in node.network_interface.items():
                        if hasattr(port, "ip_address"):
                            if port.ip_address != IPv4Address("127.0.0.1"):
                                port_str = port.port_name if port.port_name else port.port_num
                                table.add_row(
                                    [node.hostname, port_str, port.ip_address, port.subnet_mask, node.default_gateway]
                                )
            print(table)

        if links:
            table = PrettyTable(
                ["Endpoint A", "A Port", "Endpoint B", "B Port", "is Up", "Bandwidth (MBits)", "Current Load"]
            )
            if markdown:
                table.set_style(MARKDOWN)
            table.align = "l"
            table.title = "Links"
            links = list(self.links.values())
            for nodes in nodes_type_map.values():
                for node in nodes:
                    for link in links[::-1]:
                        if node in [link.endpoint_a.parent, link.endpoint_b.parent]:
                            table.add_row(
                                [
                                    link.endpoint_a.parent.hostname,
                                    str(link.endpoint_a),
                                    link.endpoint_b.parent.hostname,
                                    str(link.endpoint_b),
                                    link.is_up,
                                    link.bandwidth,
                                    link.current_load_percent,
                                ]
                            )
                            links.remove(link)
            print(table)

    def clear_links(self):
        """Clear all the links in the network by resetting their component state for the episode."""
        for link in self.links.values():
            link.setup_for_episode(episode=0)  # TODO: shouldn't be using this method here.

    def draw(self, seed: int = 123):
        """
        Draw the Network using NetworkX and matplotlib.pyplot.

        :param seed: An integer seed for reproducible layouts. Default is 123.
        """
        pos = nx.spring_layout(self._nx_graph, seed=seed)
        nx.draw(self._nx_graph, pos, with_labels=True)
        plt.show()

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of the Network.

        :return: A dictionary capturing the current state of the Network and its child objects.
        """
        state = super().describe_state()
        state.update(
            {
                "nodes": {node.hostname: node.describe_state() for node in self.nodes.values()},
                "links": {},
            }
        )
        # Update the links one-by-one. The key is a 4-tuple of `hostname_a, port_a, hostname_b, port_b`
        for _, link in self.links.items():
            node_a = link.endpoint_a._connected_node
            node_b = link.endpoint_b._connected_node
            hostname_a = node_a.hostname if node_a else None
            hostname_b = node_b.hostname if node_b else None
            port_a = link.endpoint_a.port_num
            port_b = link.endpoint_b.port_num
            link_key = f"{hostname_a}:eth-{port_a}<->{hostname_b}:eth-{port_b}"
            state["links"][link_key] = link.describe_state()
            state["links"][link_key]["hostname_a"] = hostname_a
            state["links"][link_key]["hostname_b"] = hostname_b
            state["links"][link_key]["port_a"] = port_a
            state["links"][link_key]["port_b"] = port_b

        return state

    def add_node(self, node: Node) -> None:
        """
        Add an existing node to the network.

        .. note:: If the node is already present in the network, a warning is logged.

        :param node: Node instance that should be kept track of by the network.
        """
        if node in self:
            _LOGGER.warning(f"Can't add node {node.uuid}. It is already in the network.")
            return
        self.nodes[node.uuid] = node
        self._node_id_map[len(self.nodes)] = node
        node.parent = self
        self._nx_graph.add_node(node.hostname)
        _LOGGER.debug(f"Added node {node.uuid} to Network {self.uuid}")
        self._node_request_manager.add_request(name=node.hostname, request_type=RequestType(func=node._request_manager))

    def get_node_by_hostname(self, hostname: str) -> Optional[Node]:
        """
        Get a Node from the Network by its hostname.

        .. note:: Assumes hostnames on the network are unique.

        :param hostname: The Node hostname.
        :return: The Node if it exists in the network.
        """
        for node in self.nodes.values():
            if node.hostname == hostname:
                return node

    def remove_node(self, node: Node) -> None:
        """
        Remove a node from the network.

        .. note:: If the node is not found in the network, a warning is logged.

        :param node: Node instance that is currently part of the network that should be removed.
        :type node: Node
        """
        if node not in self:
            _LOGGER.warning(f"Can't remove node {node.hostname}. It's not in the network.")
            return
        self.nodes.pop(node.uuid)
        for i, _node in self._node_id_map.items():
            if node == _node:
                self._node_id_map.pop(i)
                break
        node.parent = None
        self._node_request_manager.remove_request(name=node.hostname)
        _LOGGER.info(f"Removed node {node.hostname} from network {self.uuid}")

    def connect(
        self, endpoint_a: WiredNetworkInterface, endpoint_b: WiredNetworkInterface, bandwidth: int = 100, **kwargs
    ) -> Optional[Link]:
        """
        Connect two endpoints on the network by creating a link between their NICs/SwitchPorts.

        .. note:: If the nodes owning the endpoints are not already in the network, they are automatically added.

        :param endpoint_a: The first endpoint to connect.
        :type endpoint_a: WiredNetworkInterface
        :param endpoint_b: The second endpoint to connect.
        :type endpoint_b: WiredNetworkInterface
        :param bandwidth: bandwidth of new link, default of 100mbps
        :type bandwidth: int
        :raises RuntimeError: If any validation or runtime checks fail.
        """
        node_a: Node = endpoint_a.parent
        node_b: Node = endpoint_b.parent
        if node_a not in self:
            self.add_node(node_a)
        if node_b not in self:
            self.add_node(node_b)
        if node_a is node_b:
            _LOGGER.warning(f"Cannot link endpoint {endpoint_a} to {endpoint_b} because they belong to the same node.")
            return
        link = Link(endpoint_a=endpoint_a, endpoint_b=endpoint_b, bandwidth=bandwidth, **kwargs)
        self.links[link.uuid] = link
        self._link_id_map[len(self.links)] = link
        self._nx_graph.add_edge(endpoint_a.parent.hostname, endpoint_b.parent.hostname)
        link.parent = self
        _LOGGER.debug(f"Added link {link.uuid} to connect {endpoint_a} and {endpoint_b}")
        return link

    def remove_link(self, link: Link) -> None:
        """Disconnect a link from the network.

        :param link: The link to be removed
        :type link: Link
        """
        link.endpoint_a.disconnect_link()
        link.endpoint_b.disconnect_link()
        self.links.pop(link.uuid)
        for i, _link in self._link_id_map.items():
            if link == _link:
                self._link_id_map.pop(i)
                break
        link.parent = None
        _LOGGER.info(f"Removed link {link.uuid} from network {self.uuid}.")

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Node):
            return item.uuid in self.nodes
        elif isinstance(item, Link):
            return item.uuid in self.links
        return False
