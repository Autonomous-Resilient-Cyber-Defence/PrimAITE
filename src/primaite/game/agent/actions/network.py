# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

from typing import ClassVar, Dict, Optional

from pydantic import BaseModel, ConfigDict

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat


class NetworkPortAbstractAction(AbstractAction):
    """Base class for Network port actions"""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base configuration schema for NetworkPort actions."""
        target_nodename: str
        port_id: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.target_nodename is None or  config.port_id is None:
            return ["do_nothing"]
        return ["network", "node", config.target_nodename, "network_interface", config.port_id, cls.verb]


class NetworkPortEnableAction(NetworkPortAbstractAction, identifier="network_port_enable"):
    """Action which enables are port on a router or a firewall."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for NetworkPortEnableAction."""

        verb: str = "enable"

class NetworkPortDisableAction(NetworkPortAbstractAction, identifier="network_port_disable"):
    """Action which disables are port on a router or a firewall."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for NetworkPortDisableAction"""

        verb: str = "disable"

