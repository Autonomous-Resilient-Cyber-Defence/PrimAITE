from primaite.game.agent.rewards import GreenAdminDatabaseUnreachablePenalty, WebpageUnavailablePenalty
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService
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

    db_client.apply_request(
        [
            "execute",
        ]
    )
    state = game.get_sim_state()
    reward_value = comp.calculate(state)
    assert reward_value == 1.0

    router.acl.remove_rule(position=2)

    db_client.apply_request(
        [
            "execute",
        ]
    )
    state = game.get_sim_state()
    reward_value = comp.calculate(state)
    assert reward_value == -1.0
