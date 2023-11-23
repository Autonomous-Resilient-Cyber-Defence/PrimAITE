"""PrimAITE session - the main entry point to training agents on PrimAITE."""
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional, Tuple

from arcd_gate.client.gate_client import ActType, GATEClient
from gymnasium import spaces
from gymnasium.core import ActType, ObsType
from gymnasium.spaces.utils import flatten, flatten_space
from pydantic import BaseModel

from primaite import getLogger
from primaite.game.agent.actions import ActionManager
from primaite.game.agent.interface import AbstractAgent, AgentSettings, DataManipulationAgent, RandomAgent
from primaite.game.agent.observations import ObservationSpace
from primaite.game.agent.rewards import RewardFunction
from primaite.simulator.network.hardware.base import Link, NIC, Node
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.red_services.data_manipulation_bot import DataManipulationBot
from primaite.simulator.system.services.service import Service
from primaite.simulator.system.services.web_server.web_server import WebServer

_LOGGER = getLogger(__name__)


class PrimaiteGATEClient(GATEClient):
    """Lightweight wrapper around the GATEClient class that allows PrimAITE to message GATE."""

    def __init__(self, parent_session: "PrimaiteSession", service_port: int = 50000):
        """
        Create a new GATE client for PrimAITE.

        :param parent_session: The parent session object.
        :type parent_session: PrimaiteSession
        :param service_port: The port on which the GATE service is running.
        :type service_port: int, optional
        """
        super().__init__(service_port=service_port)
        self.parent_session: "PrimaiteSession" = parent_session

    @property
    def rl_framework(self) -> str:
        """The reinforcement learning framework to use."""
        return self.parent_session.training_options.rl_framework

    @property
    def rl_algorithm(self) -> str:
        """The reinforcement learning algorithm to use."""
        return self.parent_session.training_options.rl_algorithm

    @property
    def seed(self) -> Optional[int]:
        """The seed to use for the environment's random number generator."""
        return self.parent_session.training_options.seed

    @property
    def n_learn_episodes(self) -> int:
        """The number of episodes in each learning run."""
        return self.parent_session.training_options.n_learn_episodes

    @property
    def n_learn_steps(self) -> int:
        """The number of steps in each learning episode."""
        return self.parent_session.training_options.n_learn_steps

    @property
    def n_eval_episodes(self) -> int:
        """The number of episodes in each evaluation run."""
        return self.parent_session.training_options.n_eval_episodes

    @property
    def n_eval_steps(self) -> int:
        """The number of steps in each evaluation episode."""
        return self.parent_session.training_options.n_eval_steps

    @property
    def action_space(self) -> spaces.Space:
        """The gym action space of the agent."""
        return self.parent_session.rl_agent.action_space.space

    @property
    def observation_space(self) -> spaces.Space:
        """The gymnasium observation space of the agent."""
        return flatten_space(self.parent_session.rl_agent.observation_space.space)

    def step(self, action: ActType) -> Tuple[ObsType, float, bool, bool, Dict]:
        """Take a step in the environment.

        This method is called by GATE to advance the simulation by one timestep.

        :param action: The agent's action.
        :type action: ActType
        :return: The observation, reward, terminal flag, truncated flag, and info dictionary.
        :rtype: Tuple[ObsType, float, bool, bool, Dict]
        """
        self.parent_session.rl_agent.most_recent_action = action
        self.parent_session.step()
        state = self.parent_session.simulation.describe_state()
        obs = self.parent_session.rl_agent.observation_space.observe(state)
        obs = flatten(self.parent_session.rl_agent.observation_space.space, obs)
        rew = self.parent_session.rl_agent.reward_function.calculate(state)
        term = False
        trunc = False
        info = {}
        return obs, rew, term, trunc, info

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[ObsType, Dict]:
        """Reset the environment.

        This method is called when the environment is initialized and at the end of each episode.

        :param seed: The seed to use for the environment's random number generator.
        :type seed: int, optional
        :param options: Additional options for the reset. None are used by PrimAITE but this is included for
            compatibility with GATE.
        :type options: dict[str, Any], optional
        :return: The initial observation and an empty info dictionary.
        :rtype: Tuple[ObsType, Dict]
        """
        self.parent_session.reset()
        state = self.parent_session.simulation.describe_state()
        obs = self.parent_session.rl_agent.observation_space.observe(state)
        obs = flatten(self.parent_session.rl_agent.observation_space.space, obs)
        return obs, {}

    def close(self):
        """Close the session, this will stop the gate client and close the simulation."""
        self.parent_session.close()


class PrimaiteSessionOptions(BaseModel):
    """
    Global options which are applicable to all of the agents in the game.

    Currently this is used to restrict which ports and protocols exist in the world of the simulation.
    """

    ports: List[str]
    protocols: List[str]


class TrainingOptions(BaseModel):
    """Options for training the RL agent."""

    rl_framework: str
    rl_algorithm: str
    seed: Optional[int]
    n_learn_episodes: int
    n_learn_steps: int
    n_eval_episodes: int
    n_eval_steps: int


class PrimaiteSession:
    """The main entrypoint for PrimAITE sessions, this manages a simulation, agents, and connections to ARCD GATE."""

    def __init__(self):
        self.simulation: Simulation = Simulation()
        """Simulation object with which the agents will interact."""
        self.agents: List[AbstractAgent] = []
        """List of agents."""
        self.rl_agent: AbstractAgent
        """The agent from the list which communicates with GATE to perform reinforcement learning."""
        self.step_counter: int = 0
        """Current timestep within the episode."""
        self.episode_counter: int = 0
        """Current episode number."""
        self.options: PrimaiteSessionOptions
        """Special options that apply for the entire game."""
        self.training_options: TrainingOptions
        """Options specific to agent training."""

        self.ref_map_nodes: Dict[str, Node] = {}
        """Mapping from unique node reference name to node object. Used when parsing config files."""
        self.ref_map_services: Dict[str, Service] = {}
        """Mapping from human-readable service reference to service object. Used for parsing config files."""
        self.ref_map_applications: Dict[str, Application] = {}
        """Mapping from human-readable application reference to application object. Used for parsing config files."""
        self.ref_map_links: Dict[str, Link] = {}
        """Mapping from human-readable link reference to link object. Used when parsing config files."""
        self.gate_client: PrimaiteGATEClient = PrimaiteGATEClient(self)
        """Reference to a GATE Client object, which will send data to GATE service for training RL agent."""

    def start_session(self) -> None:
        """Commence the training session, this gives the GATE client control over the simulation/agent loop."""
        self.gate_client.start()

    def step(self):
        """
        Perform one step of the simulation/agent loop.

        This is the main loop of the game. It corresponds to one timestep in the simulation, and one action from each
        agent. The steps are as follows:
            1. The simulation state is updated.
            2. The simulation state is sent to each agent.
            3. Each agent converts the state to an observation and calculates a reward.
            4. Each agent chooses an action based on the observation.
            5. Each agent converts the action to a request.
            6. The simulation applies the requests.
        """
        _LOGGER.debug(f"Stepping primaite session. Step counter: {self.step_counter}")
        # currently designed with assumption that all agents act once per step in order

        for agent in self.agents:
            # 3. primaite session asks simulation to provide initial state
            # 4. primate session gives state to all agents
            # 5. primaite session asks agents to produce an action based on most recent state
            _LOGGER.debug(f"Sending simulation state to agent {agent.agent_name}")
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
            _LOGGER.debug("Getting agent action")
            agent_action, action_options = agent.get_action(agent_obs, agent_reward)
            # 9. CAOS action is converted into request (extra information might be needed to enrich
            # the request, this is what the execution definition is there for)
            _LOGGER.debug(f"Formatting agent action {agent_action}")  # maybe too many debug log statements
            agent_request = agent.format_request(agent_action, action_options)

            # 10. primaite session receives the action from the agents and asks the simulation to apply each
            _LOGGER.debug(f"Sending request to simulation: {agent_request}")
            self.simulation.apply_request(agent_request)

        _LOGGER.debug(f"Initiating simulation step {self.step_counter}")
        self.simulation.apply_timestep(self.step_counter)
        self.step_counter += 1

    def reset(self) -> None:
        """Reset the session, this will reset the simulation."""
        return NotImplemented

    def close(self) -> None:
        """Close the session, this will stop the gate client and close the simulation."""
        return NotImplemented

    @classmethod
    def from_config(cls, cfg: dict) -> "PrimaiteSession":
        """Create a PrimaiteSession object from a config dictionary.

        The config dictionary should have the following top-level keys:
        1. training_config: options for training the RL agent. Used by GATE.
        2. game_config: options for the game itself. Used by PrimaiteSession.
        3. simulation: defines the network topology and the initial state of the simulation.

        The specification for each of the three major areas is described in a separate documentation page.
        # TODO: create documentation page and add links to it here.

        :param cfg: The config dictionary.
        :type cfg: dict
        :return: A PrimaiteSession object.
        :rtype: PrimaiteSession
        """
        sess = cls()
        sess.options = PrimaiteSessionOptions(
            ports=cfg["game_config"]["ports"],
            protocols=cfg["game_config"]["protocols"],
        )
        sess.training_options = TrainingOptions(**cfg["training_config"])
        sim = sess.simulation
        net = sim.network

        sess.ref_map_nodes: Dict[str, Node] = {}
        sess.ref_map_services: Dict[str, Service] = {}
        sess.ref_map_links: Dict[str, Link] = {}

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
                        "WebServer": WebServer,
                        "DataManipulationBot": DataManipulationBot,
                    }
                    if service_type in service_types_mapping:
                        print(f"installing {service_type} on node {new_node.hostname}")
                        new_node.software_manager.install(service_types_mapping[service_type])
                        new_service = new_node.software_manager.software[service_type]
                        sess.ref_map_services[service_ref] = new_service
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
                    if service_type == "DataManipulationBot":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            new_service.configure(
                                server_ip_address=opt.get("server_ip"),
                                payload=opt.get("payload"),
                                port_scan_p_of_success=float(opt.get("port_scan_p_of_success", "0.1")),
                                data_manipulation_p_of_success=float(opt.get("data_manipulation_p_of_success", "0.1")),
                            )

            if "applications" in node_cfg:
                for application_cfg in node_cfg["applications"]:
                    application_ref = application_cfg["ref"]
                    application_type = application_cfg["type"]
                    application_types_mapping = {
                        "WebBrowser": WebBrowser,
                    }
                    if application_type in application_types_mapping:
                        new_node.software_manager.install(application_types_mapping[application_type])
                        new_application = new_node.software_manager.software[application_type]
                        sess.ref_map_applications[application_ref] = new_application
                    else:
                        print(f"application type not found {application_type}")
            if "nics" in node_cfg:
                for nic_num, nic_cfg in node_cfg["nics"].items():
                    new_node.connect_nic(NIC(ip_address=nic_cfg["ip_address"], subnet_mask=nic_cfg["subnet_mask"]))

            net.add_node(new_node)
            new_node.power_on()
            sess.ref_map_nodes[
                node_ref
            ] = (
                new_node.uuid
            )  # TODO: fix incosistency with service and link. Node gets added by uuid, but service by object

        # 2. create links between nodes
        for link_cfg in links_cfg:
            node_a = net.nodes[sess.ref_map_nodes[link_cfg["endpoint_a_ref"]]]
            node_b = net.nodes[sess.ref_map_nodes[link_cfg["endpoint_b_ref"]]]
            if isinstance(node_a, Switch):
                endpoint_a = node_a.switch_ports[link_cfg["endpoint_a_port"]]
            else:
                endpoint_a = node_a.ethernet_port[link_cfg["endpoint_a_port"]]
            if isinstance(node_b, Switch):
                endpoint_b = node_b.switch_ports[link_cfg["endpoint_b_port"]]
            else:
                endpoint_b = node_b.ethernet_port[link_cfg["endpoint_b_port"]]
            new_link = net.connect(endpoint_a=endpoint_a, endpoint_b=endpoint_b)
            sess.ref_map_links[link_cfg["ref"]] = new_link.uuid

        # 3. create agents
        game_cfg = cfg["game_config"]
        agents_cfg = game_cfg["agents"]

        for agent_cfg in agents_cfg:
            agent_ref = agent_cfg["ref"]  # noqa: F841
            agent_type = agent_cfg["type"]
            action_space_cfg = agent_cfg["action_space"]
            observation_space_cfg = agent_cfg["observation_space"]
            reward_function_cfg = agent_cfg["reward_function"]

            # CREATE OBSERVATION SPACE
            obs_space = ObservationSpace.from_config(observation_space_cfg, sess)

            # CREATE ACTION SPACE
            action_space_cfg["options"]["node_uuids"] = []
            # if a list of nodes is defined, convert them from node references to node UUIDs
            for action_node_option in action_space_cfg.get("options", {}).pop("nodes", {}):
                if "node_ref" in action_node_option:
                    node_uuid = sess.ref_map_nodes[action_node_option["node_ref"]]
                    action_space_cfg["options"]["node_uuids"].append(node_uuid)
            # Each action space can potentially have a different list of nodes that it can apply to. Therefore,
            # we will pass node_uuids as a part of the action space config.
            # However, it's not possible to specify the node uuids directly in the config, as they are generated
            # dynamically, so we have to translate node references to uuids before passing this config on.

            if "action_list" in action_space_cfg:
                for action_config in action_space_cfg["action_list"]:
                    if "options" in action_config:
                        if "target_router_ref" in action_config["options"]:
                            _target = action_config["options"]["target_router_ref"]
                            action_config["options"]["target_router_uuid"] = sess.ref_map_nodes[_target]

            action_space = ActionManager.from_config(sess, action_space_cfg)

            # CREATE REWARD FUNCTION
            rew_function = RewardFunction.from_config(reward_function_cfg, session=sess)

            agent_settings = AgentSettings.from_config(agent_cfg.get("agent_settings"))

            # CREATE AGENT
            if agent_type == "GreenWebBrowsingAgent":
                # TODO: implement non-random agents and fix this parsing
                new_agent = RandomAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=rew_function,
                    agent_settings=agent_settings,
                )
                sess.agents.append(new_agent)
            elif agent_type == "GATERLAgent":
                new_agent = RandomAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=rew_function,
                    agent_settings=agent_settings,
                )
                sess.agents.append(new_agent)
                sess.rl_agent = new_agent
            elif agent_type == "RedDatabaseCorruptingAgent":
                new_agent = DataManipulationAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=rew_function,
                    agent_settings=agent_settings,
                )
                sess.agents.append(new_agent)
            else:
                print("agent type not found")

        return sess
