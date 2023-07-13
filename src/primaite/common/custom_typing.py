from typing import TypeVar

from primaite.nodes.active_node import ActiveNode
from primaite.nodes.passive_node import PassiveNode
from primaite.nodes.service_node import ServiceNode

NodeUnion = TypeVar("NodeUnion", ServiceNode, ActiveNode, PassiveNode)
"""A Union of ActiveNode, PassiveNode, and ServiceNode."""
