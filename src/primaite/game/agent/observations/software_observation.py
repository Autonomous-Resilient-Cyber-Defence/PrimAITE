# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import Dict

from gymnasium import spaces
from gymnasium.core import ObsType

from primaite.game.agent.observations.observations import AbstractObservation, WhereType
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE


class ServiceObservation(AbstractObservation, identifier="SERVICE"):
    """Service observation, shows status of a service in the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for ServiceObservation."""

        service_name: str
        """Name of the service, used for querying simulation state dictionary"""

    def __init__(self, where: WhereType) -> None:
        """
        Initialise a service observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this service.
            A typical location for a service might be ['network', 'nodes', <node_hostname>, 'services', <service_name>].
        :type where: WhereType
        """
        self.where = where
        self.default_observation = {"operating_status": 0, "health_status": 0}

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Observation containing the operating status and health status of the service.
        :rtype: ObsType
        """
        service_state = access_from_nested_dict(state, self.where)
        if service_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": service_state["operating_state"],
            "health_status": service_state["health_state_visible"],
        }

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for service status.
        :rtype: spaces.Space
        """
        return spaces.Dict({"operating_status": spaces.Discrete(7), "health_status": spaces.Discrete(5)})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> ServiceObservation:
        """
        Create a service observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the service observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this service's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed service observation instance.
        :rtype: ServiceObservation
        """
        return cls(where=parent_where + ["services", config.service_name])


class ApplicationObservation(AbstractObservation, identifier="APPLICATION"):
    """Application observation, shows the status of an application within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for ApplicationObservation."""

        application_name: str
        """Name of the application, used for querying simulation state dictionary"""

    def __init__(self, where: WhereType) -> None:
        """
        Initialise an application observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this application.
            A typical location for an application might be
            ['network', 'nodes', <node_hostname>, 'applications', <application_name>].
        :type where: WhereType
        """
        self.where = where
        self.default_observation = {"operating_status": 0, "health_status": 0, "num_executions": 0}

        # TODO: allow these to be configured in yaml
        self.high_threshold = 10
        self.med_threshold = 5
        self.low_threshold = 0

    def _categorise_num_executions(self, num_executions: int) -> int:
        """
        Represent number of file accesses as a categorical variable.

        :param num_access: Number of file accesses.
        :return: Bin number corresponding to the number of accesses.
        """
        if num_executions > self.high_threshold:
            return 3
        elif num_executions > self.med_threshold:
            return 2
        elif num_executions > self.low_threshold:
            return 1
        return 0

    def observe(self, state: Dict) -> ObsType:
        """
        Generate observation based on the current state of the simulation.

        :param state: Simulation state dictionary.
        :type state: Dict
        :return: Obs containing the operating status, health status, and number of executions of the application.
        :rtype: ObsType
        """
        application_state = access_from_nested_dict(state, self.where)
        if application_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": application_state["operating_state"],
            "health_status": application_state["health_state_visible"],
            "num_executions": self._categorise_num_executions(application_state["num_executions"]),
        }

    @property
    def space(self) -> spaces.Space:
        """
        Gymnasium space object describing the observation space shape.

        :return: Gymnasium space representing the observation space for application status.
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                "operating_status": spaces.Discrete(7),
                "health_status": spaces.Discrete(5),
                "num_executions": spaces.Discrete(4),
            }
        )

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = []) -> ApplicationObservation:
        """
        Create an application observation from a configuration schema.

        :param config: Configuration schema containing the necessary information for the application observation.
        :type config: ConfigSchema
        :param parent_where: Where in the simulation state dictionary to find the information about this application's
            parent node. A typical location for a node might be ['network', 'nodes', <node_hostname>].
        :type parent_where: WhereType, optional
        :return: Constructed application observation instance.
        :rtype: ApplicationObservation
        """
        return cls(where=parent_where + ["applications", config.application_name])
