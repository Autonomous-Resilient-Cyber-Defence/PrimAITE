# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
"""PrimAITE game - Encapsulates the simulation and agents."""
from ipaddress import IPv4Address
from typing import Dict, List, Optional, Union

import numpy as np
from pydantic import BaseModel, ConfigDict

from primaite import DEFAULT_BANDWIDTH, getLogger
from primaite.game.agent.actions import ActionManager
from primaite.game.agent.interface import AbstractAgent, AgentSettings, ProxyAgent
from primaite.game.agent.observations.observation_manager import ObservationManager
from primaite.game.agent.rewards import RewardFunction, SharedReward
from primaite.game.agent.scripted_agents.data_manipulation_bot import DataManipulationAgent
from primaite.game.agent.scripted_agents.probabilistic_agent import ProbabilisticAgent
from primaite.game.agent.scripted_agents.random_agent import PeriodicAgent
from primaite.game.agent.scripted_agents.tap001 import TAP001
from primaite.game.science import graph_has_cycle, topological_sort
from primaite.simulator import SIM_OUTPUT
from primaite.simulator.network.airspace import AirSpaceFrequency
from primaite.simulator.network.hardware.base import NetworkInterface, NodeOperatingState, UserManager
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.host_node import NIC
from primaite.simulator.network.hardware.nodes.host.server import Printer, Server
from primaite.simulator.network.hardware.nodes.network.firewall import Firewall
from primaite.simulator.network.hardware.nodes.network.router import Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.network.hardware.nodes.network.wireless_router import WirelessRouter
from primaite.simulator.network.nmne import NMNEConfig
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.database_client import DatabaseClient  # noqa: F401
from primaite.simulator.system.applications.red_applications.data_manipulation_bot import (  # noqa: F401
    DataManipulationBot,
)
from primaite.simulator.system.applications.red_applications.dos_bot import DoSBot  # noqa: F401
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript  # noqa: F401
from primaite.simulator.system.applications.web_browser import WebBrowser  # noqa: F401
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.ntp.ntp_client import NTPClient
from primaite.simulator.system.services.ntp.ntp_server import NTPServer
from primaite.simulator.system.services.service import Service
from primaite.simulator.system.services.terminal.terminal import Terminal
from primaite.simulator.system.services.web_server.web_server import WebServer
from primaite.simulator.system.software import Software

_LOGGER = getLogger(__name__)

SERVICE_TYPES_MAPPING = {
    "DNSClient": DNSClient,
    "DNSServer": DNSServer,
    "DatabaseService": DatabaseService,
    "WebServer": WebServer,
    "FTPClient": FTPClient,
    "FTPServer": FTPServer,
    "NTPClient": NTPClient,
    "NTPServer": NTPServer,
    "Terminal": Terminal,
}
"""List of available services that can be installed on nodes in the PrimAITE Simulation."""


class PrimaiteGameOptions(BaseModel):
    """
    Global options which are applicable to all of the agents in the game.

    Currently this is used to restrict which ports and protocols exist in the world of the simulation.
    """

    model_config = ConfigDict(extra="forbid")

    seed: int = None
    """Random number seed for RNGs."""
    max_episode_length: int = 256
    """Maximum number of episodes for the PrimAITE game."""
    ports: List[str]
    """A whitelist of available ports in the simulation."""
    protocols: List[str]
    """A whitelist of available protocols in the simulation."""
    thresholds: Optional[Dict] = {}
    """A dict containing the thresholds used for determining what is acceptable during observations."""


class PrimaiteGame:
    """
    Primaite game encapsulates the simulation and agents which interact with it.

    Provides main logic loop for the game. However, it does not provide policy training, or a gymnasium environment.
    """

    def __init__(self):
        """Initialise a PrimaiteGame object."""
        self.simulation: Simulation = Simulation()
        """Simulation object with which the agents will interact."""

        self.agents: Dict[str, AbstractAgent] = {}
        """Mapping from agent name to agent object."""

        self.rl_agents: Dict[str, ProxyAgent] = {}
        """Subset of agents which are intended for reinforcement learning."""

        self.step_counter: int = 0
        """Current timestep within the episode."""

        self.options: PrimaiteGameOptions
        """Special options that apply for the entire game."""

        self.save_step_metadata: bool = False
        """Whether to save the RL agents' action, environment state, and other data at every single step."""

        self._reward_calculation_order: List[str] = [name for name in self.agents]
        """Agent order for reward evaluation, as some rewards can be dependent on other agents' rewards."""

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

        self.pre_timestep()

        if self.step_counter == 0:
            state = self.get_sim_state()
            for agent in self.agents.values():
                agent.update_observation(state=state)
        # Apply all actions to simulation as requests
        self.apply_agent_actions()

        # Advance timestep
        self.advance_timestep()

        # Get the current state of the simulation
        sim_state = self.get_sim_state()

        # Update agents' observations and rewards based on the current state, and the response from the last action
        self.update_agents(state=sim_state)

    def get_sim_state(self) -> Dict:
        """Get the current state of the simulation."""
        return self.simulation.describe_state()

    def update_agents(self, state: Dict) -> None:
        """Update agents' observations and rewards based on the current state."""
        for agent_name in self._reward_calculation_order:
            agent = self.agents[agent_name]
            if self.step_counter > 0:  # can't get reward before first action
                agent.update_reward(state=state)
                agent.save_reward_to_history()
            agent.update_observation(state=state)  # order of this doesn't matter so just use reward order
            agent.reward_function.total_reward += agent.reward_function.current_reward

    def apply_agent_actions(self) -> None:
        """Apply all actions to simulation as requests."""
        for _, agent in self.agents.items():
            obs = agent.observation_manager.current_observation
            action_choice, parameters = agent.get_action(obs, timestep=self.step_counter)
            if SIM_OUTPUT.save_agent_logs:
                agent.logger.debug(f"Chosen Action: {action_choice}")
            request = agent.format_request(action_choice, parameters)
            response = self.simulation.apply_request(request)
            agent.process_action_response(
                timestep=self.step_counter,
                action=action_choice,
                parameters=parameters,
                request=request,
                response=response,
            )

    def pre_timestep(self) -> None:
        """Apply any pre-timestep logic that helps make sure we have the correct observations."""
        self.simulation.pre_timestep(self.step_counter)

    def advance_timestep(self) -> None:
        """Advance timestep."""
        self.step_counter += 1
        _LOGGER.debug(f"Advancing timestep to {self.step_counter} ")
        self.update_agent_loggers()
        self.simulation.apply_timestep(self.step_counter)

    def update_agent_loggers(self) -> None:
        """Updates Agent Loggers with new timestep."""
        for agent in self.agents.values():
            agent.logger.update_timestep(self.step_counter)

    def calculate_truncated(self) -> bool:
        """Calculate whether the episode is truncated."""
        current_step = self.step_counter
        max_steps = self.options.max_episode_length
        if current_step >= max_steps:
            return True
        return False

    def action_mask(self, agent_name: str) -> np.ndarray:
        """
        Return the action mask for the agent.

        This is a boolean list corresponding to the agent's action space. A False entry means this action cannot be
        performed during this step.

        :return: Action mask
        :rtype: List[bool]
        """
        agent = self.agents[agent_name]
        mask = [True] * len(agent.action_manager.action_map)
        for i, action in agent.action_manager.action_map.items():
            request = agent.action_manager.form_request(action_identifier=action[0], action_options=action[1])
            mask[i] = self.simulation._request_manager.check_valid(request, {})
        return np.asarray(mask, dtype=np.int8)

    def close(self) -> None:
        """Close the game, this will close the simulation."""
        return NotImplemented

    def setup_for_episode(self, episode: int) -> None:
        """Perform any final configuration of components to make them ready for the game to start."""
        self.simulation.setup_for_episode(episode=episode)

    @classmethod
    def from_config(cls, cfg: Dict) -> "PrimaiteGame":
        """Create a PrimaiteGame object from a config dictionary.

        The config dictionary should have the following top-level keys:
        1. io_settings: options for logging data during training
        2. game_config: options for the game itself, such as agents.
        3. simulation: defines the network topology and the initial state of the simulation.

        The specification for each of the three major areas is described in a separate documentation page.
        # TODO: create documentation page and add links to it here.

        :param cfg: The config dictionary.
        :type cfg: dict
        :return: A PrimaiteGame object.
        :rtype: PrimaiteGame
        """
        game = cls()
        game.options = PrimaiteGameOptions(**cfg["game"])
        game.save_step_metadata = cfg.get("io_settings", {}).get("save_step_metadata") or False

        # 1. create simulation
        sim = game.simulation
        net = sim.network

        simulation_config = cfg.get("simulation", {})
        network_config = simulation_config.get("network", {})
        airspace_cfg = network_config.get("airspace", {})
        frequency_max_capacity_mbps_cfg = airspace_cfg.get("frequency_max_capacity_mbps", {})

        frequency_max_capacity_mbps_cfg = {AirSpaceFrequency[k]: v for k, v in frequency_max_capacity_mbps_cfg.items()}

        net.airspace.frequency_max_capacity_mbps_ = frequency_max_capacity_mbps_cfg

        nodes_cfg = network_config.get("nodes", [])
        links_cfg = network_config.get("links", [])
        # Set the NMNE capture config
        NetworkInterface.nmne_config = NMNEConfig(**network_config.get("nmne_config", {}))

        for node_cfg in nodes_cfg:
            n_type = node_cfg["type"]
            new_node = None
            if n_type == "computer":
                new_node = Computer(
                    hostname=node_cfg["hostname"],
                    ip_address=node_cfg["ip_address"],
                    subnet_mask=IPv4Address(node_cfg.get("subnet_mask", "255.255.255.0")),
                    default_gateway=node_cfg.get("default_gateway"),
                    dns_server=node_cfg.get("dns_server", None),
                    operating_state=NodeOperatingState.ON
                    if not (p := node_cfg.get("operating_state"))
                    else NodeOperatingState[p.upper()],
                )
            elif n_type == "server":
                new_node = Server(
                    hostname=node_cfg["hostname"],
                    ip_address=node_cfg["ip_address"],
                    subnet_mask=IPv4Address(node_cfg.get("subnet_mask", "255.255.255.0")),
                    default_gateway=node_cfg.get("default_gateway"),
                    dns_server=node_cfg.get("dns_server", None),
                    operating_state=NodeOperatingState.ON
                    if not (p := node_cfg.get("operating_state"))
                    else NodeOperatingState[p.upper()],
                )
            elif n_type == "switch":
                new_node = Switch(
                    hostname=node_cfg["hostname"],
                    num_ports=int(node_cfg.get("num_ports", "8")),
                    operating_state=NodeOperatingState.ON
                    if not (p := node_cfg.get("operating_state"))
                    else NodeOperatingState[p.upper()],
                )
            elif n_type == "router":
                new_node = Router.from_config(node_cfg)
            elif n_type == "firewall":
                new_node = Firewall.from_config(node_cfg)
            elif n_type == "wireless_router":
                new_node = WirelessRouter.from_config(node_cfg, airspace=net.airspace)
            elif n_type == "printer":
                new_node = Printer(
                    hostname=node_cfg["hostname"],
                    ip_address=node_cfg["ip_address"],
                    subnet_mask=node_cfg["subnet_mask"],
                    operating_state=NodeOperatingState.ON
                    if not (p := node_cfg.get("operating_state"))
                    else NodeOperatingState[p.upper()],
                )
            else:
                msg = f"invalid node type {n_type} in config"
                _LOGGER.error(msg)
                raise ValueError(msg)

            if "users" in node_cfg and new_node.software_manager.software.get("UserManager"):
                user_manager: UserManager = new_node.software_manager.software["UserManager"]  # noqa
                for user_cfg in node_cfg["users"]:
                    user_manager.add_user(**user_cfg, bypass_can_perform_action=True)

            def _set_software_listen_on_ports(software: Union[Software, Service], software_cfg: Dict):
                """Set listener ports on software."""
                listen_on_ports = []
                for port_id in set(software_cfg.get("options", {}).get("listen_on_ports", [])):
                    print("yes", port_id)
                    port = None
                    if isinstance(port_id, int):
                        port = Port(port_id)
                    elif isinstance(port_id, str):
                        port = Port[port_id]
                    if port:
                        listen_on_ports.append(port)
                software.listen_on_ports = set(listen_on_ports)

            if "services" in node_cfg:
                for service_cfg in node_cfg["services"]:
                    new_service = None
                    service_type = service_cfg["type"]
                    if service_type in SERVICE_TYPES_MAPPING:
                        _LOGGER.debug(f"installing {service_type} on node {new_node.hostname}")
                        new_node.software_manager.install(SERVICE_TYPES_MAPPING[service_type])
                        new_service = new_node.software_manager.software[service_type]

                        # fixing duration for the service
                        if "fix_duration" in service_cfg.get("options", {}):
                            new_service.fixing_duration = service_cfg["options"]["fix_duration"]

                        _set_software_listen_on_ports(new_service, service_cfg)
                        # start the service
                        new_service.start()
                    else:
                        msg = f"Configuration contains an invalid service type: {service_type}"
                        _LOGGER.error(msg)
                        raise ValueError(msg)
                    # service-dependent options
                    if service_type == "DNSClient":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            if "dns_server" in opt:
                                new_service.dns_server = IPv4Address(opt["dns_server"])
                    if service_type == "DNSServer":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            if "domain_mapping" in opt:
                                for domain, ip in opt["domain_mapping"].items():
                                    new_service.dns_register(domain, IPv4Address(ip))
                    if service_type == "DatabaseService":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            new_service.password = opt.get("db_password", None)
                            if "backup_server_ip" in opt:
                                new_service.configure_backup(backup_server=IPv4Address(opt.get("backup_server_ip")))
                    if service_type == "FTPServer":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            new_service.server_password = opt.get("server_password")
                    if service_type == "NTPClient":
                        if "options" in service_cfg:
                            opt = service_cfg["options"]
                            new_service.ntp_server = IPv4Address(opt.get("ntp_server_ip"))
            if "applications" in node_cfg:
                for application_cfg in node_cfg["applications"]:
                    new_application = None
                    application_type = application_cfg["type"]

                    if application_type in Application._application_registry:
                        new_node.software_manager.install(Application._application_registry[application_type])
                        new_application = new_node.software_manager.software[application_type]  # grab the instance

                        # fixing duration for the application
                        if "fix_duration" in application_cfg.get("options", {}):
                            new_application.fixing_duration = application_cfg["options"]["fix_duration"]
                    else:
                        msg = f"Configuration contains an invalid application type: {application_type}"
                        _LOGGER.error(msg)
                        raise ValueError(msg)

                    _set_software_listen_on_ports(new_application, application_cfg)

                    # run the application
                    new_application.run()

                    if application_type == "DataManipulationBot":
                        if "options" in application_cfg:
                            opt = application_cfg["options"]
                            new_application.configure(
                                server_ip_address=IPv4Address(opt.get("server_ip")),
                                server_password=opt.get("server_password"),
                                payload=opt.get("payload", "DELETE"),
                                port_scan_p_of_success=float(opt.get("port_scan_p_of_success", "0.1")),
                                data_manipulation_p_of_success=float(opt.get("data_manipulation_p_of_success", "0.1")),
                            )
                    elif application_type == "RansomwareScript":
                        if "options" in application_cfg:
                            opt = application_cfg["options"]
                            new_application.configure(
                                server_ip_address=IPv4Address(opt.get("server_ip")) if opt.get("server_ip") else None,
                                server_password=opt.get("server_password"),
                                payload=opt.get("payload", "ENCRYPT"),
                            )
                    elif application_type == "DatabaseClient":
                        if "options" in application_cfg:
                            opt = application_cfg["options"]
                            new_application.configure(
                                server_ip_address=IPv4Address(opt.get("db_server_ip")),
                                server_password=opt.get("server_password"),
                            )
                    elif application_type == "WebBrowser":
                        if "options" in application_cfg:
                            opt = application_cfg["options"]
                            new_application.target_url = opt.get("target_url")
                    elif application_type == "DoSBot":
                        if "options" in application_cfg:
                            opt = application_cfg["options"]
                            new_application.configure(
                                target_ip_address=IPv4Address(opt.get("target_ip_address")),
                                target_port=Port(opt.get("target_port", Port.POSTGRES_SERVER.value)),
                                payload=opt.get("payload"),
                                repeat=bool(opt.get("repeat")),
                                port_scan_p_of_success=float(opt.get("port_scan_p_of_success", "0.1")),
                                dos_intensity=float(opt.get("dos_intensity", "1.0")),
                                max_sessions=int(opt.get("max_sessions", "1000")),
                            )
            if "network_interfaces" in node_cfg:
                for nic_num, nic_cfg in node_cfg["network_interfaces"].items():
                    new_node.connect_nic(NIC(ip_address=nic_cfg["ip_address"], subnet_mask=nic_cfg["subnet_mask"]))

            # temporarily set to 0 so all nodes are initially on
            new_node.start_up_duration = 0
            new_node.shut_down_duration = 0

            net.add_node(new_node)
            # run through the power on step if the node is to be turned on at the start
            if new_node.operating_state == NodeOperatingState.ON:
                new_node.power_on()

            # set start up and shut down duration
            new_node.start_up_duration = int(node_cfg.get("start_up_duration", 3))
            new_node.shut_down_duration = int(node_cfg.get("shut_down_duration", 3))

        # 2. create links between nodes
        for link_cfg in links_cfg:
            node_a = net.get_node_by_hostname(link_cfg["endpoint_a_hostname"])
            node_b = net.get_node_by_hostname(link_cfg["endpoint_b_hostname"])
            bandwidth = link_cfg.get("bandwidth", DEFAULT_BANDWIDTH)  # default value if not configured

            if isinstance(node_a, Switch):
                endpoint_a = node_a.network_interface[link_cfg["endpoint_a_port"]]
            else:
                endpoint_a = node_a.network_interface[link_cfg["endpoint_a_port"]]
            if isinstance(node_b, Switch):
                endpoint_b = node_b.network_interface[link_cfg["endpoint_b_port"]]
            else:
                endpoint_b = node_b.network_interface[link_cfg["endpoint_b_port"]]
            net.connect(endpoint_a=endpoint_a, endpoint_b=endpoint_b, bandwidth=bandwidth)

        # 3. create agents
        agents_cfg = cfg.get("agents", [])

        for agent_cfg in agents_cfg:
            agent_ref = agent_cfg["ref"]  # noqa: F841
            agent_type = agent_cfg["type"]
            action_space_cfg = agent_cfg["action_space"]
            observation_space_cfg = agent_cfg["observation_space"]
            reward_function_cfg = agent_cfg["reward_function"]

            # CREATE OBSERVATION SPACE
            obs_space = ObservationManager.from_config(observation_space_cfg)

            # CREATE ACTION SPACE
            action_space = ActionManager.from_config(game, action_space_cfg)

            # CREATE REWARD FUNCTION
            reward_function = RewardFunction.from_config(reward_function_cfg)

            # CREATE AGENT
            if agent_type == "ProbabilisticAgent":
                # TODO: implement non-random agents and fix this parsing
                settings = agent_cfg.get("agent_settings", {})
                new_agent = ProbabilisticAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=reward_function,
                    settings=settings,
                )
            elif agent_type == "PeriodicAgent":
                settings = PeriodicAgent.Settings(**agent_cfg.get("settings", {}))
                new_agent = PeriodicAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=reward_function,
                    settings=settings,
                )

            elif agent_type == "ProxyAgent":
                agent_settings = AgentSettings.from_config(agent_cfg.get("agent_settings"))
                new_agent = ProxyAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=reward_function,
                    agent_settings=agent_settings,
                )
                game.rl_agents[agent_cfg["ref"]] = new_agent
            elif agent_type == "RedDatabaseCorruptingAgent":
                agent_settings = AgentSettings.from_config(agent_cfg.get("agent_settings"))

                new_agent = DataManipulationAgent(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=reward_function,
                    agent_settings=agent_settings,
                )
            elif agent_type == "TAP001":
                agent_settings = AgentSettings.from_config(agent_cfg.get("agent_settings"))
                new_agent = TAP001(
                    agent_name=agent_cfg["ref"],
                    action_space=action_space,
                    observation_space=obs_space,
                    reward_function=reward_function,
                    agent_settings=agent_settings,
                )
            else:
                msg = f"Configuration error: {agent_type} is not a valid agent type."
                _LOGGER.error(msg)
                raise ValueError(msg)
            game.agents[agent_cfg["ref"]] = new_agent

        # Validate that if any agents are sharing rewards, they aren't forming an infinite loop.
        game.setup_reward_sharing()

        game.update_agents(game.get_sim_state())
        return game

    def setup_reward_sharing(self):
        """Do necessary setup to enable reward sharing between agents.

        This method ensures that there are no cycles in the reward sharing. A cycle would be for example if agent_1
        depends on agent_2 and agent_2 depends on agent_1. It would cause an infinite loop.

        Also, SharedReward requires us to pass it a callback method that will provide the reward of the agent who is
        sharing their reward. This callback is provided by this setup method.

        Finally, this method sorts the agents in order in which rewards will be evaluated to make sure that any rewards
        that rely on the value of another reward are evaluated later.

        :raises RuntimeError: If the reward sharing is specified with a cyclic dependency.
        """
        # construct dependency graph in the reward sharing between agents.
        graph = {}
        for name, agent in self.agents.items():
            graph[name] = set()
            for comp, weight in agent.reward_function.reward_components:
                if isinstance(comp, SharedReward):
                    comp: SharedReward
                    graph[name].add(comp.agent_name)

                    # while constructing the graph, we might as well set up the reward sharing itself.
                    comp.callback = lambda agent_name: self.agents[agent_name].reward_function.current_reward

        # make sure the graph is acyclic. Otherwise we will enter an infinite loop of reward sharing.
        if graph_has_cycle(graph):
            raise RuntimeError(
                (
                    "Detected cycle in agent reward sharing. Check the agent reward function ",
                    "configuration: reward sharing can only go one way.",
                )
            )

        # sort the agents so the rewards that depend on other rewards are always evaluated later
        self._reward_calculation_order = topological_sort(graph)
