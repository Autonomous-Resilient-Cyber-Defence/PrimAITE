# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import Any, Dict, List

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite import getLogger
from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)


class LinkObservation(AbstractObservation, identifier="LINK"):
    """Link observation, providing information about a specific link within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for LinkObservation."""

        link_reference: str
        """Reference identifier for the link."""

    def __init__(self, where: WhereType) -> None:
        """
        Initialise a link observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this link.
            A typical location for a link might be ['network', 'links', <link_reference>].
        :type where: WhereType
        """
        self.where = where
        self.default_observation: ObsType = {"PROTOCOLS": {"ALL": 0}}

    def observe(self, state: Dict) -> Any:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing information about the link.
        :rtype: Any
        """
        link_state = access_from_nested_dict(state, self.where)
        if link_state is NOT_PRESENT_IN_STATE:
            self.where[-1] = "<->".join(self.where[-1].split("<->")[::-1])  # try swapping endpoint A and B
            link_state = access_from_nested_dict(state, self.where)
            if link_state is NOT_PRESENT_IN_STATE:
                return self.default_observation

        bandwidth = link_state["bandwidth"]
        load = link_state["current_load"]
        if load == 0:
            utilisation_category = 0
        else:
            utilisation_fraction = load / bandwidth
            utilisation_category = int(utilisation_fraction * 9) + 1

        return {"PROTOCOLS": {"ALL": min(utilisation_category, 10)}}

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for link status.
        :rtype: spaces.Space
        """
        return spaces.Dict({"PROTOCOLS": spaces.Dict({"ALL": spaces.Discrete(11)})})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> LinkObservation:
        """
        Create a link observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the link observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this link.
            A typical location might be ['network', 'links', <link_reference>].
        :type parent_where: WhereType, optional
        :return: Constructed link observation instance.
        :rtype: LinkObservation
        """
        link_reference = config.link_reference
        if parent_where == []:
            where = ["network", "links", link_reference]
        else:
            where = parent_where + ["links", link_reference]
        return cls(where=where)


class LinksObservation(AbstractObservation, identifier="LINKS"):
    """Collection of link observations representing multiple links within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for LinksObservation."""

        link_references: List[str]
        """List of reference identifiers for the links."""

    def __init__(self, where: WhereType, links: List[LinkObservation]) -> None:
        """
        Initialise a links observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for these links.
            A typical location for links might be ['network', 'links'].
        :type where: WhereType
        :param links: List of link observations.
        :type links: List[LinkObservation]
        """
        self.where: WhereType = where
        self.links: List[LinkObservation] = links
        self.default_observation: ObsType = {i + 1: l.default_observation for i, l in enumerate(self.links)}

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing information about multiple links.
        :rtype: ObsType
        """
        return {i + 1: l.observe(state) for i, l in enumerate(self.links)}

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for multiple links.
        :rtype: spaces.Space
        """
        return spaces.Dict({i + 1: l.space for i, l in enumerate(self.links)})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> LinksObservation:
        """
        Create a links observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the links observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about these links.
            A typical location might be ['network'].
        :type parent_where: WhereType, optional
        :return: Constructed links observation instance.
        :rtype: LinksObservation
        """
        where = parent_where + ["network"]
        link_cfgs = [LinkObservation.ConfigSchema(link_reference=ref) for ref in config.link_references]
        links = [LinkObservation.from_config(c, parent_where=where) for c in link_cfgs]
        return cls(where=where, links=links)
