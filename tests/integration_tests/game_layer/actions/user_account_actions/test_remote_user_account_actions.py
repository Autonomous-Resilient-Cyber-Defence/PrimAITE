# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK


def test_remote_logon(game_and_agent):
    """Test that the remote session login action works."""
    game, agent = game_and_agent

    action = (
        "NODE_SESSIONS_REMOTE_LOGIN",
        {"node_id": 0},
    )
    agent.store_action(action)
    game.step()

    # TODO Assert that there is a logged in user


def test_remote_logoff(game_and_agent):
    """Test that the remote session logout action works."""
    game, agent = game_and_agent

    action = (
        "NODE_SESSIONS_REMOTE_LOGIN",
        {"node_id": 0},
    )
    agent.store_action(action)
    game.step()

    # TODO Assert that there is a logged in user

    action = (
        "NODE_SESSIONS_REMOTE_LOGOUT",
        {"node_id": 0},
    )
    agent.store_action(action)
    game.step()

    # TODO Assert the user has logged out
