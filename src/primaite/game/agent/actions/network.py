# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat


class NetworkPortEnableAction(AbstractAction):
    """Action which enables are port on a router or a firewall."""

    def __init__(self, manager: "ActionManager", max_nics_per_node: int, **kwargs) -> None:
        """Init method for NetworkPortEnableAction.

        :param max_nics_per_node: Maximum number of NICs per node.
        :type max_nics_per_node: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"port_id": max_nics_per_node}

    def form_request(self, target_nodename: str, port_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if target_nodename is None or port_id is None:
            return ["do_nothing"]
        return ["network", "node", target_nodename, "network_interface", port_id, "enable"]


class NetworkPortDisableAction(AbstractAction):
    """Action which disables are port on a router or a firewall."""

    def __init__(self, manager: "ActionManager", max_nics_per_node: int, **kwargs) -> None:
        """Init method for NetworkPortDisableAction.

        :param max_nics_per_node: Maximum number of NICs per node.
        :type max_nics_per_node: int
        """
        super().__init__(manager=manager)
        self.shape: Dict[str, int] = {"port_id": max_nics_per_node}

    def form_request(self, target_nodename: str, port_id: int) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if target_nodename is None or port_id is None:
            return ["do_nothing"]
        return ["network", "node", target_nodename, "network_interface", port_id, "disable"]
