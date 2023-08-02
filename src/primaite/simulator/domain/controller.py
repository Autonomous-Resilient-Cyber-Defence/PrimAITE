from typing import Set, TypeAlias

from primaite.simulator.core import SimComponent
from primaite.simulator.domain import Account

__temp_node = TypeAlias()  # placeholder while nodes don't exist


class DomainController(SimComponent):
    """Main object for controlling the domain."""

    nodes: Set(__temp_node) = set()
    accounts: Set(Account) = set()
