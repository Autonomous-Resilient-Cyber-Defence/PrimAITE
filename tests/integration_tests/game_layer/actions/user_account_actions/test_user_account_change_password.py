# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.network.hardware.nodes.host.computer import Computer


def test_remote_logon(game_and_agent):
    """Test that the remote session login action works."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    client_1.user_manager.add_user(username="test_user", password="password", bypass_can_perform_action=True)
    user = next((user for user in client_1.user_manager.users.values() if user.username == "test_user"), None)

    assert user.password == "password"

    action = (
        "NODE_ACCOUNTS_CHANGEPASSWORD",
        {"node_id": 0, "username": user.username, "current_password": user.password, "new_password": "test_pass"},
    )
    agent.store_action(action)
    game.step()

    assert user.password == "test_pass"
