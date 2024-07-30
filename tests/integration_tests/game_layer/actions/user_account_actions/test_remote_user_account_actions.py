# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.network.hardware.nodes.host.computer import Computer


def test_remote_logon(game_and_agent):
    """Test that the remote session login action works."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    client_1.user_manager.add_user(username="test_user", password="password", bypass_can_perform_action=True)

    action = (
        "NODE_SESSIONS_REMOTE_LOGIN",
        {"node_id": 0, "username": "test_user", "password": "password"},
    )
    agent.store_action(action)
    game.step()

    assert len(client_1.user_session_manager.remote_sessions) == 1


def test_remote_logoff(game_and_agent):
    """Test that the remote session logout action works."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    client_1.user_manager.add_user(username="test_user", password="password", bypass_can_perform_action=True)

    action = (
        "NODE_SESSIONS_REMOTE_LOGIN",
        {"node_id": 0, "username": "test_user", "password": "password"},
    )
    agent.store_action(action)
    game.step()

    assert len(client_1.user_session_manager.remote_sessions) == 1

    remote_session_id = client_1.user_session_manager.remote_sessions[0].uuid

    action = (
        "NODE_SESSIONS_REMOTE_LOGOUT",
        {"node_id": 0, "remote_session_id": remote_session_id},
    )
    agent.store_action(action)
    game.step()

    assert len(client_1.user_session_manager.remote_sessions) == 0
