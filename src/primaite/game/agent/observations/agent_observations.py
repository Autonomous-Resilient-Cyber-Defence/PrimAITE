from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from gymnasium import spaces

from primaite.game.agent.observations.host import NodeObservation
from primaite.game.agent.observations.observations import (
    AbstractObservation,
    AclObservation,
    ICSObservation,
    LinkObservation,
    NullObservation,
)

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class UC2BlueObservation(AbstractObservation):
    """Container for all observations used by the blue agent in UC2.

    TODO: there's no real need for a UC2 blue container class, we should be able to simply use the observation handler
        for the purpose of compiling several observation components.
    """

    def __init__(
        self,
        nodes: List[NodeObservation],
        links: List[LinkObservation],
        acl: AclObservation,
        ics: ICSObservation,
        where: Optional[List[str]] = None,
    ) -> None:
        """Initialise UC2 blue observation.

        :param nodes: List of node observations
        :type nodes: List[NodeObservation]
        :param links: List of link observations
        :type links: List[LinkObservation]
        :param acl: The Access Control List observation
        :type acl: AclObservation
        :param ics: The ICS observation
        :type ics: ICSObservation
        :param where: Where in the simulation state dict to find information. Not used in this particular observation
            because it only compiles other observations and doesn't contribute any new information, defaults to None
        :type where: Optional[List[str]], optional
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

        self.nodes: List[NodeObservation] = nodes
        self.links: List[LinkObservation] = links
        self.acl: AclObservation = acl
        self.ics: ICSObservation = ics

        self.default_observation: Dict = {
            "NODES": {i + 1: n.default_observation for i, n in enumerate(self.nodes)},
            "LINKS": {i + 1: l.default_observation for i, l in enumerate(self.links)},
            "ACL": self.acl.default_observation,
            "ICS": self.ics.default_observation,
        }

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation

        obs = {}
        obs["NODES"] = {i + 1: node.observe(state) for i, node in enumerate(self.nodes)}
        obs["LINKS"] = {i + 1: link.observe(state) for i, link in enumerate(self.links)}
        obs["ACL"] = self.acl.observe(state)
        obs["ICS"] = self.ics.observe(state)

        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Space
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                "NODES": spaces.Dict({i + 1: node.space for i, node in enumerate(self.nodes)}),
                "LINKS": spaces.Dict({i + 1: link.space for i, link in enumerate(self.links)}),
                "ACL": self.acl.space,
                "ICS": self.ics.space,
            }
        )

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "UC2BlueObservation":
        """Create UC2 blue observation from a config.

        :param config: Dictionary containing the configuration for this UC2 blue observation. This includes the nodes,
            links, ACL and ICS observations.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :return: Constructed UC2 blue observation
        :rtype: UC2BlueObservation
        """
        node_configs = config["nodes"]

        num_services_per_node = config["num_services_per_node"]
        num_folders_per_node = config["num_folders_per_node"]
        num_files_per_folder = config["num_files_per_folder"]
        num_nics_per_node = config["num_nics_per_node"]
        nodes = [
            NodeObservation.from_config(
                config=n,
                game=game,
                num_services_per_node=num_services_per_node,
                num_folders_per_node=num_folders_per_node,
                num_files_per_folder=num_files_per_folder,
                num_nics_per_node=num_nics_per_node,
            )
            for n in node_configs
        ]

        link_configs = config["links"]
        links = [LinkObservation.from_config(config=link, game=game) for link in link_configs]

        acl_config = config["acl"]
        acl = AclObservation.from_config(config=acl_config, game=game)

        ics_config = config["ics"]
        ics = ICSObservation.from_config(config=ics_config, game=game)
        new = cls(nodes=nodes, links=links, acl=acl, ics=ics, where=["network"])
        return new

