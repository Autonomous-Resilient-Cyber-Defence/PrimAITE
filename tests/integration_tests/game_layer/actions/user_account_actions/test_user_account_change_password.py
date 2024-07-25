# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
def test_remote_logon(game_and_agent):
    """Test that the remote session login action works."""
    game, agent = game_and_agent

    action = (
        "NODE_ACCOUNTS_CHANGEPASSWORD",
        {"node_id": 0},
    )
    agent.store_action(action)
    game.step()

    # TODO Assert that the user account password is changed
