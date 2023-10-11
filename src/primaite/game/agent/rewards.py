from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, TYPE_CHECKING
from primaite import getLogger
_LOGGER = getLogger(__name__)

if TYPE_CHECKING:
    from primaite.game.session import PrimaiteSession


class AbstractReward:

    @abstractmethod
    def calculate(self, state: Dict) -> float:
        return 0.0

    @abstractmethod
    @classmethod
    def from_config(cls, config:dict) -> "AbstractReward":
        return cls()


class DummyReward(AbstractReward):
    def calculate(self, state: Dict) -> float:
        return 0.0

    @classmethod
    def from_config(cls, config: dict) -> "DummyReward":
        return cls()

class DatabaseFileIntegrity(AbstractReward):
    def __init__(self, node_uuid:str, folder_name:str, file_name:str) -> None:
        self.location_in_state = ["network", "node", node_uuid, "file_system", ""]

    def calculate(self, state: Dict) -> float:
        database_file_state = access_from_nested_dict(state, self.location_in_state)
        health_status = database_file_state['health_status']
        if health_status == "corrupted":
            return -1
        elif health_status == "good":
            return 1
        else:
            return 0

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession") -> "DatabaseFileIntegrity":
        node_ref = config.get("node_ref")
        folder_name = config.get("folder_name")
        file_name = config.get("file_name")
        if not (node_ref):
            _LOGGER.error(f"{cls.__name__} could not be initialised from config because node_ref parameter was not specified")
            return DummyReward() #TODO: better error handling
        if not folder_name:
            _LOGGER.error(f"{cls.__name__} could not be initialised from config because folder_name parameter was not specified")
            return DummyReward() # TODO: better error handling
        if not file_name:
            _LOGGER.error(f"{cls.__name__} could not be initialised from config because file_name parameter was not specified")
            return DummyReward() # TODO: better error handling
        node_uuid = session.ref_map_nodes[node_ref].uuid
        if not node_uuid:
            _LOGGER.error(f"{cls.__name__} could not be initialised from config because the referenced node could not be found in the simulation")
            return DummyReward() # TODO: better error handling

        return cls(node_uuid = node_uuid, folder_name=folder_name, file_name=file_name)

class WebServer404Penalty(AbstractReward):
    def __init__(self, node_uuid:str, service_uuid:str) -> None:
        self.location_in_state = ['network','node', node_uuid, 'services', service_uuid]

    def calculate(self, state: Dict) -> float:
        web_service_state = access_from_nested_dict(state, self.location_in_state)
        most_recent_return_code = web_service_state['most_recent_return_code']
        if most_recent_return_code == 200:
            return 1
        elif most_recent_return_code == 404:
            return -1
        else:
            return 0

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession") -> "WebServer404Penalty":
        node_ref = config.get("node_ref")
        service_ref = config.get("service_ref")
        if not (node_ref and service_ref):
            msg = f"{cls.__name__} could not be initialised from config because node_ref and service_ref were not found in reward config."
            _LOGGER.warn(msg)
            return DummyReward() #TODO: should we error out with incorrect inputs? Probably!
        node_uuid = session.ref_map_nodes[node_ref].uuid
        service_uuid = session.ref_map_services[service_ref].uuid
        if not (node_uuid and service_uuid):
            msg = f"{cls.__name__} could not be initialised because node {node_ref} and service {service_ref} were not found in the simulator."
            _LOGGER.warn(msg)
            return DummyReward() # TODO: consider erroring here as well

        return cls(node_uuid=node_uuid, service_uuid=service_uuid)


class RewardFunction:
    __rew_class_identifiers: Dict[str, type[AbstractReward]] = {
        "DUMMY": DummyReward,
        "DATABASE_FILE_INTEGRITY": DatabaseFileIntegrity,
        "WEB_SERVER_404_PENALTY": WebServer404Penalty,
        }

    def __init__(self):
        self.reward_components: List[Tuple[AbstractReward, float]] = []
        "attribute reward_components keeps track of reward components and the weights assigned to each."

    def regsiter_component(self, component:AbstractReward, weight:float=1.0) -> None:
        self.reward_components.append((component, weight))

    def calculate(self, state: Dict) -> float:
        total = 0.0
        for comp_and_weight in self.reward_components:
            comp = comp_and_weight[0]
            weight = comp_and_weight[1]
            total += weight * comp.calculate(state=state)
        return total

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession") -> "RewardFunction":
        new = cls()

        for rew_component_cfg in config["reward_components"]:
            rew_type = rew_component_cfg["type"]
            weight = rew_component_cfg["weight"]
            rew_class = cls.__rew_class_identifiers[rew_type]
            rew_instance = rew_class.from_config(config=rew_component_cfg.get('options',{}), session=session)
            new.regsiter_component(component=rew_instance, weight=weight)
        return new
