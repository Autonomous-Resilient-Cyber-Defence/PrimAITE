# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import ClassVar

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = ("HostNICEnableAction", "HostNICDisableAction")


class HostNICAbstractAction(AbstractAction, identifier="host_nic_abstract"):
    """
    Abstract base class for NIC actions.

    Any action which applies to a NIC and uses node_id and nic_id as its only two parameters can inherit from this base
    class.
    """

    config: "HostNICAbstractAction.ConfigSchema"

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base Configuration schema for HostNIC actions."""

        node_name: str
        nic_num: int
        verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.nic_num is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "network_interface",
            config.nic_num,
            config.verb,
        ]


class HostNICEnableAction(HostNICAbstractAction, identifier="host_nic_enable"):
    """Action which enables a NIC."""

    config: "HostNICEnableAction.ConfigSchema"

    class ConfigSchema(HostNICAbstractAction.ConfigSchema):
        """Configuration schema for HostNICEnableAction."""

        verb: str = "enable"


class HostNICDisableAction(HostNICAbstractAction, identifier="host_nic_disable"):
    """Action which disables a NIC."""

    config: "HostNICDisableAction.ConfigSchema"

    class ConfigSchema(HostNICAbstractAction.ConfigSchema):
        """Configuration schema for HostNICDisableAction."""

        verb: str = "disable"
