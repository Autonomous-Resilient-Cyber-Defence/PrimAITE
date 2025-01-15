# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from functools import cached_property
from typing import Any, Dict, List, Optional

from gymnasium import spaces
from gymnasium.core import ObsType
from pydantic import BaseModel, computed_field, ConfigDict, Field, model_validator, ValidationError

from primaite.game.agent.observations.observations import AbstractObservation, WhereType


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
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> NestedObservation:
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
            obs_instance = obs_class.from_config(config=obs_class.ConfigSchema(**component.options))
            instances[component.label] = obs_instance
        return cls(components=instances)


class NullObservation(AbstractObservation, identifier="NONE"):
    """Empty observation that acts as a placeholder."""

    def __init__(self) -> None:
        """Initialise the empty observation."""
        self.default_observation = 0

    def observe(self, state: Dict) -> Any:
        """Simply return 0."""
        return 0

    @property
    def space(self) -> spaces.Space:
        """Essentially empty space."""
        return spaces.Discrete(1)

    @classmethod
    def from_config(cls, config: NullObservation.ConfigSchema, parent_where: WhereType = []) -> NullObservation:
        """Instantiate a NullObservation. Accepts parameters to comply with API."""
        return cls()


class ObservationManager(BaseModel):
    """
    Manage the observations of an Agent.

    The observation space has the purpose of:
      1. Reading the outputted state from the PrimAITE Simulation.
      2. Selecting parts of the simulation state that are requested by the simulation config
      3. Formatting this information so an agent can use it to make decisions.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    class ConfigSchema(BaseModel):
        """Config Schema for Observation Manager."""

        model_config = ConfigDict(extra="forbid")
        type: str = "NONE"
        """Identifier name for the top-level observation."""
        options: AbstractObservation.ConfigSchema = Field(
            default_factory=lambda: NullObservation.ConfigSchema(), validate_default=True
        )
        """Options to pass into the top-level observation during creation."""

        @model_validator(mode="before")
        @classmethod
        def resolve_obs_options_type(cls, data: Any) -> Any:
            """
            When constructing the model from a dict, resolve the correct observation class based on `type` field.

            Workaround: The `options` field is statically typed as AbstractObservation. Therefore, it falls over when
            passing in data that adheres to a subclass schema rather than the plain AbstractObservation schema. There is
            a way to do this properly using discriminated union, but most advice on the internet assumes that the full
            list of types between which to discriminate is known ahead-of-time. That is not the case for us, because of
            our plugin architecture.

            We may be able to revisit and implement a better solution when needed using the following resources as
            research starting points:
            https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions
            https://github.com/pydantic/pydantic/issues/7366
            https://github.com/pydantic/pydantic/issues/7462
            https://github.com/pydantic/pydantic/pull/7983
            """
            if not isinstance(data, dict):
                return data

            # (TODO: duplicate default definition between here and the actual model)
            obs_type = data["type"] if "type" in data else "NONE"
            obs_class = AbstractObservation._registry[obs_type]

            # if no options are passed in, try to create a default schema. Only works if there are no mandatory fields
            if "options" not in data:
                data["options"] = obs_class.ConfigSchema()

            # if options passed as a dict, convert to a schema
            elif isinstance(data["options"], dict):
                data["options"] = obs_class.ConfigSchema(**data["options"])

            return data

    config: ConfigSchema = Field(default_factory=lambda: ObservationManager.ConfigSchema())

    current_observation: ObsType = 0

    @computed_field
    @cached_property
    def obs(self) -> AbstractObservation:
        """Create the main observation component for the observation manager from the config."""
        obs_class = AbstractObservation._registry[self.config.type]
        obs_instance = obs_class.from_config(config=self.config.options)
        return obs_instance

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
    def from_config(cls, config: Optional[Dict]) -> "ObservationManager":
        """
        Create observation space from a config.

        :param config: Dictionary containing the configuration for this observation space.
            If None, a blank observation space is created.
            Otherwise, this must be a Dict with a type field and options field.
            type: string that corresponds to one of the observation identifiers that are provided when subclassing
            AbstractObservation
            options: this must adhere to the chosen observation type's ConfigSchema nested class.
        :type config: Dict
        """
        if config is None:
            return cls(NullObservation())
        obs_type = config["type"]
        obs_class = AbstractObservation._registry[obs_type]
        observation = obs_class.from_config(config=obs_class.ConfigSchema(**config["options"]))
        obs_manager = cls(observation)
        return obs_manager
