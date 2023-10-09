from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import networkx as nx
from networkx import MultiGraph
from prettytable import MARKDOWN, PrettyTable

from primaite import getLogger
from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.network.hardware.base import Link, NIC, Node, SwitchPort
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.router import Router
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch

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

    def _init_request_manager(self) -> RequestManager:
        am = super()._init_request_manager()
        self._node_request_manager = RequestManager()
        am.add_request(
            "node",
            RequestType(func=self._node_request_manager),
        )
        return am

    @property
    def routers(self) -> List[Router]:
        """The Routers in the Network."""
        return [node for node in self.nodes.values() if isinstance(node, Router)]

    @property
    def switches(self) -> List[Switch]:
        """The Switches in the Network."""
        return [node for node in self.nodes.values() if isinstance(node, Switch)]

    @property
    def computers(self) -> List[Computer]:
        """The Computers in the Network."""
        return [node for node in self.nodes.values() if isinstance(node, Computer) and not isinstance(node, Server)]

    @property
    def servers(self) -> List[Server]:
        """The Servers in the Network."""
        return [node for node in self.nodes.values() if isinstance(node, Server)]

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
            "Router": self.routers,
            "Switch": self.switches,
            "Server": self.servers,
            "Computer": self.computers,
        }
        if nodes:
            table = PrettyTable(["Node", "Type", "Operating State"])
            if markdown:
                table.set_style(MARKDOWN)
            table.align = "l"
            table.title = "Nodes"
            for node_type, nodes in nodes_type_map.items():
                for node in nodes:
                    table.add_row([node.hostname, node_type, node.operating_state.name])
            print(table)

        if ip_addresses:
            table = PrettyTable(["Node", "Port", "IP Address", "Subnet Mask", "Default Gateway"])
            if markdown:
                table.set_style(MARKDOWN)
            table.align = "l"
            table.title = "IP Addresses"
            for nodes in nodes_type_map.values():
                for node in nodes:
                    for i, port in node.ethernet_port.items():
                        table.add_row([node.hostname, i, port.ip_address, port.subnet_mask, node.default_gateway])
            print(table)

        if links:
            table = PrettyTable(["Endpoint A", "Endpoint B", "is Up", "Bandwidth (MBits)", "Current Load"])
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
                                    link.endpoint_b.parent.hostname,
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
            link.reset_component_for_episode()

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
                "nodes": {uuid: node.describe_state() for uuid, node in self.nodes.items()},
                "links": {uuid: link.describe_state() for uuid, link in self.links.items()},
            }
        )
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
        _LOGGER.info(f"Added node {node.uuid} to Network {self.uuid}")
        self._node_request_manager.add_request(name=node.uuid, request_type=RequestType(func=node._request_manager))

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
            _LOGGER.warning(f"Can't remove node {node.uuid}. It's not in the network.")
            return
        self.nodes.pop(node.uuid)
        for i, _node in self._node_id_map.items():
            if node == _node:
                self._node_id_map.pop(i)
                break
        node.parent = None
        _LOGGER.info(f"Removed node {node.uuid} from network {self.uuid}")
        self._node_request_manager.remove_request(name=node.uuid)

    def connect(
        self, endpoint_a: Union[NIC, SwitchPort], endpoint_b: Union[NIC, SwitchPort], **kwargs
    ) -> Optional[Link]:
        """
        Connect two endpoints on the network by creating a link between their NICs/SwitchPorts.

        .. note:: If the nodes owning the endpoints are not already in the network, they are automatically added.

        :param endpoint_a: The first endpoint to connect.
        :type endpoint_a: Union[NIC, SwitchPort]
        :param endpoint_b: The second endpoint to connect.
        :type endpoint_b: Union[NIC, SwitchPort]
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
        link = Link(endpoint_a=endpoint_a, endpoint_b=endpoint_b, **kwargs)
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
