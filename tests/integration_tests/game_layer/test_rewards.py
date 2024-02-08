from primaite.game.agent.rewards import RewardFunction, WebpageUnavailablePenalty
from primaite.simulator.network.hardware.nodes.router import ACLAction, Router
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
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
