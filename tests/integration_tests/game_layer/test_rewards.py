# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import yaml

from primaite.game.agent.interface import AgentHistoryItem
from primaite.game.agent.rewards import ActionPenalty, GreenAdminDatabaseUnreachablePenalty, WebpageUnavailablePenalty
from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService
from tests import TEST_ASSETS_ROOT
from tests.conftest import ControlledAgent


def test_WebpageUnavailablePenalty(game_and_agent):
    """Test that we get the right reward for failing to fetch a website."""
    game, agent = game_and_agent
    agent: ControlledAgent
    comp = WebpageUnavailablePenalty(node_hostname="client_1")

    agent.reward_function.register_component(comp, 0.7)
    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()

    # client 1 has not attempted to fetch webpage yet!
    assert agent.reward_function.current_reward == 0.0

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    browser = client_1.software_manager.software.get("WebBrowser")
    browser.run()
    browser.target_url = "http://www.example.com"
    assert browser.get_webpage()
    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()
    assert agent.reward_function.current_reward == 0.7

    router: Router = game.simulation.network.get_node_by_hostname("router")
    router.acl.add_rule(action=ACLAction.DENY, protocol=IPProtocol.TCP, src_port=Port.HTTP, dst_port=Port.HTTP)
    assert not browser.get_webpage()
    agent.store_action(action)
    game.step()
    assert agent.reward_function.current_reward == -0.7


def test_uc2_rewards(game_and_agent):
    """Test that the reward component correctly applies a penalty when the selected client cannot reach the database."""
    game, agent = game_and_agent
    agent: ControlledAgent

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    server_1.software_manager.install(DatabaseService)
    db_service = server_1.software_manager.software.get("DatabaseService")
    db_service.start()

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    client_1.software_manager.install(DatabaseClient)
    db_client: DatabaseClient = client_1.software_manager.software.get("DatabaseClient")
    db_client.configure(server_ip_address=server_1.network_interface[1].ip_address)
    db_client.run()

    router: Router = game.simulation.network.get_node_by_hostname("router")
    router.acl.add_rule(ACLAction.PERMIT, src_port=Port.POSTGRES_SERVER, dst_port=Port.POSTGRES_SERVER, position=2)

    comp = GreenAdminDatabaseUnreachablePenalty("client_1")

    response = db_client.apply_request(
        [
            "execute",
        ]
    )
    state = game.get_sim_state()
    reward_value = comp.calculate(
        state,
        last_action_response=AgentHistoryItem(
            timestep=0, action="NODE_APPLICATION_EXECUTE", parameters={}, request=["execute"], response=response
        ),
    )
    assert reward_value == 1.0

    router.acl.remove_rule(position=2)

    db_client.apply_request(
        [
            "execute",
        ]
    )
    state = game.get_sim_state()
    reward_value = comp.calculate(
        state,
        last_action_response=AgentHistoryItem(
            timestep=0, action="NODE_APPLICATION_EXECUTE", parameters={}, request=["execute"], response=response
        ),
    )
    assert reward_value == -1.0


def test_shared_reward():
    CFG_PATH = TEST_ASSETS_ROOT / "configs/shared_rewards.yaml"
    with open(CFG_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    env = PrimaiteGymEnv(env_config=cfg)

    env.reset()

    order = env.game._reward_calculation_order
    assert order.index("defender") > order.index("client_1_green_user")
    assert order.index("defender") > order.index("client_2_green_user")

    for step in range(256):
        act = env.action_space.sample()
        env.step(act)
        g1_reward = env.game.agents["client_1_green_user"].reward_function.current_reward
        g2_reward = env.game.agents["client_2_green_user"].reward_function.current_reward
        blue_reward = env.game.agents["defender"].reward_function.current_reward
        assert blue_reward == g1_reward + g2_reward


def test_action_penalty_loads_from_config():
    """Test to ensure that action penalty is correctly loaded from config into PrimaiteGymEnv"""
    CFG_PATH = TEST_ASSETS_ROOT / "configs/action_penalty.yaml"
    with open(CFG_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    env = PrimaiteGymEnv(env_config=cfg)

    env.reset()

    ActionPenalty_Value = env.game.agents["defender"].reward_function.reward_components[2][0].penalty
    CFG_Penalty_Value = cfg["agents"][3]["reward_function"]["reward_components"][2]["options"]["penalty_value"]

    assert ActionPenalty_Value == CFG_Penalty_Value


def test_action_penalty(game_and_agent):
    """Test that the action penalty is correctly applied when agent performs any action"""

    # Create an ActionPenalty Reward
    Penalty = ActionPenalty(agent_name="Test_Blue_Agent", penalty=-1.0)

    game, _ = game_and_agent

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    server_1.software_manager.install(DatabaseService)
    db_service = server_1.software_manager.software.get("DatabaseService")
    db_service.start()

    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    client_1.software_manager.install(DatabaseClient)
    db_client: DatabaseClient = client_1.software_manager.software.get("DatabaseClient")
    db_client.configure(server_ip_address=server_1.network_interface[1].ip_address)
    db_client.run()

    response = db_client.apply_request(
        [
            "execute",
        ]
    )

    state = game.get_sim_state()

    # Assert that penalty is applied if action isn't DONOTHING
    reward_value = Penalty.calculate(
        state,
        last_action_response=AgentHistoryItem(
            timestep=0, action="NODE_APPLICATION_EXECUTE", parameters={}, request=["execute"], response=response
        ),
    )

    assert reward_value == -1.0

    # Assert that no penalty applied for a DONOTHING action
    reward_value = Penalty.calculate(
        state,
        last_action_response=AgentHistoryItem(
            timestep=0, action="DONOTHING", parameters={}, request=["execute"], response=response
        ),
    )

    assert reward_value == 0
