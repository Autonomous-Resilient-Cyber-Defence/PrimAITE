from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING

from gymnasium import spaces
from gymnasium.core import ObsType
from pydantic import BaseModel, ConfigDict, model_validator, ValidationError

from primaite.game.agent.observations.observations import AbstractObservation, WhereType

if TYPE_CHECKING:
    from primaite.game.game import PrimaiteGame


class NestedObservation(AbstractObservation, identifier="CUSTOM"):
    """Observation type that allows combining other observations into a gymnasium.spaces.Dict space."""

    class NestedObservationItem(BaseModel):
        """One list item of the config."""

        model_config = ConfigDict(extra="forbid")
        type: str
        """Select observation class. It maps to the identifier of the obs class by checking the registry."""
        label: str
        """Dict key in the final observation space."""
        options: Dict
        """Options to pass to the observation class from_config method."""

        @model_validator(mode="after")
        def check_model(self) -> "NestedObservation.NestedObservationItem":
            """Make sure tha the config options match up with the selected observation type."""
            obs_subclass_name = self.type
            obs_options = self.options
            if obs_subclass_name not in AbstractObservation._registry:
                raise ValueError(f"Observation of type {obs_subclass_name} could not be found.")
            obs_schema = AbstractObservation._registry[obs_subclass_name].ConfigSchema
            try:
                obs_schema(**obs_options)
            except ValidationError as e:
                raise ValueError(f"Observation options did not match schema, got this error: {e}")
            return self

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for NestedObservation."""

        components: List[NestedObservation.NestedObservationItem] = []
        """List of observation components to be part of this space."""

    def __init__(self, components: Dict[str, AbstractObservation]) -> None:
        """Initialise nested observation."""
        self.components: Dict[str, AbstractObservation] = components
        """Maps label: observation object"""

        self.default_observation = {label: obs.default_observation for label, obs in self.components.items()}
        """Default observation is just the default observations of constituents."""

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the status information about the host.
        :rtype: ObsType
        """
        return {label: obs.observe(state) for label, obs in self.components.items()}

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the nested observation space.
        :rtype: spaces.Space
        """
        return spaces.Dict({label: obs.space for label, obs in self.components.items()})

    @classmethod
    def from_config(cls, config: ConfigSchema, game: "PrimaiteGame", parent_where: WhereType = []) -> NestedObservation:
        """
        Read the Nested observation config and create all defined subcomponents.

        Example configuration that utilises NestedObservation:
        This lets us have different options for different types of hosts.

        ```yaml
            observation_space:
            - type: CUSTOM
                options:
                components:

                    - type: HOSTS
                    label: COMPUTERS # What is the dictionary key called
                    options:
                        hosts:
                            - client_1
                            - client_2
                        num_services: 0
                        num_applications: 5
                        ... # other options

                    - type: HOSTS
                    label: SERVERS # What is the dictionary key called
                    options:
                        hosts:
                        - hostname: database_server
                        - hostname: web_server
                        num_services: 4
                        num_applications: 0
                        num_folders: 2
                        num_files: 2

        ```
        """
        instances = dict()
        for component in config.components:
            obs_class = AbstractObservation._registry[component.type]
            obs_instance = obs_class.from_config(config=obs_class.ConfigSchema(**component.options), game=game)
            instances[component.label] = obs_instance
        return cls(components=instances)


class ObservationManager:
    """
    Manage the observations of an Agent.

    The observation space has the purpose of:
      1. Reading the outputted state from the PrimAITE Simulation.
      2. Selecting parts of the simulation state that are requested by the simulation config
      3. Formatting this information so an agent can use it to make decisions.
    """

    def __init__(self, obs: AbstractObservation) -> None:
        """Initialise observation space.

        :param observation: Observation object
        :type observation: AbstractObservation
        """
        self.obs: AbstractObservation = obs
        self.current_observation: ObsType
        """Cached copy of the observation at the time it was most recently calculated."""

    def update(self, state: Dict) -> Dict:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary
        :type state: Dict
        """
        self.current_observation = self.obs.observe(state)
        return self.current_observation

    @property
    def space(self) -> None:
        """Gymnasium space object describing the observation space shape."""
        return self.obs.space

    @classmethod
    def from_config(cls, config: Dict, game: "PrimaiteGame") -> "ObservationManager":
        """
        Create observation space from a config.

        :param config: Dictionary containing the configuration for this observation space.
            It should contain the key 'type' which selects which observation class to use (from a choice of:
            UC2BlueObservation, UC2RedObservation, UC2GreenObservation)
            The other key is 'options' which are passed to the constructor of the selected observation class.
        :type config: Dict
        :param game: Reference to the PrimaiteGame object that spawned this observation.
        :type game: PrimaiteGame
        """
        obs_type = config["type"]
        obs_class = AbstractObservation._registry[obs_type]
        observation = obs_class.from_config(config=obs_class.ConfigSchema(**config["options"]), game=game)
        obs_manager = cls(observation)
        return obs_manager
