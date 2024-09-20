# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import pytest
import yaml

from primaite.game.agent.interface import AgentHistoryItem
from primaite.game.agent.rewards import ActionPenalty, GreenAdminDatabaseUnreachablePenalty, WebpageUnavailablePenalty
from primaite.game.game import PrimaiteGame
from primaite.interface.request import RequestResponse
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.transport_layer import PORT_LOOKUP
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.utils.validators import PROTOCOL_LOOKUP
from tests import TEST_ASSETS_ROOT
from tests.conftest import ControlledAgent


def test_WebpageUnavailablePenalty(game_and_agent):
    """Test that we get the right reward for failing to fetch a website."""
    # set up the scenario, configure the web browser to the correct url
    game, agent = game_and_agent
    agent: ControlledAgent
    comp = WebpageUnavailablePenalty(node_hostname="client_1")
    client_1 = game.simulation.network.get_node_by_hostname("client_1")
    browser: WebBrowser = client_1.software_manager.software.get("WebBrowser")
    browser.run()
    browser.target_url = "http://www.example.com"
    agent.reward_function.register_component(comp, 0.7)

    # Check that before trying to fetch the webpage, the reward is 0.0
    agent.store_action(("DONOTHING", {}))
    game.step()
    assert agent.reward_function.current_reward == 0.0

    # Check that successfully fetching the webpage yields a reward of 0.7
    agent.store_action(("NODE_APPLICATION_EXECUTE", {"node_id": 0, "application_id": 0}))
    game.step()
    assert agent.reward_function.current_reward == 0.7

    # Block the web traffic, check that failing to fetch the webpage yields a reward of -0.7
    router: Router = game.simulation.network.get_node_by_hostname("router")
    router.acl.add_rule(
        action=ACLAction.DENY,
        protocol=PROTOCOL_LOOKUP["TCP"],
        src_port=PORT_LOOKUP["HTTP"],
        dst_port=PORT_LOOKUP["HTTP"],
    )
    agent.store_action(("NODE_APPLICATION_EXECUTE", {"node_id": 0, "application_id": 0}))
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
    router.acl.add_rule(
        ACLAction.PERMIT, src_port=PORT_LOOKUP["POSTGRES_SERVER"], dst_port=PORT_LOOKUP["POSTGRES_SERVER"], position=2
    )

    comp = GreenAdminDatabaseUnreachablePenalty("client_1")

    request = ["network", "node", "client_1", "application", "DatabaseClient", "execute"]
    response = game.simulation.apply_request(request)
    state = game.get_sim_state()
    ahi = AgentHistoryItem(
        timestep=0, action="NODE_APPLICATION_EXECUTE", parameters={}, request=request, response=response
    )
    reward_value = comp.calculate(state, last_action_response=ahi)
    assert reward_value == 1.0
    assert ahi.reward_info == {"connection_attempt_status": "success"}

    router.acl.remove_rule(position=2)

    response = game.simulation.apply_request(request)
    state = game.get_sim_state()
    ahi = AgentHistoryItem(
        timestep=0, action="NODE_APPLICATION_EXECUTE", parameters={}, request=request, response=response
    )
    reward_value = comp.calculate(
        state,
        last_action_response=ahi,
    )
    assert reward_value == -1.0
    assert ahi.reward_info == {"connection_attempt_status": "failure"}


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
    defender = env.game.agents["defender"]
    act_penalty_obj = None
    for comp in defender.reward_function.reward_components:
        if isinstance(comp[0], ActionPenalty):
            act_penalty_obj = comp[0]
    if act_penalty_obj is None:
        pytest.fail("Action penalty reward component was not added to the agent from config.")
    assert act_penalty_obj.action_penalty == -0.75
    assert act_penalty_obj.do_nothing_penalty == 0.125


def test_action_penalty():
    """Test that the action penalty is correctly applied when agent performs any action"""

    # Create an ActionPenalty Reward
    Penalty = ActionPenalty(action_penalty=-0.75, do_nothing_penalty=0.125)

    # Assert that penalty is applied if action isn't DONOTHING
    reward_value = Penalty.calculate(
        state={},
        last_action_response=AgentHistoryItem(
            timestep=0,
            action="NODE_APPLICATION_EXECUTE",
            parameters={"node_id": 0, "application_id": 1},
            request=["execute"],
            response=RequestResponse.from_bool(True),
        ),
    )

    assert reward_value == -0.75

    # Assert that no penalty applied for a DONOTHING action
    reward_value = Penalty.calculate(
        state={},
        last_action_response=AgentHistoryItem(
            timestep=0,
            action="DONOTHING",
            parameters={},
            request=["do_nothing"],
            response=RequestResponse.from_bool(True),
        ),
    )

    assert reward_value == 0.125


def test_action_penalty_e2e(game_and_agent):
    """Test that we get the right reward for doing actions to fetch a website."""
    game, agent = game_and_agent
    agent: ControlledAgent
    comp = ActionPenalty(action_penalty=-0.75, do_nothing_penalty=0.125)

    agent.reward_function.register_component(comp, 1.0)

    action = ("DONOTHING", {})
    agent.store_action(action)
    game.step()
    assert agent.reward_function.current_reward == 0.125

    action = ("NODE_FILE_SCAN", {"node_id": 0, "folder_id": 0, "file_id": 0})
    agent.store_action(action)
    game.step()
    assert agent.reward_function.current_reward == -0.75
