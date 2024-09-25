# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from typing import Dict, List, Optional

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

        services_requires_scan: Optional[bool] = None
        """If True, services must be scanned to update the health state. If False, true state is always shown."""

    def __init__(self, where: WhereType, services_requires_scan: bool) -> None:
        """
        Initialise a service observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this service.
            A typical location for a service might be ['network', 'nodes', <node_hostname>, 'services', <service_name>].
        :type where: WhereType
        """
        self.where = where
        self.services_requires_scan = services_requires_scan
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
            "health_status": service_state["health_state_visible"]
            if self.services_requires_scan
            else service_state["health_state_actual"],
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
        return cls(
            where=parent_where + ["services", config.service_name], services_requires_scan=config.services_requires_scan
        )


class ApplicationObservation(AbstractObservation, identifier="APPLICATION"):
    """Application observation, shows the status of an application within the simulation environment."""

    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Configuration schema for ApplicationObservation."""

        application_name: str
        """Name of the application, used for querying simulation state dictionary"""

        applications_requires_scan: Optional[bool] = None
        """
        If True, applications must be scanned to update the health state. If False, true state is always shown.
        """

    def __init__(self, where: WhereType, applications_requires_scan: bool, thresholds: Optional[Dict] = {}) -> None:
        """
        Initialise an application observation instance.

        :param where: Where in the simulation state dictionary to find the relevant information for this application.
            A typical location for an application might be
            ['network', 'nodes', <node_hostname>, 'applications', <application_name>].
        :type where: WhereType
        """
        self.where = where
        self.applications_requires_scan = applications_requires_scan
        self.default_observation = {"operating_status": 0, "health_status": 0, "num_executions": 0}

        if thresholds.get("app_executions") is None:
            self.low_app_execution_threshold = 0
            self.med_app_execution_threshold = 5
            self.high_app_execution_threshold = 10
        else:
            self._set_application_execution_thresholds(
                thresholds=[
                    thresholds.get("app_executions")["low"],
                    thresholds.get("app_executions")["medium"],
                    thresholds.get("app_executions")["high"],
                ]
            )

    def _set_application_execution_thresholds(self, thresholds: List[int]):
        """
        Method that validates and then sets the application execution threshold.

        :param: thresholds: The application execution threshold to validate and set.
        """
        if self._validate_thresholds(
            thresholds=[
                thresholds[0],
                thresholds[1],
                thresholds[2],
            ],
            threshold_identifier="app_executions",
        ):
            self.low_app_execution_threshold = thresholds[0]
            self.med_app_execution_threshold = thresholds[1]
            self.high_app_execution_threshold = thresholds[2]

    def _categorise_num_executions(self, num_executions: int) -> int:
        """
        Represent number of application executions as a categorical variable.

        :param num_access: Number of application executions.
        :return: Bin number corresponding to the number of accesses.
        """
        if num_executions > self.high_app_execution_threshold:
            return 3
        elif num_executions > self.med_app_execution_threshold:
            return 2
        elif num_executions > self.low_app_execution_threshold:
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
            "health_status": application_state["health_state_visible"]
            if self.applications_requires_scan
            else application_state["health_state_actual"],
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
        return cls(
            where=parent_where + ["applications", config.application_name],
            applications_requires_scan=config.applications_requires_scan,
            thresholds=config.thresholds,
        )
