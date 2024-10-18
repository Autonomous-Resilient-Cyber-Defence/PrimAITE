# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat


class HostNICAbstractAction(AbstractAction):
    """
    Abstract base class for NIC actions.

    Any action which applies to a NIC and uses node_id and nic_id as its only two parameters can inherit from this base
    class.
    """

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base Configuration schema for HostNIC actions."""

        num_nodes: str
        max_nics_per_node: str
        node_name: str
        nic_num: str

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.nic_num is None:
            return ["do_nothing"]
        return ["network", "node", config.node_name, "network_interface", config.nic_num, cls.verb]


class HostNICEnableAction(HostNICAbstractAction):
    """Action which enables a NIC."""

    class ConfigSchema(HostNICAbstractAction.ConfigSchema):
        """Configuration schema for HostNICEnableAction."""

        verb: str = "enable"


class HostNICDisableAction(HostNICAbstractAction):
    """Action which disables a NIC."""

    class ConfigSchema(HostNICAbstractAction.ConfigSchema):
        """Configuration schema for HostNICDisableAction."""

        verb: str = "disable"
