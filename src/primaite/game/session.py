# What do? Be an entry point for using PrimAITE
# 1. parse monoconfig
# 2. craete simulation
# 3. create actors and configure their actions/observations/rewards/ anything else
# 4. Create connection with ARCD GATE
# 5. idk

from ipaddress import IPv4Address
from typing import Dict, List

from pydantic import BaseModel

from primaite.game.agent.actions import ActionManager
from primaite.game.agent.interface import AbstractAgent
from primaite.game.agent.observations import (
    AclObservation,
    FileObservation,
    FolderObservation,
    ICSObservation,
    LinkObservation,
    NicObservation,
    NodeObservation,
    NullObservation,
    ServiceObservation,
    UC2BlueObservation,
    UC2RedObservation,
)
from primaite.simulator.network.hardware.base import Link, NIC, Node
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database_service import DatabaseService
from primaite.simulator.system.services.dns_client import DNSClient
from primaite.simulator.system.services.dns_server import DNSServer
from primaite.simulator.system.services.red_services.data_manipulation_bot import DataManipulationBot
from primaite.simulator.system.services.service import Service


class PrimaiteSessionOptions(BaseModel):
    ports: List[str]
    protocols: List[str]


class PrimaiteSession:
    def __init__(self):
        self.simulation: Simulation = Simulation()
        self.agents: List[AbstractAgent] = []
        self.step_counter: int = 0
        self.episode_counter: int = 0
        self.options: PrimaiteSessionOptions

    def step(self):
        # currently designed with assumption that all agents act once per step in order

        for agent in self.agents:
            # 3. primaite session asks simulation to provide initial state
            # 4. primate session gives state to all agents
            # 5. primaite session asks agents to produce an action based on most recent state
            sim_state = self.simulation.describe_state()

            # 6. each agent takes most recent state and converts it to CAOS observation
            agent_obs = agent.convert_state_to_obs(sim_state)

            # 7. meanwhile each agent also takes state and calculates reward
            agent_reward = agent.calculate_reward_from_state(sim_state)

            # 8. each agent takes observation and applies decision rule to observation to create CAOS
            #    action(such as random, rulebased, or send to GATE) (therefore, converting CAOS action
            #    to discrete(40) is only necessary for purposes of RL learning, therefore that bit of
            #    code should live inside of the GATE agent subclass)
            # gets action in CAOS format
            agent_action = agent.get_action(agent_obs, agent_reward)
            # 9. CAOS action is converted into request (extra information might be needed to enrich
            # the request, this is what the execution definition is there for)
            agent_request = agent.format_request(agent_action)

            # 10. primaite session receives the action from the agents and asks the simulation to apply each
            self.simulation.apply_action(agent_request)

        self.simulation.apply_timestep(self.step_counter)
        self.step_counter += 1

    @classmethod
    def from_config(cls, cfg: dict) -> "PrimaiteSession":
        sess = cls()
        sim = sess.simulation
        net = sim.network

        ref_map_nodes: Dict[str, Node] = {}
        ref_map_services: Dict[str, Service] = {}
        ref_map_links: Dict[str, Link] = {}

        nodes_cfg = cfg["simulation"]["network"]["nodes"]
        links_cfg = cfg["simulation"]["network"]["links"]
        for node_cfg in nodes_cfg:
            node_ref = node_cfg["ref"]
            n_type = node_cfg["type"]
            if n_type == "computer":
                new_node = Computer(
                    hostname=node_cfg["hostname"],
                    ip_address=node_cfg["ip_address"],
                    subnet_mask=node_cfg["subnet_mask"],
                    default_gateway=node_cfg["default_gateway"],
                    dns_server=node_cfg["dns_server"],
                )
            elif n_type == "server":
                new_node = Server(
                    hostname=node_cfg["hostname"],
                    ip_address=node_cfg["ip_address"],
                    subnet_mask=node_cfg["subnet_mask"],
                    default_gateway=node_cfg["default_gateway"],
                    dns_server=node_cfg.get("dns_server"),
                )
            elif n_type == "switch":
                new_node = Switch(hostname=node_cfg["hostname"], num_ports=node_cfg.get("num_ports"))
            elif n_type == "router":
                new_node = Router(hostname=node_cfg["hostname"], num_ports=node_cfg.get("num_ports"))
                if "ports" in node_cfg:
                    for port_num, port_cfg in node_cfg["ports"].items():
                        new_node.configure_port(
                            port=port_num, ip_address=port_cfg["ip_address"], subnet_mask=port_cfg["subnet_mask"]
                        )
                if "acl" in node_cfg:
                    for r_num, r_cfg in node_cfg["acl"].items():
                        # excuse the uncommon walrus operator ` := `. It's just here as a shorthand, to avoid repeating
                        # this: 'r_cfg.get('src_port')'
                        # Port/IPProtocol. TODO Refactor
                        new_node.acl.add_rule(
                            action=ACLAction[r_cfg["action"]],
                            src_port=None if not (p := r_cfg.get("src_port")) else Port[p],
                            dst_port=None if not (p := r_cfg.get("dst_port")) else Port[p],
                            protocol=None if not (p := r_cfg.get("protocol")) else IPProtocol[p],
                            src_ip_address=r_cfg.get("ip_address"),
                            dst_ip_address=r_cfg.get("ip_address"),
                            position=r_num,
                        )
            else:
                print("invalid node type")
            if "services" in node_cfg:
                for service_cfg in node_cfg["services"]:
                    service_ref = service_cfg["ref"]
                    service_type = service_cfg["type"]
                    service_types_mapping = {
                        "DNSClient": DNSClient,  # key is equal to the 'name' attr of the service class itself.
                        "DNSServer": DNSServer,
                        "DatabaseClient": DatabaseClient,
                        "DatabaseService": DatabaseService,
                        # 'database_backup': ,
                        "DataManipulationBot": DataManipulationBot,
                        # 'web_browser'
                    }
                    if service_type in service_types_mapping:
                        new_node.software_manager.install(service_types_mapping[service_type])
                        new_service = new_node.software_manager.software[service_type]
                        ref_map_services[service_ref] = new_service
                    else:
                        print(f"service type not found {service_type}")
                    # service-dependent options
                    if service_type == "DatabaseClient":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            if "db_server_ip" in opt:
                                new_service.configure(server_ip_address=IPv4Address(opt["db_server_ip"]))
                    if service_type == "DNSServer":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            if "domain_mapping" in opt:
                                for domain, ip in opt["domain_mapping"].items():
                                    new_service.dns_register(domain, ip)
            if "nics" in node_cfg:
                for nic_num, nic_cfg in node_cfg["nics"].items():
                    new_node.connect_nic(NIC(ip_address=nic_cfg["ip_address"], subnet_mask=nic_cfg["subnet_mask"]))

            net.add_node(new_node)
            new_node.power_on()
            ref_map_nodes[node_ref] = new_node.uuid

        # 2. create links between nodes
        for link_cfg in links_cfg:
            node_a = net.nodes[ref_map_nodes[link_cfg["endpoint_a_ref"]]]
            node_b = net.nodes[ref_map_nodes[link_cfg["endpoint_b_ref"]]]
            if isinstance(node_a, Switch):
                endpoint_a = node_a.switch_ports[link_cfg["endpoint_a_port"]]
            else:
                endpoint_a = node_a.ethernet_port[link_cfg["endpoint_a_port"]]
            if isinstance(node_b, Switch):
                endpoint_b = node_b.switch_ports[link_cfg["endpoint_b_port"]]
            else:
                endpoint_b = node_b.ethernet_port[link_cfg["endpoint_b_port"]]
            new_link = net.connect(endpoint_a=endpoint_a, endpoint_b=endpoint_b)
            ref_map_links[link_cfg["ref"]] = new_link.uuid

        # 3. create agents
        game_cfg = cfg["game_config"]
        ports_cfg = game_cfg["ports"]
        protocols_cfg = game_cfg["protocols"]
        agents_cfg = game_cfg["agents"]

        for agent_cfg in agents_cfg:
            agent_ref = agent_cfg["ref"]
            agent_type = agent_cfg["type"]
            action_space_cfg = agent_cfg["action_space"]
            observation_space_cfg = agent_cfg["observation_space"]
            reward_function_cfg = agent_cfg["reward_function"]

            # CREATE OBSERVATION SPACE
            if observation_space_cfg is None:
                obs_space = NullObservation()
            elif observation_space_cfg["type"] == "UC2BlueObservation":
                node_obs_list = []
                link_obs_list = []

                # node ip to index maps ip addresses to node id, as there are potentially multiple nics on a node, there are multiple ip addresses
                node_ip_to_index = {}
                for node_idx, node_cfg in enumerate(nodes_cfg):
                    n_ref = node_cfg["ref"]
                    n_obj = net.nodes[ref_map_nodes[n_ref]]
                    for nic_uuid, nic_obj in n_obj.nics.items():
                        node_ip_to_index[nic_obj.ip_address] = node_idx + 2

                for node_obs_cfg in observation_space_cfg["options"]["nodes"]:
                    node_ref = node_obs_cfg["node_ref"]
                    folder_obs_list = []
                    service_obs_list = []
                    if "services" in node_obs_cfg:
                        for service_obs_cfg in node_obs_cfg["services"]:
                            service_obs_list.append(
                                ServiceObservation(
                                    where=[
                                        "network",
                                        "nodes",
                                        ref_map_nodes[node_ref],
                                        "services",
                                        ref_map_services[service_obs_cfg["service_ref"]],
                                    ]
                                )
                            )
                    if "folders" in node_obs_cfg:
                        for folder_obs_cfg in node_obs_cfg["folders"]:
                            file_obs_list = []
                            if "files" in folder_obs_cfg:
                                for file_obs_cfg in folder_obs_cfg["files"]:
                                    file_obs_list.append(
                                        FileObservation(
                                            where=[
                                                "network",
                                                "nodes",
                                                ref_map_nodes[node_ref],
                                                "folders",
                                                folder_obs_cfg["folder_name"],
                                                "files",
                                                file_obs_cfg["file_name"],
                                            ]
                                        )
                                    )
                            folder_obs_list.append(
                                FolderObservation(
                                    where=[
                                        "network",
                                        "nodes",
                                        ref_map_nodes[node_ref],
                                        "folders",
                                        folder_obs_cfg["folder_name"],
                                    ],
                                    files=file_obs_list,
                                )
                            )
                    nic_obs_list = []
                    for nic_uuid in net.nodes[ref_map_nodes[node_obs_cfg["node_ref"]]].nics.keys():
                        nic_obs_list.append(
                            NicObservation(where=["network", "nodes", ref_map_nodes[node_ref], "NICs", nic_uuid])
                        )
                    node_obs_list.append(
                        NodeObservation(
                            where=["network", "nodes", ref_map_nodes[node_ref]],
                            services=service_obs_list,
                            folders=folder_obs_list,
                            nics=nic_obs_list,
                            logon_status=False,
                        )
                    )
                for link_obs_cfg in observation_space_cfg["options"]["links"]:
                    link_ref = link_obs_cfg["link_ref"]
                    link_obs_list.append(LinkObservation(where=["network", "links", ref_map_links[link_ref]]))

                acl_obs = AclObservation(
                    node_ip_to_id=node_ip_to_index,
                    ports=game_cfg["ports"],
                    protocols=game_cfg["ports"],
                    where=["network", "nodes", observation_space_cfg["options"]["acl"]["router_node_ref"]],
                )
                obs_space = UC2BlueObservation(
                    nodes=node_obs_list, links=link_obs_list, acl=acl_obs, ics=ICSObservation()
                )
            elif observation_space_cfg["type"] == "UC2RedObservation":
                obs_space = UC2RedObservation.from_config(observation_space_cfg["options"], sim=sim)
            else:
                print("observation space config not specified correctly.")
                obs_space = NullObservation()

            # CREATE ACTION SPACE
            action_space = ActionManager.from_config(sess, action_space_cfg)

            # CREATE REWARD FUNCTION

            # CREATE AGENT
            if agent_type == "GreenWebBrowsingAgent":
                ...
            elif agent_type == "GATERLAgent":
                ...
            elif agent_type == "RedDatabaseCorruptingAgent":
                ...
            else:
                print("agent type not found")

        return sess
