# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
from typing import Type, Union

from primaite.nodes.active_node import ActiveNode
from primaite.nodes.passive_node import PassiveNode
from primaite.nodes.service_node import ServiceNode

NodeUnion: Type = Union[ActiveNode, PassiveNode, ServiceNode]
"""A Union of ActiveNode, PassiveNode, and ServiceNode."""
