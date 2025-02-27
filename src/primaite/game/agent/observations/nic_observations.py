# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import ClassVar, Dict, List, Optional

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE
from primaite.simulator.network.nmne import NMNEConfig
from primaite.utils.validation.ip_protocol import IPProtocol
from primaite.utils.validation.port import Port


class NICObservation(AbstractObservation, discriminator="network-interface"):
    """Status information about a network interface within the simulation environment."""

    capture_nmne: ClassVar[bool] = NMNEConfig().capture_nmne
    "A Boolean specifying whether malicious network events should be captured."

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for NICObservation."""

        nic_num: int
        """Number of the network interface."""
        include_nmne: Optional[bool] = None
        """Whether to include number of malicious network events (NMNE) in the observation."""
        monitored_traffic: Optional[Dict[IPProtocol, List[Port]]] = None
        """A dict containing which traffic types are to be included in the observation."""

    def __init__(
        self,
        where: WhereType,
        include_nmne: bool,
        monitored_traffic: Optional[Dict] = None,
        thresholds: Dict = {},
    ) -> None:
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
            self.nmne_inbound_last_step: int = 0
            self.nmne_outbound_last_step: int = 0

        if thresholds.get("nmne") is None:
            self.low_nmne_threshold = 0
            self.med_nmne_threshold = 5
            self.high_nmne_threshold = 10
        else:
            self._set_nmne_threshold(
                thresholds=[
                    thresholds.get("nmne")["low"],
                    thresholds.get("nmne")["medium"],
                    thresholds.get("nmne")["high"],
                ]
            )

        self.monitored_traffic = monitored_traffic
        if self.monitored_traffic:
            self.default_observation.update(
                self._default_monitored_traffic_observation(monitored_traffic_config=monitored_traffic)
            )

    def _default_monitored_traffic_observation(self, monitored_traffic_config: Dict) -> Dict:
        default_traffic_obs = {"TRAFFIC": {}}

        for protocol in self.monitored_traffic:
            protocol = str(protocol).lower()
            default_traffic_obs["TRAFFIC"][protocol] = {}

            if protocol == "icmp":
                default_traffic_obs["TRAFFIC"]["icmp"] = {"inbound": 0, "outbound": 0}
            else:
                default_traffic_obs["TRAFFIC"][protocol] = {}
                for port in self.monitored_traffic[protocol]:
                    default_traffic_obs["TRAFFIC"][protocol][port] = {"inbound": 0, "outbound": 0}

        return default_traffic_obs

    def _categorise_mne_count(self, nmne_count: int) -> int:
        """
        Categorise the number of Malicious Network Events (NMNEs) into discrete bins.

        This helps in classifying the severity or volume of MNEs into manageable levels for the agent.

        Bins are defined as follows:
        - 0: No MNEs detected (0 events).
        - 1: Low number of MNEs (default 1-5 events).
        - 2: Moderate number of MNEs (default 6-10 events).
        - 3: High number of MNEs (default more than 10 events).

        :param nmne_count: Number of MNEs detected.
        :return: Bin number corresponding to the number of MNEs. Returns 0, 1, 2, or 3 based on the detected MNE count.
        """
        if nmne_count > self.high_nmne_threshold:
            return 3
        elif nmne_count > self.med_nmne_threshold:
            return 2
        elif nmne_count > self.low_nmne_threshold:
            return 1
        return 0

    def _categorise_traffic(self, traffic_value: float, nic_state: Dict) -> int:
        """Categorise the traffic into discrete categories."""
        if traffic_value == 0:
            return 0

        nic_max_bandwidth = nic_state.get("speed")

        bandwidth_utilisation = traffic_value / nic_max_bandwidth
        return int(bandwidth_utilisation * 9) + 1

    def _set_nmne_threshold(self, thresholds: List[int]):
        """
        Method that validates and then sets the NMNE threshold.

        :param: thresholds: The NMNE threshold to validate and set.
        """
        if self._validate_thresholds(
            thresholds=thresholds,
            threshold_identifier="nmne",
        ):
            self.low_nmne_threshold = thresholds[0]
            self.med_nmne_threshold = thresholds[1]
            self.high_nmne_threshold = thresholds[2]

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status of the network interface and optionally NMNE information.
        :rtype: ObsType
        """
        nic_state = access_from_nested_dict(state, self.where)

        if nic_state is NOT_PRESENT_IN_STATE or self.where is None:
            return self.default_observation

        obs = {"nic_status": 1 if nic_state["enabled"] else 2}

        # if the observation was configured to monitor traffic from ports/protocols
        if self.monitored_traffic:
            obs["TRAFFIC"] = {}

            # iterate through the protocols
            for protocol in self.monitored_traffic:
                protocol = str(protocol).lower()
                obs["TRAFFIC"][protocol] = {}
                # check if the nic has seen traffic with this protocol
                if nic_state["traffic"].get(protocol):
                    # deal with icmp
                    if protocol == "icmp":
                        obs["TRAFFIC"][protocol] = {
                            "inbound": self._categorise_traffic(
                                traffic_value=nic_state["traffic"]["icmp"]["inbound"], nic_state=nic_state
                            ),
                            "outbound": self._categorise_traffic(
                                traffic_value=nic_state["traffic"]["icmp"]["outbound"], nic_state=nic_state
                            ),
                        }
                    else:
                        for port in self.monitored_traffic[protocol]:
                            obs["TRAFFIC"][protocol][port] = {}
                            traffic = {"inbound": 0, "outbound": 0}

                            if nic_state["traffic"][protocol].get(port) is not None:
                                traffic = nic_state["traffic"][protocol][port]

                            obs["TRAFFIC"][protocol][port]["inbound"] = self._categorise_traffic(
                                traffic_value=traffic["inbound"], nic_state=nic_state
                            )
                            obs["TRAFFIC"][protocol][port]["outbound"] = self._categorise_traffic(
                                traffic_value=traffic["outbound"], nic_state=nic_state
                            )

                # set all the ports under the protocol to 0
                else:
                    if protocol == "icmp":
                        obs["TRAFFIC"]["icmp"] = {"inbound": 0, "outbound": 0}
                    else:
                        for port in self.monitored_traffic[protocol]:
                            obs["TRAFFIC"][protocol][port] = {"inbound": 0, "outbound": 0}

        if self.capture_nmne and self.include_nmne:
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

        if self.monitored_traffic:
            space["TRAFFIC"] = spaces.Dict({})
            for protocol in self.monitored_traffic:
                protocol = str(protocol).lower()
                if protocol == "icmp":
                    space["TRAFFIC"]["icmp"] = spaces.Dict(
                        {"inbound": spaces.Discrete(11), "outbound": spaces.Discrete(11)}
                    )
                else:
                    space["TRAFFIC"][protocol] = spaces.Dict({})
                    for port in self.monitored_traffic[protocol]:
                        space["TRAFFIC"][protocol][port] = spaces.Dict(
                            {"inbound": spaces.Discrete(11), "outbound": spaces.Discrete(11)}
                        )

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
        return cls(
            where=parent_where + ["NICs", config.nic_num],
            include_nmne=config.include_nmne,
            monitored_traffic=config.monitored_traffic,
            thresholds=config.thresholds,
        )


class PortObservation(AbstractObservation, discriminator="port"):
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
