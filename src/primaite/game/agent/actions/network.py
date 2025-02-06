# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

from abc import ABC
from typing import ClassVar

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = ("NetworkPortEnableAction", "NetworkPortDisableAction")


class NetworkPortAbstractAction(AbstractAction, ABC):
    """Base class for Network port actions."""

    class ConfigSchema(AbstractAction.ConfigSchema, ABC):
        """Base configuration schema for NetworkPort actions."""

        target_nodename: str
        port_num: int
        verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.target_nodename is None or config.port_num is None:
            return ["do-nothing"]
        return [
            "network",
            "node",
            config.target_nodename,
            "network_interface",
            config.port_num,
            config.verb,
        ]


class NetworkPortEnableAction(NetworkPortAbstractAction, discriminator="network-port-enable"):
    """Action which enables are port on a router or a firewall."""

    config: "NetworkPortEnableAction.ConfigSchema"

    class ConfigSchema(NetworkPortAbstractAction.ConfigSchema):
        """Configuration schema for NetworkPortEnableAction."""

        verb: ClassVar[str] = "enable"


class NetworkPortDisableAction(NetworkPortAbstractAction, discriminator="network-port-disable"):
    """Action which disables are port on a router or a firewall."""

    config: "NetworkPortDisableAction.ConfigSchema"

    class ConfigSchema(NetworkPortAbstractAction.ConfigSchema):
        """Configuration schema for NetworkPortDisableAction."""

        verb: ClassVar[str] = "disable"
