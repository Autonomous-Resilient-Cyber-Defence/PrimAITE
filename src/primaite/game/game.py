"""PrimAITE game - Encapsulates the simulation and agents."""
from ipaddress import IPv4Address
from typing import Dict, List, Tuple

from pydantic import BaseModel, ConfigDict

from primaite import getLogger
from primaite.game.agent.actions import ActionManager
from primaite.game.agent.data_manipulation_bot import DataManipulationAgent
from primaite.game.agent.interface import AbstractAgent, AgentSettings, ProxyAgent, RandomAgent
from primaite.game.agent.observations import ObservationManager
from primaite.game.agent.rewards import RewardFunction
from primaite.session.io import SessionIO, SessionIOSettings
from primaite.simulator.network.hardware.base import NIC, NodeOperatingState
from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.router import Router
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.network.hardware.nodes.switch import Switch
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.data_manipulation_bot import DataManipulationBot
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer
from primaite.simulator.system.services.web_server.web_server import WebServer

_LOGGER = getLogger(__name__)


class PrimaiteGameOptions(BaseModel):
    """
    Global options which are applicable to all of the agents in the game.

    Currently this is used to restrict which ports and protocols exist in the world of the simulation.
    """

    model_config = ConfigDict(extra="forbid")

    max_episode_length: int = 256
    ports: List[str]
    protocols: List[str]


class PrimaiteGame:
    """
    Primaite game encapsulates the simulation and agents which interact with it.

    Provides main logic loop for the game. However, it does not provide policy training, or a gymnasium environment.
    """

    def __init__(self):
        """Initialise a PrimaiteGame object."""
        self.simulation: Simulation = Simulation()
        """Simulation object with which the agents will interact."""

        self.agents: List[AbstractAgent] = []
        """List of agents."""

        self.rl_agents: List[ProxyAgent] = []
        """Subset of agent list including only the reinforcement learning agents."""

        self.step_counter: int = 0
        """Current timestep within the episode."""

        self.options: PrimaiteGameOptions
        """Special options that apply for the entire game."""

        self.ref_map_nodes: Dict[str, str] = {}
        """Mapping from unique node reference name to node object. Used when parsing config files."""

        self.ref_map_services: Dict[str, str] = {}
        """Mapping from human-readable service reference to service object. Used for parsing config files."""

        self.ref_map_applications: Dict[str, str] = {}
        """Mapping from human-readable application reference to application object. Used for parsing config files."""

        self.ref_map_links: Dict[str, str] = {}
        """Mapping from human-readable link reference to link object. Used when parsing config files."""

        self.save_step_metadata: bool = False
        """Whether to save the RL agents' action, environment state, and other data at every single step."""

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

        Warning: This method should only be used with scripted agents. For RL agents, the environment that the agent
        interacts with should implement a step method that calls methods used by this method. For example, if using a
        single-agent gym, make sure to update the ProxyAgent's action with the action before calling
        ``self.apply_agent_actions()``.
        """
        _LOGGER.debug(f"Stepping. Step counter: {self.step_counter}")

        # Get the current state of the simulation
        sim_state = self.get_sim_state()

        # Update agents' observations and rewards based on the current state
        self.update_agents(sim_state)

        # Apply all actions to simulation as requests
        agent_actions = self.apply_agent_actions()  # noqa

        # Advance timestep
        self.advance_timestep()

    def get_sim_state(self) -> Dict:
        """Get the current state of the simulation."""
        return self.simulation.describe_state()

    def update_agents(self, state: Dict) -> None:
        """Update agents' observations and rewards based on the current state."""
        for agent in self.agents:
            agent.update_observation(state)
            agent.update_reward(state)
            agent.reward_function.total_reward += agent.reward_function.current_reward

    def apply_agent_actions(self) -> Dict[str, Tuple[str, Dict]]:
        """
        Apply all actions to simulation as requests.

        :return: A recap of each agent's actions, in CAOS format.
        :rtype: Dict[str, Tuple[str, Dict]]

        """
        agent_actions = {}
        for agent in self.agents:
            obs = agent.observation_manager.current_observation
            rew = agent.reward_function.current_reward
            action_choice, options = agent.get_action(obs, rew)
            agent_actions[agent.agent_name] = (action_choice, options)
            request = agent.format_request(action_choice, options)
            self.simulation.apply_request(request)
        return agent_actions

    def advance_timestep(self) -> None:
        """Advance timestep."""
        self.step_counter += 1
        _LOGGER.debug(f"Advancing timestep to {self.step_counter} ")
        self.simulation.apply_timestep(self.step_counter)

    def calculate_truncated(self) -> bool:
        """Calculate whether the episode is truncated."""
        current_step = self.step_counter
        max_steps = self.options.max_episode_length
        if current_step >= max_steps:
            return True
        return False

    def close(self) -> None:
        """Close the game, this will close the simulation."""
        return NotImplemented

    @classmethod
    def from_config(cls, cfg: Dict) -> "PrimaiteGame":
        """Create a PrimaiteGame object from a config dictionary.

        The config dictionary should have the following top-level keys:
        1. training_config: options for training the RL agent.
        2. game_config: options for the game itself. Used by PrimaiteGame.
        3. simulation: defines the network topology and the initial state of the simulation.

        The specification for each of the three major areas is described in a separate documentation page.
        # TODO: create documentation page and add links to it here.

        :param cfg: The config dictionary.
        :type cfg: dict
        :return: A PrimaiteGame object.
        :rtype: PrimaiteGame
        """
        io_settings = cfg.get("io_settings", {})
        _ = SessionIO(SessionIOSettings(**io_settings))
        # Instantiating this ensures that the game saves to the correct output dir even without being part of a session

        game = cls()
        game.options = PrimaiteGameOptions(**cfg["game"])
        game.save_step_metadata = cfg.get("io_settings", {}).get("save_step_metadata") or False

        # 1. create simulation
        sim = game.simulation
        net = sim.network

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
                    operating_state=NodeOperatingState.ON,
                )
            elif n_type == "server":
                new_node = Server(
                    hostname=node_cfg["hostname"],
                    ip_address=node_cfg["ip_address"],
                    subnet_mask=node_cfg["subnet_mask"],
                    default_gateway=node_cfg["default_gateway"],
                    dns_server=node_cfg.get("dns_server"),
                    operating_state=NodeOperatingState.ON,
                )
            elif n_type == "switch":
                new_node = Switch(
                    hostname=node_cfg["hostname"],
                    num_ports=node_cfg.get("num_ports"),
                    operating_state=NodeOperatingState.ON,
                )
            elif n_type == "router":
                new_node = Router.from_config(node_cfg)
            else:
                _LOGGER.warning(f"invalid node type {n_type} in config")
            if "services" in node_cfg:
                for service_cfg in node_cfg["services"]:
                    new_service = None
                    service_ref = service_cfg["ref"]
                    service_type = service_cfg["type"]
                    service_types_mapping = {
                        "DNSClient": DNSClient,  # key is equal to the 'name' attr of the service class itself.
                        "DNSServer": DNSServer,
                        "DatabaseClient": DatabaseClient,
                        "DatabaseService": DatabaseService,
                        "WebServer": WebServer,
                        "FTPClient": FTPClient,
                        "FTPServer": FTPServer,
                        "NTPClient": NTPClient,
                        "NTPServer": NTPServer,
                    }
                    if service_type in service_types_mapping:
                        _LOGGER.debug(f"installing {service_type} on node {new_node.hostname}")
                        new_node.software_manager.install(service_types_mapping[service_type])
                        new_service = new_node.software_manager.software[service_type]
                        game.ref_map_services[service_ref] = new_service.uuid
                    else:
                        _LOGGER.warning(f"service type not found {service_type}")
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
                    if service_type == "DatabaseService":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            if "backup_server_ip" in opt:
                                new_service.configure_backup(backup_server=IPv4Address(opt["backup_server_ip"]))
                        new_service.start()

            if "applications" in node_cfg:
                for application_cfg in node_cfg["applications"]:
                    new_application = None
                    application_ref = application_cfg["ref"]
                    application_type = application_cfg["type"]
                    application_types_mapping = {
                        "WebBrowser": WebBrowser,
                        "DataManipulationBot": DataManipulationBot,
                    }
                    if application_type in application_types_mapping:
                        new_node.software_manager.install(application_types_mapping[application_type])
                        new_application = new_node.software_manager.software[application_type]
                        game.ref_map_applications[application_ref] = new_application.uuid
                    else:
                        _LOGGER.warning(f"application type not found {application_type}")

                    if application_type == "DataManipulationBot":
                        if "options" in application_cfg:
                            opt = application_cfg["options"]
                            new_application.configure(
                                server_ip_address=IPv4Address(opt.get("server_ip")),
                                server_password=opt.get("server_password"),
                                payload=opt.get("payload"),
                                port_scan_p_of_success=float(opt.get("port_scan_p_of_success", "0.1")),
                                data_manipulation_p_of_success=float(opt.get("data_manipulation_p_of_success", "0.1")),
                            )
                    elif application_type == "WebBrowser":
                        if "options" in application_cfg:
                            opt = application_cfg["options"]
                            new_application.target_url = opt.get("target_url")
            if "nics" in node_cfg:
                for nic_num, nic_cfg in node_cfg["nics"].items():
                    new_node.connect_nic(NIC(ip_address=nic_cfg["ip_address"], subnet_mask=nic_cfg["subnet_mask"]))

            net.add_node(new_node)
            new_node.power_on()
            game.ref_map_nodes[node_ref] = new_node.uuid

        # 2. create links between nodes
        for link_cfg in links_cfg:
            node_a = net.nodes[game.ref_map_nodes[link_cfg["endpoint_a_ref"]]]
            node_b = net.nodes[game.ref_map_nodes[link_cfg["endpoint_b_ref"]]]
            if isinstance(node_a, Switch):
                endpoint_a = node_a.switch_ports[link_cfg["endpoint_a_port"]]
            else:
                endpoint_a = node_a.ethernet_port[link_cfg["endpoint_a_port"]]
            if isinstance(node_b, Switch):
                endpoint_b = node_b.switch_ports[link_cfg["endpoint_b_port"]]
            else:
                endpoint_b = node_b.ethernet_port[link_cfg["endpoint_b_port"]]
            new_link = net.connect(endpoint_a=endpoint_a, endpoint_b=endpoint_b)
            game.ref_map_links[link_cfg["ref"]] = new_link.uuid

        # 3. create agents
        agents_cfg = cfg["agents"]

        for agent_cfg in agents_cfg:
            agent_ref = agent_cfg["ref"]  # noqa: F841
            agent_type = agent_cfg["type"]
            action_space_cfg = agent_cfg["action_space"]
            observation_space_cfg = agent_cfg["observation_space"]
            reward_function_cfg = agent_cfg["reward_function"]

            # CREATE OBSERVATION SPACE
            obs_space = ObservationManager.from_config(observation_space_cfg, game)

            # CREATE ACTION SPACE
            action_space = ActionManager.from_config(game, action_space_cfg)

            # CREATE REWARD FUNCTION
            reward_function = RewardFunction.from_config(reward_function_cfg)

            # OTHER AGENT SETTINGS
            agent_settings = AgentSettings.from_config(agent_cfg.get("agent_settings"))

            # CREATE AGENT
            if agent_type == "GreenWebBrowsingAgent":
                # TODO: implement non-random agents and fix this parsing
                new_agent = RandomAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=reward_function,
                    agent_settings=agent_settings,
                )
                game.agents.append(new_agent)
            elif agent_type == "ProxyAgent":
                new_agent = ProxyAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=reward_function,
                    agent_settings=agent_settings,
                )
                game.agents.append(new_agent)
                game.rl_agents.append(new_agent)
            elif agent_type == "RedDatabaseCorruptingAgent":
                new_agent = DataManipulationAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=reward_function,
                    agent_settings=agent_settings,
                )
                game.agents.append(new_agent)
            else:
                _LOGGER.warning(f"agent type {agent_type} not found")

        return game
