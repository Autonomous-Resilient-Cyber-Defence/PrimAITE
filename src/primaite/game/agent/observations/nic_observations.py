from __future__ import annotations

from typing import Dict, Optional

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE


class NICObservation(AbstractObservation, identifier="NETWORK_INTERFACE"):
    """Status information about a network interface within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for NICObservation."""

        nic_num: int
        """Number of the network interface."""
        include_nmne: Optional[bool] = None
        """Whether to include number of malicious network events (NMNE) in the observation."""

    def __init__(self, where: WhereType, include_nmne: bool) -> None:
        """
        Initialise a network interface observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this interface.
            A typical location for a network interface might be
            ['network', 'nodes', <node_hostname>, 'NICs', <nic_num>].
        :type where: WhereType
        :param include_nmne: Flag to determine whether to include NMNE information in the observation.
        :type include_nmne: bool
        """
        self.where = where
        self.include_nmne: bool = include_nmne

        self.default_observation: ObsType = {"nic_status": 0}
        if self.include_nmne:
            self.default_observation.update({"NMNE": {"inbound": 0, "outbound": 0}})

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status of the network interface and optionally NMNE information.
        :rtype: ObsType
        """
        nic_state = access_from_nested_dict(state, self.where)

        if nic_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {"nic_status": 1 if nic_state["enabled"] else 2}
        if self.include_nmne:
            obs.update({"NMNE": {}})
            direction_dict = nic_state["nmne"].get("direction", {})
            inbound_keywords = direction_dict.get("inbound", {}).get("keywords", {})
            inbound_count = inbound_keywords.get("*", 0)
            outbound_keywords = direction_dict.get("outbound", {}).get("keywords", {})
            outbound_count = outbound_keywords.get("*", 0)
            obs["NMNE"]["inbound"] = self._categorise_mne_count(inbound_count - self.nmne_inbound_last_step)
            obs["NMNE"]["outbound"] = self._categorise_mne_count(outbound_count - self.nmne_outbound_last_step)
            self.nmne_inbound_last_step = inbound_count
            self.nmne_outbound_last_step = outbound_count
        return obs

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for network interface status and NMNE information.
        :rtype: spaces.Space
        """
        space = spaces.Dict({"nic_status": spaces.Discrete(3)})

        if self.include_nmne:
            space["NMNE"] = spaces.Dict({"inbound": spaces.Discrete(4), "outbound": spaces.Discrete(4)})

        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> NICObservation:
        """
        Create a network interface observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the network interface observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this NIC's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed network interface observation instance.
        :rtype: NICObservation
        """
        return cls(where=parent_where + ["NICs", config.nic_num], include_nmne=config.include_nmne)


class PortObservation(AbstractObservation, identifier="PORT"):
    """Port observation, provides status information about a network port within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for PortObservation."""

        port_id: int
        """Identifier of the port, used for querying simulation state dictionary."""

    def __init__(self, where: WhereType) -> None:
        """
        Initialise a port observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this port.
            A typical location for a port might be ['network', 'nodes', <node_hostname>, 'NICs', <port_id>].
        :type where: WhereType
        """
        self.where = where
        self.default_observation: ObsType = {"operating_status": 0}

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the operating status of the port.
        :rtype: ObsType
        """
        port_state = access_from_nested_dict(state, self.where)
        if port_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {"operating_status": 1 if port_state["enabled"] else 2}

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for port status.
        :rtype: spaces.Space
        """
        return spaces.Dict({"operating_status": spaces.Discrete(3)})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> PortObservation:
        """
        Create a port observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the port observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this port's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed port observation instance.
        :rtype: PortObservation
        """
        return cls(where=parent_where + ["NICs", config.port_id])
