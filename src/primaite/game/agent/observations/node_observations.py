# TODO: make sure when config options are being passed down from higher-level observations to lower-level, but the lower-level also defines that option, don't overwrite.
from __future__ import annotations
from ipaddress import IPv4Address
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, TYPE_CHECKING, Union

from gymnasium import spaces
from gymnasium.core import ObsType
from pydantic import BaseModel, ConfigDict

from primaite import getLogger
from primaite.game.agent.observations.observations import AbstractObservation
# from primaite.game.agent.observations.file_system_observations import FolderObservation
# from primaite.game.agent.observations.nic_observations import NicObservation
# from primaite.game.agent.observations.software_observation import ServiceObservation
from primaite.game.agent.utils import access_from_nested_dict, NOT_PRESENT_IN_STATE

_LOGGER = getLogger(__name__)

WhereType = Iterable[str | int] | None


class ServiceObservation(AbstractObservation, identifier="SERVICE"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        service_name: str

    def __init__(self, where: WhereType)->None:
        self.where = where
        self.default_observation = {"operating_status": 0, "health_status": 0}

    def observe(self, state: Dict) -> Any:
        service_state = access_from_nested_dict(state, self.where)
        if service_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": service_state["operating_state"],
            "health_status": service_state["health_state_visible"],
        }

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Dict({"operating_status": spaces.Discrete(7), "health_status": spaces.Discrete(5)})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        return cls(where=parent_where+["services", config.service_name])


class ApplicationObservation(AbstractObservation, identifier="APPLICATION"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        application_name: str

    def __init__(self, where: WhereType)->None:
        self.where = where
        self.default_observation = {"operating_status": 0, "health_status": 0, "num_executions": 0}

    def observe(self, state: Dict) -> Any:
        # raise NotImplementedError("TODO NUM EXECUTIONS NEEDS TO BE CONVERTED TO A CATEGORICAL")
        application_state = access_from_nested_dict(state, self.where)
        if application_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {
            "operating_status": application_state["operating_state"],
            "health_status": application_state["health_state_visible"],
            "num_executions": application_state["num_executions"],
        }

    @property
    def space(self) -> spaces.Space:
        """Gymnasium space object describing the observation space shape."""
        return spaces.Dict({
            "operating_status": spaces.Discrete(7),
            "health_status": spaces.Discrete(5),
            "num_executions": spaces.Discrete(4)
            })

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ApplicationObservation:
        return cls(where=parent_where+["applications", config.application_name])


class FileObservation(AbstractObservation, identifier="FILE"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        file_name: str
        include_num_access : bool = False

    def __init__(self, where: WhereType, include_num_access: bool)->None:
        self.where: WhereType = where
        self.include_num_access :bool = include_num_access

        self.default_observation: ObsType = {"health_status": 0}
        if self.include_num_access:
            self.default_observation["num_access"] = 0

    def observe(self, state: Dict) -> Any:
        file_state = access_from_nested_dict(state, self.where)
        if file_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        obs = {"health_status": file_state["visible_status"]}
        if self.include_num_access:
            obs["num_access"] = file_state["num_access"]
            # raise NotImplementedError("TODO: need to fix num_access to use thresholds instead of raw value.")
        return obs

    @property
    def space(self) -> spaces.Space:
        space = {"health_status": spaces.Discrete(6)}
        if self.include_num_access:
            space["num_access"] = spaces.Discrete(4)
        return spaces.Dict(space)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> FileObservation:
        return cls(where=parent_where+["files", config.file_name], include_num_access=config.include_num_access)


class FolderObservation(AbstractObservation, identifier="FOLDER"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        folder_name: str
        files: List[FileObservation.ConfigSchema] = []
        num_files : int = 0
        include_num_access : bool = False

    def __init__(self, where: WhereType, files: Iterable[FileObservation], num_files: int, include_num_access: bool)->None:
        self.where: WhereType = where

        self.files: List[FileObservation] = files
        while len(self.files) < num_files:
            self.files.append(FileObservation(where=None,include_num_access=include_num_access))
        while len(self.files) > num_files:
            truncated_file = self.files.pop()
            msg = f"Too many files in folder observation. Truncating file {truncated_file}"
            _LOGGER.warning(msg)

        self.default_observation = {
            "health_status": 0,
            "FILES": {i + 1: f.default_observation for i, f in enumerate(self.files)},
        }

    def observe(self, state: Dict) -> Any:
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
        """Gymnasium space object describing the observation space shape.

        :return: Gymnasium space
        :rtype: spaces.Space
        """
        return spaces.Dict(
            {
                "health_status": spaces.Discrete(6),
                "FILES": spaces.Dict({i + 1: f.space for i, f in enumerate(self.files)}),
            }
        )
    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> FolderObservation:
        where = parent_where + ["folders", config.folder_name]

        #pass down shared/common config items
        for file_config in config.files:
            file_config.include_num_access = config.include_num_access

        files = [FileObservation.from_config(config=f, parent_where = where) for f in config.files]
        return cls(where=where, files=files, num_files=config.num_files, include_num_access=config.include_num_access)


class NICObservation(AbstractObservation, identifier="NETWORK_INTERFACE"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        nic_num: int
        include_nmne: bool = False


    def __init__(self, where: WhereType, include_nmne: bool)->None:
        self.where = where
        self.include_nmne : bool = include_nmne

        self.default_observation: ObsType = {"nic_status": 0}
        if self.include_nmne:
            self.default_observation.update({"NMNE":{"inbound":0, "outbound":0}})

    def observe(self, state: Dict) -> Any:
        # raise NotImplementedError("TODO: CATEGORISATION")
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
        space = spaces.Dict({"nic_status": spaces.Discrete(3)})

        if self.include_nmne:
            space["NMNE"] = spaces.Dict({"inbound": spaces.Discrete(4), "outbound": spaces.Discrete(4)})

        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> NICObservation:
        return cls(where = parent_where+["NICs", config.nic_num], include_nmne=config.include_nmne)


class HostObservation(AbstractObservation, identifier="HOST"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        hostname: str
        services: List[ServiceObservation.ConfigSchema] = []
        applications: List[ApplicationObservation.ConfigSchema] = []
        folders: List[FolderObservation.ConfigSchema] = []
        network_interfaces: List[NICObservation.ConfigSchema] = []
        num_services: int
        num_applications: int
        num_folders: int
        num_files: int
        num_nics: int
        include_nmne: bool
        include_num_access: bool

    def __init__(self,
                 where: WhereType,
                 services:List[ServiceObservation],
                 applications:List[ApplicationObservation],
                 folders:List[FolderObservation],
                 network_interfaces:List[NICObservation],
                 num_services: int,
                 num_applications: int,
                 num_folders: int,
                 num_files: int,
                 num_nics: int,
                 include_nmne: bool,
                 include_num_access: bool
                 )->None:

        self.where : WhereType = where

        # ensure service list has length equal to num_services by truncating or padding
        self.services: List[ServiceObservation] = services
        while len(self.services) < num_services:
            self.services.append(ServiceObservation(where=None))
        while len(self.services) > num_services:
            truncated_service = self.services.pop()
            msg = f"Too many services in Node observation space for node. Truncating service {truncated_service.where}"
            _LOGGER.warning(msg)

        # ensure application list has length equal to num_applications by truncating or padding
        self.applications: List[ApplicationObservation] = applications
        while len(self.applications) < num_applications:
            self.applications.append(ApplicationObservation(where=None))
        while len(self.applications) > num_applications:
            truncated_application = self.applications.pop()
            msg = f"Too many applications in Node observation space for node. Truncating application {truncated_application.where}"
            _LOGGER.warning(msg)

        # ensure folder list has length equal to num_folders by truncating or padding
        self.folders: List[FolderObservation] = folders
        while len(self.folders) < num_folders:
            self.folders.append(FolderObservation(where = None, files= [], num_files=num_files, include_num_access=include_num_access))
        while len(self.folders) > num_folders:
            truncated_folder = self.folders.pop()
            msg = f"Too many folders in Node observation space for node. Truncating folder {truncated_folder.where}"
            _LOGGER.warning(msg)

        # ensure network_interface list has length equal to num_network_interfaces by truncating or padding
        self.network_interfaces: List[NICObservation] = network_interfaces
        while len(self.network_interfaces) < num_nics:
            self.network_interfaces.append(NICObservation(where = None, include_nmne=include_nmne))
        while len(self.network_interfaces) > num_nics:
            truncated_nic = self.network_interfaces.pop()
            msg = f"Too many network_interfaces in Node observation space for node. Truncating {truncated_folder.where}"
            _LOGGER.warning(msg)

        self.default_observation: ObsType = {
            "SERVICES": {i + 1: s.default_observation for i, s in enumerate(self.services)},
            "FOLDERS": {i + 1: f.default_observation for i, f in enumerate(self.folders)},
            "NICS": {i + 1: n.default_observation for i, n in enumerate(self.network_interfaces)},
            "operating_status": 0,
            "num_file_creations": 0,
            "num_file_deletions": 0,
        }


    def observe(self, state: Dict) -> Any:
        node_state = access_from_nested_dict(state, self.where)
        if node_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["SERVICES"] = {i + 1: service.observe(state) for i, service in enumerate(self.services)}
        obs["FOLDERS"] = {i + 1: folder.observe(state) for i, folder in enumerate(self.folders)}
        obs["operating_status"] = node_state["operating_state"]
        obs["NICS"] = {
            i + 1: network_interface.observe(state) for i, network_interface in enumerate(self.network_interfaces)
        }
        obs["num_file_creations"] = node_state["file_system"]["num_file_creations"]
        obs["num_file_deletions"] = node_state["file_system"]["num_file_deletions"]
        return obs

    @property
    def space(self) -> spaces.Space:
        shape = {
            "SERVICES": spaces.Dict({i + 1: service.space for i, service in enumerate(self.services)}),
            "FOLDERS": spaces.Dict({i + 1: folder.space for i, folder in enumerate(self.folders)}),
            "operating_status": spaces.Discrete(5),
            "NICS": spaces.Dict(
                {i + 1: network_interface.space for i, network_interface in enumerate(self.network_interfaces)}
            ),
            "num_file_creations" : spaces.Discrete(4),
            "num_file_deletions" : spaces.Discrete(4),
        }
        return spaces.Dict(shape)

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = None ) -> HostObservation:
        if parent_where is None:
            where = ["network", "nodes", config.hostname]
        else:
            where = parent_where + ["nodes", config.hostname]

        #pass down shared/common config items
        for folder_config in config.folders:
            folder_config.include_num_access = config.include_num_access
            folder_config.num_files = config.num_files
        for nic_config in config.network_interfaces:
            nic_config.include_nmne = config.include_nmne

        services = [ServiceObservation.from_config(config=c,parent_where=where) for c in config.services]
        applications = [ApplicationObservation.from_config(config=c, parent_where=where) for c in config.applications]
        folders = [FolderObservation.from_config(config=c, parent_where=where) for c in config.folders]
        nics = [NICObservation.from_config(config=c, parent_where=where) for c in config.network_interfaces]

        return cls(
            where = where,
            services = services,
            applications = applications,
            folders = folders,
            network_interfaces = nics,
            num_services = config.num_services,
            num_applications = config.num_applications,
            num_folders = config.num_folders,
            num_files = config.num_files,
            num_nics = config.num_nics,
            include_nmne = config.include_nmne,
            include_num_access = config.include_num_access,
        )


class PortObservation(AbstractObservation, identifier="PORT"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        port_id : int

    def __init__(self, where: WhereType)->None:
        self.where = where
        self.default_observation: ObsType = {"operating_status" : 0}

    def observe(self, state: Dict) -> Any:
        port_state = access_from_nested_dict(state, self.where)
        if port_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        return {"operating_status": 1 if port_state["enabled"] else 2 }

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({"operating_status": spaces.Discrete(3)})

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> PortObservation:
        return cls(where = parent_where + ["NICs", config.port_id])

class ACLObservation(AbstractObservation, identifier="ACL"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        ip_list: List[IPv4Address]
        port_list: List[int]
        protocol_list: List[str]
        num_rules: int

    def __init__(self, where: WhereType, num_rules: int, ip_list: List[IPv4Address], port_list: List[int],protocol_list: List[str])->None:
        self.where = where
        self.num_rules: int = num_rules
        self.ip_to_id: Dict[str, int] = {i+2:p for i,p in enumerate(ip_list)}
        self.port_to_id: Dict[int, int] = {i+2:p for i,p in enumerate(port_list)}
        self.protocol_to_id: Dict[str, int] = {i+2:p for i,p in enumerate(protocol_list)}
        self.default_observation: Dict = {
            i
            + 1: {
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

    def observe(self, state: Dict) -> Any:
        acl_state: Dict = access_from_nested_dict(state, self.where)
        if acl_state is NOT_PRESENT_IN_STATE:
            return self.default_observation
        obs = {}
        acl_items = dict(acl_state.items())
        i = 1  # don't show rule 0 for compatibility reasons.
        while i < self.num_rules + 1:
            rule_state = acl_items[i]
            if rule_state is None:
                obs[i] = {
                    "position": i - 1,
                    "permission": 0,
                    "source_node_id": 0,
                    "source_port": 0,
                    "dest_node_id": 0,
                    "dest_port": 0,
                    "protocol": 0,
                }
            else:
                src_ip = rule_state["src_ip_address"]
                src_node_id = 1 if src_ip is None else self.node_to_id[IPv4Address(src_ip)]
                dst_ip = rule_state["dst_ip_address"]
                dst_node_ip = 1 if dst_ip is None else self.node_to_id[IPv4Address(dst_ip)]
                src_port = rule_state["src_port"]
                src_port_id = 1 if src_port is None else self.port_to_id[src_port]
                dst_port = rule_state["dst_port"]
                dst_port_id = 1 if dst_port is None else self.port_to_id[dst_port]
                protocol = rule_state["protocol"]
                protocol_id = 1 if protocol is None else self.protocol_to_id[protocol]
                obs[i] = {
                    "position": i - 1,
                    "permission": rule_state["action"],
                    "source_node_id": src_node_id,
                    "source_port": src_port_id,
                    "dest_node_id": dst_node_ip,
                    "dest_port": dst_port_id,
                    "protocol": protocol_id,
                }
            i += 1
        return obs

    @property
    def space(self) -> spaces.Space:
        raise NotImplementedError("TODO: need to add wildcard id.")
        return spaces.Dict(
            {
                i
                + 1: spaces.Dict(
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


    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ACLObservation:
        return cls(
            where = parent_where+["acl", "acl"],
            num_rules = config.num_rules,
            ip_list = config.ip_list,
            ports = config.port_list,
            protocols = config.protocol_list
            )

class RouterObservation(AbstractObservation, identifier="ROUTER"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        hostname: str
        ports: List[PortObservation.ConfigSchema]
        num_ports: int
        acl: ACLObservation.ConfigSchema
        ip_list: List[str]
        port_list: List[int]
        protocol_list: List[str]
        num_rules: int

    def __init__(self,
                 where: WhereType,
                 ports:List[PortObservation],
                 num_ports: int,
                 acl: ACLObservation,
                 )->None:
        self.where: WhereType = where
        self.ports: List[PortObservation] = ports
        self.acl: ACLObservation = acl
        self.num_ports:int = num_ports

        while len(self.ports) < num_ports:
            self.ports.append(PortObservation(where=None))
        while len(self.ports) > num_ports:
            self.ports.pop()
            msg = f"Too many ports in router observation. Truncating."
            _LOGGER.warning(msg)

        self.default_observation = {
            "PORTS": {i+1:p.default_observation for i,p in enumerate(self.ports)},
            "ACL": self.acl.default_observation
            }

    def observe(self, state: Dict) -> Any:
        router_state = access_from_nested_dict(state, self.where)
        if router_state is NOT_PRESENT_IN_STATE:
            return self.default_observation

        obs = {}
        obs["PORTS"] = {i+1:p.observe(state) for i,p in enumerate(self.ports)}
        obs["ACL"] = self.acl.observe(state)
        return obs

    @property
    def space(self) -> spaces.Space:
        return spaces.Dict({
            "PORTS": {i+1:p.space for i,p in self.ports},
            "ACL": self.acl.space
        })

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> RouterObservation:
        where = parent_where + ["nodes", config.hostname]

        if config.acl.num_rules is None:
            config.acl.num_rules = config.num_rules
        if config.acl.ip_list is None:
            config.acl.ip_list = config.ip_list
        if config.acl.port_list is None:
            config.acl.port_list = config.port_list
        if config.acl.protocol_list is None:
            config.acl.protocol_list = config.protocol_list

        ports = [PortObservation.from_config(config=c, parent_where=where) for c in config.ports]
        acl = ACLObservation.from_config(config=config.acl, parent_where=where)
        return cls(where=where, ports=ports, num_ports=config.num_ports, acl=acl)

class FirewallObservation(AbstractObservation, identifier="FIREWALL"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        hostname: str
        ip_list: List[str]
        port_list: List[int]
        protocol_list: List[str]
        num_rules: int


    def __init__(self,
                 where: WhereType,
                 ip_list: List[str],
                 port_list: List[int],
                 protocol_list: List[str],
                 num_rules: int,
                 )->None:
        self.where: WhereType = where

        self.ports: List[PortObservation] = [PortObservation(where=[self.where+["port", port_num]]) for port_num in (1,2,3) ]
        #TODO: check what the port nums are for firewall.

        self.internal_inbound_acl = ACLObservation(where = self.where+["acl","internal","inbound"], num_rules= num_rules, ip_list=ip_list, port_list=port_list, protocol_list=protocol_list)
        self.internal_outbound_acl = ACLObservation(where = self.where+["acl","internal","outbound"], num_rules= num_rules, ip_list=ip_list, port_list=port_list, protocol_list=protocol_list)
        self.dmz_inbound_acl = ACLObservation(where = self.where+["acl","dmz","inbound"], num_rules= num_rules, ip_list=ip_list, port_list=port_list, protocol_list=protocol_list)
        self.dmz_outbound_acl = ACLObservation(where = self.where+["acl","dmz","outbound"], num_rules= num_rules, ip_list=ip_list, port_list=port_list, protocol_list=protocol_list)
        self.external_inbound_acl = ACLObservation(where = self.where+["acl","external","inbound"], num_rules= num_rules, ip_list=ip_list, port_list=port_list, protocol_list=protocol_list)
        self.external_outbound_acl = ACLObservation(where = self.where+["acl","external","outbound"], num_rules= num_rules, ip_list=ip_list, port_list=port_list, protocol_list=protocol_list)


        self.default_observation = {
            "PORTS": {i+1:p.default_observation for i,p in enumerate(self.ports)},
            "INTERNAL": {
                "INBOUND": self.internal_inbound_acl.default_observation,
                "OUTBOUND": self.internal_outbound_acl.default_observation,
                },
            "DMZ": {
                "INBOUND": self.dmz_inbound_acl.default_observation,
                "OUTBOUND": self.dmz_outbound_acl.default_observation,
                },
            "EXTERNAL": {
                "INBOUND": self.external_inbound_acl.default_observation,
                "OUTBOUND": self.external_outbound_acl.default_observation,
                },
            }

    def observe(self, state: Dict) -> Any:
        obs = {
            "PORTS": {i+1:p.observe(state) for i,p in enumerate(self.ports)},
            "INTERNAL": {
                "INBOUND": self.internal_inbound_acl.observe(state),
                "OUTBOUND": self.internal_outbound_acl.observe(state),
                },
            "DMZ": {
                "INBOUND": self.dmz_inbound_acl.observe(state),
                "OUTBOUND": self.dmz_outbound_acl.observe(state),
                },
            "EXTERNAL": {
                "INBOUND": self.external_inbound_acl.observe(state),
                "OUTBOUND": self.external_outbound_acl.observe(state),
                },
            }
        return obs

    @property
    def space(self) -> spaces.Space:
        space =spaces.Dict({
            "PORTS": spaces.Dict({i+1:p.space for i,p in enumerate(self.ports)}),
            "INTERNAL": spaces.Dict({
                "INBOUND": self.internal_inbound_acl.space,
                "OUTBOUND": self.internal_outbound_acl.space,
                }),
            "DMZ": spaces.Dict({
                "INBOUND": self.dmz_inbound_acl.space,
                "OUTBOUND": self.dmz_outbound_acl.space,
                }),
            "EXTERNAL": spaces.Dict({
                "INBOUND": self.external_inbound_acl.space,
                "OUTBOUND": self.external_outbound_acl.space,
                }),
            })
        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> FirewallObservation:
        where = parent_where+["nodes", config.hostname]
        return cls(where=where, ip_list=config.ip_list, port_list=config.port_list, protocol_list=config.protocol_list, num_rules=config.num_rules)

class NodesObservation(AbstractObservation, identifier="NODES"):
    class ConfigSchema(AbstractObservation.ConfigSchema):
        """Config"""
        hosts: List[HostObservation.ConfigSchema] = []
        routers: List[RouterObservation.ConfigSchema] = []
        firewalls: List[FirewallObservation.ConfigSchema] = []

        num_services: int
        num_applications: int
        num_folders: int
        num_files: int
        num_nics: int
        include_nmne: bool
        include_num_access: bool

        ip_list: List[str]
        port_list: List[int]
        protocol_list: List[str]
        num_rules: int


    def __init__(self, where: WhereType, hosts:List[HostObservation], routers:List[RouterObservation], firewalls:List[FirewallObservation])->None:
        self.where :WhereType = where

        self.hosts: List[HostObservation] = hosts
        self.routers: List[RouterObservation] = routers
        self.firewalls: List[FirewallObservation] = firewalls

        self.default_observation = {
            **{f"HOST{i}":host.default_observation for i,host in enumerate(self.hosts)},
            **{f"ROUTER{i}":router.default_observation for i,router in enumerate(self.routers)},
            **{f"FIREWALL{i}":firewall.default_observation for i,firewall in enumerate(self.firewalls)},
        }

    def observe(self, state: Dict) -> Any:
        obs = {
            **{f"HOST{i}":host.observe(state) for i,host in enumerate(self.hosts)},
            **{f"ROUTER{i}":router.observe(state) for i,router in enumerate(self.routers)},
            **{f"FIREWALL{i}":firewall.observe(state) for i,firewall in enumerate(self.firewalls)},
        }
        return obs

    @property
    def space(self) -> spaces.Space:
        space = spaces.Dict({
            **{f"HOST{i}":host.space for i,host in enumerate(self.hosts)},
            **{f"ROUTER{i}":router.space for i,router in enumerate(self.routers)},
            **{f"FIREWALL{i}":firewall.space for i,firewall in enumerate(self.firewalls)},
        })
        return space

    @classmethod
    def from_config(cls, config: ConfigSchema, parent_where: WhereType = [] ) -> ServiceObservation:
        if parent_where is None:
            where = ["network", "nodes"]
        else:
            where = parent_where + ["nodes"]

        for host_config in config.hosts:
            if host_config.num_services is None:
                host_config.num_services = config.num_services
            if host_config.num_applications is None:
                host_config.num_application = config.num_applications
            if host_config.num_folders is None:
                host_config.num_folder = config.num_folders
            if host_config.num_files is None:
                host_config.num_file = config.num_files
            if host_config.num_nics is None:
                host_config.num_nic = config.num_nics
            if host_config.include_nmne is None:
                host_config.include_nmne = config.include_nmne
            if host_config.include_num_access is None:
                host_config.include_num_access = config.include_num_access

        for router_config in config.routers:
            if router_config.num_ports is None:
                router_config.num_ports = config.num_ports
            if router_config.ip_list is None:
                router_config.ip_list = config.ip_list

            if router_config.port_list is None:
                router_config.port_list = config.port_list

            if router_config.protocol_list is None:
                router_config.protocol_list = config.protocol_list

            if router_config.num_rules is None:
                router_config.num_rules = config.num_rules

        for firewall_config in config.firewalls:
            if firewall_config.ip_list is None:
                firewall_config.ip_list = config.ip_list

            if firewall_config.port_list is None:
                firewall_config.port_list = config.port_list

            if firewall_config.protocol_list is None:
                firewall_config.protocol_list = config.protocol_list

            if firewall_config.num_rules is None:
                firewall_config.num_rules = config.num_rules

        hosts = [HostObservation.from_config(config=c, parent_where=where) for c in config.hosts]
        routers = [RouterObservation.from_config(config=c, parent_where=where) for c in config.routers]
        firewalls = [FirewallObservation.from_config(config=c, parent_where=where) for c in config.firewalls]

        cls(where=where, hosts=hosts, routers=routers, firewalls=firewalls)
