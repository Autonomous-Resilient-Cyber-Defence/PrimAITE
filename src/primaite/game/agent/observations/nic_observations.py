from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from gymnasium import spaces

from primaite.game.agent.observations.observations import AbstractObservation
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE
from primaite.simulator.network.nmne import CAPTURE_NMNE

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class NicObservation(AbstractObservation):
    """Observation of a Network Interface Card (NIC) in the network."""

    low_nmne_threshold: int = 0
    """The minimum number of malicious network events to be considered low."""
    med_nmne_threshold: int = 5
    """The minimum number of malicious network events to be considered medium."""
    high_nmne_threshold: int = 10
    """The minimum number of malicious network events to be considered high."""

    global CAPTURE_NMNE

    @property
    def default_observation(self) -> Dict:
        """The default NIC observation dict."""
        data = {"nic_status": 0}
        if CAPTURE_NMNE:
            data.update({"nmne": {"inbound": 0, "outbound": 0}})

        return data

    def __init__(
        self,
        where: Optional[Tuple[str]] = None,
        low_nmne_threshold: Optional[int] = 0,
        med_nmne_threshold: Optional[int] = 5,
        high_nmne_threshold: Optional[int] = 10,
    ) -> None:
        """Initialise NIC observation.

        :param where: Where in the simulation state dictionary to find the relevant information for this NIC. A typical
            example may look like this:
            ['network','nodes',<node_hostname>,'NICs',<nic_number>]
            If None, this denotes that the NIC does not exist and the observation will be populated with zeroes.
        :type where: Optional[Tuple[str]], optional
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

        global CAPTURE_NMNE
        if CAPTURE_NMNE:
            self.nmne_inbound_last_step: int = 0
            """NMNEs persist for the whole episode, but we want to count per step. Keeping track of last step count lets
              us find the difference."""
            self.nmne_outbound_last_step: int = 0
            """NMNEs persist for the whole episode, but we want to count per step. Keeping track of last step count lets
              us find the difference."""

        if low_nmne_threshold or med_nmne_threshold or high_nmne_threshold:
            self._validate_nmne_categories(
                low_nmne_threshold=low_nmne_threshold,
                med_nmne_threshold=med_nmne_threshold,
                high_nmne_threshold=high_nmne_threshold,
            )

    def _validate_nmne_categories(
        self, low_nmne_threshold: int = 0, med_nmne_threshold: int = 5, high_nmne_threshold: int = 10
    ):
        """
        Validates the nmne threshold config.

        If the configuration is valid, the thresholds will be set, otherwise, an exception is raised.

        :param: low_nmne_threshold: The minimum number of malicious network events to be considered low
        :param: med_nmne_threshold: The minimum number of malicious network events to be considered medium
        :param: high_nmne_threshold: The minimum number of malicious network events to be considered high
        """
        if high_nmne_threshold <= med_nmne_threshold:
            raise Exception(
                f"nmne_categories: high nmne count ({high_nmne_threshold}) must be greater "
                f"than medium nmne count ({med_nmne_threshold})"
            )

        if med_nmne_threshold <= low_nmne_threshold:
            raise Exception(
                f"nmne_categories: medium nmne count ({med_nmne_threshold}) must be greater "
                f"than low nmne count ({low_nmne_threshold})"
            )

        self.high_nmne_threshold = high_nmne_threshold
        self.med_nmne_threshold = med_nmne_threshold
        self.low_nmne_threshold = low_nmne_threshold

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

    def observe(self, state: Dict) -> Dict:
        """Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        :return: Observation
        :rtype: Dict
        """
        if self.where is None:
            return self.default_observation
        nic_state = access_from_nested_dict(state, self.where)

        if nic_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        else:
            obs_dict = {"nic_status": 1 if nic_state["enabled"] else 2}
            if CAPTURE_NMNE:
                obs_dict.update({"nmne": {}})
                direction_dict = nic_state["nmne"].get("direction", {})
                inbound_keywords = direction_dict.get("inbound", {}).get("keywords", {})
                inbound_count = inbound_keywords.get("*", 0)
                outbound_keywords = direction_dict.get("outbound", {}).get("keywords", {})
                outbound_count = outbound_keywords.get("*", 0)
                obs_dict["nmne"]["inbound"] = self._categorise_mne_count(inbound_count - self.nmne_inbound_last_step)
                obs_dict["nmne"]["outbound"] = self._categorise_mne_count(outbound_count - self.nmne_outbound_last_step)
                self.nmne_inbound_last_step = inbound_count
                self.nmne_outbound_last_step = outbound_count
            return obs_dict

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        space = spaces.Dict({"nic_status": spaces.Discrete(3)})

        if CAPTURE_NMNE:
            space["nmne"] = spaces.Dict({"inbound": spaces.Discrete(4), "outbound": spaces.Discrete(4)})

        return space

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame", parent_where: Optional[List[str]]) -> "NicObservation":
        """Create NIC observation from a config.

        :param config: Dictionary containing the configuration for this NIC observation.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        :param parent_where: Where in the simulation state dictionary to find the information about this NIC's parent
            node. A typical location for a node ``where`` can be: ['network','nodes',<node_hostname>]
        :type parent_where: Optional[List[str]]
        :return: Constructed NIC observation
        :rtype: NicObservation
        """
        low_nmne_threshold = None
        med_nmne_threshold = None
        high_nmne_threshold = None

        if game and game.options and game.options.thresholds and game.options.thresholds.get("nmne"):
            threshold = game.options.thresholds["nmne"]

            low_nmne_threshold = int(threshold.get("low")) if threshold.get("low") is not None else None
            med_nmne_threshold = int(threshold.get("medium")) if threshold.get("medium") is not None else None
            high_nmne_threshold = int(threshold.get("high")) if threshold.get("high") is not None else None

        return cls(
            where=parent_where + ["NICs", config["nic_num"]],
            low_nmne_threshold=low_nmne_threshold,
            med_nmne_threshold=med_nmne_threshold,
            high_nmne_threshold=high_nmne_threshold,
        )
