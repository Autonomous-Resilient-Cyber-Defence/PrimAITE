# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from typing import ClassVar, List, Optional, Union

from primaite.game.agent.actions.manager import AbstractAction
from primaite.interface.request import RequestFormat

__all__ = (
    "NodeOSScanAction",
    "NodeShutdownAction",
    "NodeStartupAction",
    "NodeResetAction",
    "NodeNMAPPingScanAction",
    "NodeNMAPPortScanAction",
    "NodeNetworkServiceReconAction",
)


class NodeAbstractAction(AbstractAction, identifier="node_abstract"):
    """
    Abstract base class for node actions.

    Any action which applies to a node and uses node_name as its only parameter can inherit from this base class.
    """

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base Configuration schema for Node actions."""

        node_name: str

    verb: ClassVar[str]

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return ["network", "node", config.node_name, cls.verb]


class NodeOSScanAction(NodeAbstractAction, identifier="node_os_scan"):
    """Action which scans a node's OS."""

    class ConfigSchema(NodeAbstractAction.ConfigSchema):
        """Configuration schema for NodeOSScanAction."""

        verb: str = "scan"


class NodeShutdownAction(NodeAbstractAction, identifier="node_shutdown"):
    """Action which shuts down a node."""

    class ConfigSchema(NodeAbstractAction.ConfigSchema):
        """Configuration schema for NodeShutdownAction."""

        verb: str = "shutdown"


class NodeStartupAction(NodeAbstractAction, identifier="node_startup"):
    """Action which starts up a node."""

    class ConfigSchema(NodeAbstractAction.ConfigSchema):
        """Configuration schema for NodeStartupAction."""

        verb: str = "startup"


class NodeResetAction(NodeAbstractAction, identifier="node_reset"):
    """Action which resets a node."""

    class ConfigSchema(NodeAbstractAction.ConfigSchema):
        """Configuration schema for NodeResetAction."""

        verb: str = "reset"


class NodeNMAPAbstractAction(AbstractAction, identifier="node_nmap_abstract_action"):
    """Base class for NodeNMAP actions."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Base Configuration Schema for NodeNMAP actions."""

        target_ip_address: Union[str, List[str]]
        show: bool = False
        node_name: str

    @classmethod
    @abstractmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        pass


class NodeNMAPPingScanAction(NodeNMAPAbstractAction, identifier="node_nmap_ping_scan"):
    """Action which performs an NMAP ping scan."""

    class ConfigSchema(NodeNMAPAbstractAction.ConfigSchema):
        """Configuration schema for NodeNMAPPingScanAction."""

        pass

    @classmethod
    def form_request(cls, config: ConfigSchema) -> List[str]:  # noqa
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.node_name,
            "application",
            "NMAP",
            "ping_scan",
            {"target_ip_address": config.target_ip_address, "show": config.show},
        ]


class NodeNMAPPortScanAction(NodeNMAPAbstractAction, identifier="node_nmap_port_scan"):
    """Action which performs an NMAP port scan."""

    class ConfigSchema(NodeNMAPAbstractAction.ConfigSchema):
        """Configuration Schema for NodeNMAPPortScanAction."""

        source_node: str
        target_protocol: Optional[Union[str, List[str]]] = (None,)
        target_port: Optional[Union[str, List[str]]] = (None,)
        show: Optional[bool] = (False,)

    @classmethod
    def form_request(
        cls,
        config: ConfigSchema,
    ) -> List[str]:  # noqa
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.source_node,
            "application",
            "NMAP",
            "port_scan",
            {
                "target_ip_address": config.target_ip_address,
                "target_port": config.target_port,
                "target_protocol": config.target_protocol,
                "show": config.show,
            },
        ]


class NodeNetworkServiceReconAction(NodeNMAPAbstractAction, identifier="node_network_service_recon"):
    """Action which performs an NMAP network service recon (ping scan followed by port scan)."""

    class ConfigSchema(AbstractAction.ConfigSchema):
        """Configuration schema for NodeNetworkServiceReconAction."""

        target_protocol: Optional[Union[str, List[str]]] = (None,)
        target_port: Optional[Union[str, List[str]]] = (None,)
        show: Optional[bool] = (False,)

    @classmethod
    def form_request(
        cls,
        config: ConfigSchema,
    ) -> List[str]:  # noqa
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        return [
            "network",
            "node",
            config.source_node,
            "application",
            "NMAP",
            "network_service_recon",
            {
                "target_ip_address": config.target_ip_address,
                "target_port": config.target_port,
                "target_protocol": config.target_protocol,
                "show": config.show,
            },
        ]
