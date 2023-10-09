from abc import ABC, abstractmethod
from typing import Any, Dict, Hashable, List, Optional, TYPE_CHECKING, Sequence, Tuple

from gym import spaces
from pydantic import BaseModel

from primaite.simulator.sim_container import Simulation
if TYPE_CHECKING:
    from primaite.game.session import PrimaiteSession

NOT_PRESENT_IN_STATE = object()
"""
Need an object to return when the sim state does not contain a requested value. Cannot use None because sometimes
the thing requested in the state could equal None. This NOT_PRESENT_IN_STATE is a sentinel for this purpose.
"""


def access_from_nested_dict(dictionary: Dict, keys: Sequence[Hashable]) -> Any:
    """
    Access an item from a deeply dictionary with a list of keys.

    For example, if the dictionary is {1: 'a', 2: {3: {4: 'b'}}}, then the key [2, 3, 4] would return 'b', and the key
    [2, 3] would return {4: 'b'}. Raises a KeyError if specified key does not exist at any level of nesting.

    :param dictionary: Deeply nested dictionary
    :type dictionary: Dict
    :param keys: List of dict keys used to traverse the nested dict. Each item corresponds to one level of depth.
    :type keys: List[Hashable]
    :return: The value in the dictionary
    :rtype: Any
    """
    key_list = [*keys] # copy keys to a new list to prevent editing original list
    if len(key_list) == 0:
        return dictionary
    k = key_list.pop(0)
    if k not in dictionary:
        return NOT_PRESENT_IN_STATE
    return access_from_nested_dict(dictionary[k], key_list)


class AbstractObservation(ABC):
    @abstractmethod
    def observe(self, state: Dict) -> Any:
        """_summary_

        :param state: _description_
        :type state: Dict
        :return: _description_
        :rtype: Any
        """
        ...

    @property
    @abstractmethod
    def space(self) -> spaces.Space:
        """Subclasses must define the shape that they expect"""
        ...

    @classmethod
    @abstractmethod
    def from_config(cls, config:Dict, session:"PrimaiteSession"):
        """Create this observation space component form a serialised format.

        The `session` parameter is for a the PrimaiteSession object that spawns this component. During deserialisation,
        a subclass of this class may need to translate from a 'reference' to a UUID.
        """


class FileObservation(AbstractObservation):
    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """
        _summary_

        :param where: Store information about where in the simulation state dictionary to find the relevatn information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a file looks like this:
            ['network','nodes',<node_uuid>,'file_system', 'folders',<folder_name>,'files',<file_name>]
        :type where: Optional[List[str]]
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where
        self.default_observation: spaces.Space = {"health_status": 0}
        "Default observation is what should be returned when the file doesn't exist, e.g. after it has been deleted."

    def observe(self, state: Dict) -> Dict:
        if self.where is None:
            return self.default_observation
        file_state = access_from_nested_dict(state, self.where)
        if file_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {"health_status": file_state["health_status"]}

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({"health_status": spaces.Discrete(6)})

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession", parent_where=None):
        return cls(where=parent_where+["files", config["file_name"]])


class ServiceObservation(AbstractObservation):
    default_observation: spaces.Space = {"operating_status": 0, "health_status": 0}
    "Default observation is what should be returned when the service doesn't exist."

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """
        :param where: Store information about where in the simulation state dictionary to find the relevant information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a service looks like this:
            `['network','nodes',<node_uuid>,'services', <service_uuid>]`
        :type where: Optional[List[str]]
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

    def observe(self, state: Dict) -> Dict:
        if self.where is None:
            return self.default_observation

        service_state = access_from_nested_dict(state, self.where)
        if service_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {"operating_status": service_state["operating_state"], "health_status": service_state["health_status"]}

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({"operating_status": spaces.Discrete(7), "health_status": spaces.Discrete(6)})

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession", parent_where:Optional[List[str]]=None):
        return cls(
            where=parent_where+["services",session.ref_map_services[config['service_ref']].uuid]
            )



class LinkObservation(AbstractObservation):
    default_observation: spaces.Space = {"protocols": {"all": {"load": 0}}}
    "Default observation is what should be returned when the link doesn't exist."

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        """
        :param where: Store information about where in the simulation state dictionary to find the relevant information.
            Optional. If None, this corresponds that the file does not exist and the observation will be populated with
            zeroes.

            A typical location for a service looks like this:
            `['network','nodes',<node_uuid>,'servics', <service_uuid>]`
        :type where: Optional[List[str]]
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

    def observe(self, state: Dict) -> Dict:
        if self.where is None:
            return self.default_observation

        link_state = access_from_nested_dict(state, self.where)
        if link_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        bandwidth = link_state["bandwidth"]
        load = link_state["current_load"]
        utilisation_fraction = load / bandwidth
        # 0 is UNUSED, 1 is 0%-10%. 2 is 10%-20%. 3 is 20%-30%. And so on... 10 is exactly 100%
        utilisation_category = int(utilisation_fraction * 10) + 1

        # TODO: once the links support separte load per protocol, this needs amendment to reflect that.
        return {"protocols": {"all": {"load": utilisation_category}}}

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({"protocols": spaces.Dict({"all": spaces.Dict({"load": spaces.Discrete(11)})})})

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession"):
        return cls(where=['network','links', session.ref_map_links[config['link_ref']]])


class FolderObservation(AbstractObservation):
    def __init__(self, where: Optional[Tuple[str]] = None, files: List[FileObservation] = []) -> None:
        """Initialise folder Observation, including files inside of the folder.

        :param where: Where in the simulation state dictionary to find the relevant information for this folder.
            A typical location for a file looks like this:
            ['network','nodes',<node_uuid>,'file_system', 'folders',<folder_name>]
        :type where: Optional[List[str]]
        :param max_files: As size of the space must remain static, define max files that can be in this folder
            , defaults to 5
        :type max_files: int, optional
        :param file_positions: Defines the positioning within the observation space of particular files. This ensures
            that even if new files are created, the existing files will always occupy the same space in the observation
            space. The keys must be between 1 and max_files. Providing file_positions will reserve a spot in the
            observation space for a file with that name, even if it's temporarily deleted, if it reappears with the same
            name, it will take the position defined in this dict. Defaults to {}
        :type file_positions: Dict[int, str], optional
        """
        super().__init__()

        self.where: Optional[Tuple[str]] = where

        self.files: List[FileObservation] = files

        self.default_observation = {
            "health_status": 0,
            "FILES": {i + 1: f.default_observation for i, f in enumerate(self.files)},
        }

    def observe(self, state: Dict) -> Dict:
        if self.where is None:
            return self.default_observation
        folder_state = access_from_nested_dict(state, self.where)
        if folder_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        health_status = folder_state["health_status"]

        obs = {}

        obs["health_status"] = health_status
        obs["FILES"] = {i + 1: file.observe(state) for i, file in enumerate(self.files)}

        return obs

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict(
            {
                "health_status": spaces.Discrete(6),
                "FILES": spaces.Dict({i + 1: f.space for i, f in enumerate(self.files)}),
            }
        )

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession", parent_where:Optional[List[str]]):
        where = parent_where + ["folders", config['folder_name']]

        file_configs = config["files"]
        files = [FileObservation.from_config(config=f, session=session, parent_where=where) for f in file_configs]

        return cls(where=where,files=files)


class NicObservation(AbstractObservation):
    default_observation: spaces.Space = {"nic_status": 0}

    def __init__(self, where: Optional[Tuple[str]] = None) -> None:
        super().__init__()
        self.where: Optional[Tuple[str]] = where

    def observe(self, state: Dict) -> Dict:
        if self.where is None:
            return self.default_observation
        nic_state = access_from_nested_dict(state, self.where)
        if nic_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        else:
            return {"nic_status": 1 if nic_state["enabled"] else 2}

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({"nic_status": spaces.Discrete(3)})

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession", parent_where:Optional[List[str]]):
        return cls(where=parent_where + ["NICs", config["nic_uuid"]])


class NodeObservation(AbstractObservation):
    def __init__(
        self,
        where: Optional[Tuple[str]] = None,
        services: List[ServiceObservation] = [],
        folders: List[FolderObservation] = [],
        nics: List[NicObservation] = [],
        logon_status:bool=False
    ) -> None:
        """
        Configurable observation for a node in the simulation.

        :param where: Where in the simulation state dictionary for find relevant information for this observation.
            A typical location for a node looks like this:
            ['network','nodes',<node_uuid>]. If empty list, a default null observation will be output, defaults to []
        :type where: List[str], optional
        :param services: Mapping between position in observation space and service UUID, defaults to {}
        :type services: Dict[int,str], optional
        :param max_services: Max number of services that can be presented in observation space for this node, defaults to 2
        :type max_services: int, optional
        :param folders: Mapping between position in observation space and folder name, defaults to {}
        :type folders: Dict[int,str], optional
        :param max_folders: Max number of folders in this node's obs space, defaults to 2
        :type max_folders: int, optional
        :param nics: Mapping between position in observation space and NIC UUID, defaults to {}
        :type nics: Dict[int,str], optional
        :param max_nics: Max number of NICS in this node's obs space, defaults to 5
        :type max_nics: int, optional
        """
        super().__init__()
        self.where: Optional[Tuple[str]] = where

        self.services: List[ServiceObservation] = services
        self.folders: List[FolderObservation] = folders
        self.nics: List[NicObservation] = nics
        self.logon_status:bool=logon_status

        self.default_observation: Dict = {
            "SERVICES": {i + 1: s.default_observation for i, s in enumerate(self.services)},
            "FOLDERS": {i + 1: f.default_observation for i, f in enumerate(self.folders)},
            "NICS": {i + 1: n.default_observation for i, n in enumerate(self.nics)},
            "operating_status": 0,
        }
        if self.logon_status:
            self.default_observation['logon_status']=0

    def observe(self, state: Dict) -> Dict:
        if self.where is None:
            return self.default_observation

        node_state = access_from_nested_dict(state, self.where)
        if node_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["SERVICES"] = {i + 1: service.observe(state) for i, service in enumerate(self.services)}
        obs["FOLDERS"] = {i + 1: folder.observe(state) for i, folder in enumerate(self.folders)}
        obs["operating_status"] = node_state["operating_state"]
        obs["NICS"] = {i + 1: nic.observe(state) for i, nic in enumerate(self.nics)}

        if self.logon_status:
            obs['logon_status'] = 0

        return obs

    @property
    def space(self) -> spaces.Space:
        space_shape = {
            "SERVICES": spaces.Dict({i + 1: service.space for i, service in enumerate(self.services)}),
            "FOLDERS": spaces.Dict({i + 1: folder.space for i, folder in enumerate(self.folders)}),
            "operating_status": spaces.Discrete(5),
            "NICS": spaces.Dict({i + 1: nic.space for i, nic in enumerate(self.nics)}),
        }
        if self.logon_status:
            space_shape['logon_status'] = spaces.Discrete(3)

        return spaces.Dict(space_shape)

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession", parent_where:Optional[List[str]]= None) -> "NodeObservation":
        node_uuid = session.ref_map_nodes[config['node_ref']]
        if parent_where is None:
            where = ["network", "nodes", node_uuid]
        else:
            where = parent_where + ["nodes", node_uuid]

        svc_configs = config.get('services', {})
        services = [ServiceObservation.from_config(config=c, session=session, parent_where=where) for c in svc_configs]
        folder_configs = config.get('folders', {})
        folders = [FolderObservation.from_config(config=c,session=session, parent_where=where) for c in folder_configs]
        nic_uuids = session.simulation.network.nodes[node_uuid].nics.keys()
        nic_configs = [{'nic_uuid':n for n in nic_uuids }] if nic_uuids else []
        nics = [NicObservation.from_config(config=c, session=session, parent_where=where) for c in nic_configs]
        logon_status = config.get('logon_status',False)
        return cls(where=where, services=services, folders=folders, nics=nics, logon_status=logon_status)


class AclObservation(AbstractObservation):
    # TODO: should where be optional, and we can use where=None to pad the observation space?
    # definitely the current approach does not support tracking files that aren't specified by name, for example
    # if a file is created at runtime, we have currently got no way of telling the observation space to track it.
    # this needs adding, but not for the MVP.
    def __init__(
        self, node_ip_to_id: Dict[str,int], ports: List[int], protocols: list[str], where: Optional[Tuple[str]] = None, num_rules: int = 10
    ) -> None:
        super().__init__()
        self.where: Optional[Tuple[str]] = where
        self.num_rules: int = num_rules
        self.node_to_id: Dict[str, int] = node_ip_to_id
        "List of node IP addresses, order in this list determines how they are converted to an ID"
        self.port_to_id: Dict[int, int] = {port: i + 2 for i, port in enumerate(ports)}
        "List of ports which are part of the game that define the ordering when converting to an ID"
        self.protocol_to_id: Dict[str, int] = {protocol: i + 2 for i, protocol in enumerate(protocols)}
        "List of protocols which are part of the game, defines ordering when converting to an ID"
        self.default_observation: Dict = {
            "RULES": {i+ 1:{
                "position": i,
                "permission": 0,
                "source_node_id": 0,
                "source_port": 0,
                "dest_node_id": 0,
                "dest_port": 0,
                "protocol": 0,
                }
            for i in range(self.num_rules)
            }
        }

    def observe(self, state: Dict) -> Dict:
        if self.where is None:
            return self.default_observation
        acl_state: Dict = access_from_nested_dict(state, self.where)
        if acl_state is NOT_PRESENT_IN_STATE:
            return self.default_observation


        #TODO: what if the ACL has more rules than num of max rules for obs space
        obs = {}
        obs["RULES"] = {}
        for i, rule_state in acl_state.items():
            if rule_state is None:
                obs["RULES"][i + 1] = {
                    "position": i,
                    "permission": 0,
                    "source_node_id": 0,
                    "source_port": 0,
                    "dest_node_id": 0,
                    "dest_port": 0,
                    "protocol": 0,
                }
            else:
                obs["RULES"][i + 1] = {
                    "position": i,
                    "permission": rule_state["action"],
                    "source_node_id": self.node_to_id[rule_state["src_ip_address"]],
                    "source_port": self.port_to_id[rule_state["src_port"]],
                    "dest_node_id": self.node_to_id[rule_state["dst_ip_address"]],
                    "dest_port": self.port_to_id[rule_state["dst_port"]],
                    "protocol": self.protocol_to_id[rule_state["protocol"]],
                }
        return obs

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict(
            {
                "RULE": spaces.Dict(
                    {
                        i + 1: spaces.Dict(
                            {
                                "position": spaces.Discrete(self.num_rules),
                                "permission": spaces.Discrete(3),
                                # adding two to lengths is to account for reserved values 0 (unused) and 1 (any)
                                "source_node_id": spaces.Discrete(len(set(self.node_to_id.values())) + 2),
                                "source_port": spaces.Discrete(len(self.port_to_id) + 2),
                                "dest_node_id": spaces.Discrete(len(set(self.node_to_id.values())) + 2),
                                "dest_port": spaces.Discrete(len(self.port_to_id) + 2),
                                "protocol": spaces.Discrete(len(self.protocol_to_id) + 2),
                            }
                        )
                        for i in range(self.num_rules)
                    }
                )
            }
        )

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession") -> "AclObservation":
        node_ip_to_idx = {}
        for node_idx, node_cfg in enumerate(config['node_order']):
            n_ref = node_cfg["node_ref"]
            n_obj = session.simulation.network.nodes[session.ref_map_nodes[n_ref]]
            for nic_uuid, nic_obj in n_obj.nics.items():
                node_ip_to_idx[nic_obj.ip_address] = node_idx + 2

        router_uuid = session.ref_map_nodes[config['router_node_ref']]
        return cls(
            node_ip_to_id=node_ip_to_idx,
            ports=session.options.ports,
            protocols=session.options.protocols,
            where=["network", "nodes", router_uuid, "acl", "acl"])



class NullObservation(AbstractObservation):
    def __init__(self, where:Optional[List[str]]=None):
        self.default_observation: Dict = {}

    def observe(self, state: Dict) -> Dict:
        return {}

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({})

    @classmethod
    def from_config(cls, config:Dict, session:Optional["PrimaiteSession"]=None) -> "NullObservation":
        return cls()

class ICSObservation(NullObservation): pass


class UC2BlueObservation(AbstractObservation):
    def __init__(
            self,
            nodes: List[NodeObservation],
            links: List[LinkObservation],
            acl: AclObservation,
            ics: ICSObservation,
            where:Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.where: Optional[Tuple[str]] = where

        self.nodes: List[NodeObservation] = nodes
        self.links: List[LinkObservation] = links
        self.acl: AclObservation = acl
        self.ics: ICSObservation = ics

        self.default_observation : Dict = {
            "NODES": {i+1: n.default_observation for i,n in enumerate(self.nodes)},
            "LINKS": {i+1: l.default_observation for i,l in enumerate(self.links)},
            "ACL": self.acl.default_observation,
            "ICS": self.ics.default_observation,
        }

    def observe(self, state:Dict) -> Dict:
        if self.where is None:
            return self.default_observation

        obs = {}
        obs['NODES'] = {i + 1: node.observe(state) for i, node in enumerate(self.nodes)}
        obs['LINKS'] = {i + 1: link.observe(state) for i, link in enumerate(self.links)}
        obs['ACL'] = self.acl.observe(state)
        obs['ICS'] = self.ics.observe(state)

        return obs

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({
            "NODES": spaces.Dict({i+1: node.space for i, node in enumerate(self.nodes)}),
            "LINKS": spaces.Dict({i+1: link.space for i, link in enumerate(self.links)}),
            "ACL": self.acl.space,
            "ICS": self.ics.space,
        })

    @classmethod
    def from_config(cls, config:Dict, session:"PrimaiteSession"):
        node_configs = config["nodes"]
        nodes = [NodeObservation.from_config(config=n, session=session) for n in node_configs]

        link_configs = config["links"]
        links = [LinkObservation.from_config(config=l, session=session) for l in link_configs]

        acl_config = config["acl"]
        acl = AclObservation.from_config(config=acl_config, session=session)

        ics_config = config["ics"]
        ics = ICSObservation.from_config(config=ics_config, session=session)
        new = cls(nodes=nodes, links=links, acl=acl, ics=ics, where=['network'])
        return new


class UC2RedObservation(AbstractObservation):
    def __init__(self, nodes:List[NodeObservation], where:Optional[List[str]] = None) -> None:
        super().__init__()
        self.where:Optional[List[str]] = where
        self.nodes: List[NodeObservation] = nodes

        self.default_observation : Dict = {
            "NODES": {i+1: n.default_observation for i,n in enumerate(self.nodes)},
        }

    def observe(self, state: Dict) -> Dict:
        if self.where is None:
            return self.default_observation

        obs = {}
        obs['NODES'] = {i+1: node.observe(state) for i, node in enumerate(self.nodes)}
        return obs

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({
            "NODES": spaces.Dict({i+1: node.space for i, node in enumerate(self.nodes)}),
        })

    @classmethod
    def from_config(cls, config: Dict, session: "PrimaiteSession"):
        node_configs = config["nodes"]
        nodes = [NodeObservation.from_config(config=cfg, session=session) for cfg in node_configs]
        return cls(nodes=nodes, where=["network"])


class UC2GreenObservation(NullObservation): pass

class ObservationSpace:
    """
    Manage the observations of an Actor.

    The observation space has the purpose of:
      1. Reading the outputted state from the PrimAITE Simulation.
      2. Selecting parts of the simulation state that are requested by the simulation config
      3. Formatting this information so an actor can use it to make decisions.
    """

    ...

    # what this class does:
    # keep a list of observations
    # create observations for an actor from the config
    def __init__(self, observation:AbstractObservation) -> None:
        self.obs: AbstractObservation = observation

    def observe(self, state) -> Dict:
        return self.obs.observe(state)

    @property
    def space(self) -> None:
        return self.obs.space

    @classmethod
    def from_config(cls, config:Dict, session:"PrimaiteSession") -> "ObservationSpace":
        if config['type'] == "UC2BlueObservation":
            return cls(UC2BlueObservation.from_config(config.get('options',{}), session=session))
        elif config['type'] == "UC2RedObservation":
            return cls(UC2RedObservation.from_config(config.get('options',{}), session=session))
        elif config['type'] == "UC2GreenObservation":
            return cls(UC2GreenObservation.from_config(config.get("options",{}), session=session))
        else:
            raise ValueError("Observation space type invalid")
