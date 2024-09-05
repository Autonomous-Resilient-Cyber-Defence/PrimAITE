# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.network.hardware.nodes.host.computer import Computer


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")
    client_1.start_up_duration = 3

    return (game, agent)


def test_user_account_add_user_action(game_and_agent_fixture):
    """Tests the add user account action."""
    game, agent = game_and_agent_fixture
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    assert len(client_1.user_manager.users) == 1  # admin is created by default
    assert len(client_1.user_manager.admins) == 1

    # add admin account
    action = (
        "NODE_ACCOUNTS_ADD_USER",
        {"node_id": 0, "username": "soccon_diiz", "password": "nuts", "is_admin": True},
    )
    agent.store_action(action)
    game.step()

    assert len(client_1.user_manager.users) == 2  # new user added
    assert len(client_1.user_manager.admins) == 2

    # add non admin account
    action = (
        "NODE_ACCOUNTS_ADD_USER",
        {"node_id": 0, "username": "mike_rotch", "password": "password", "is_admin": False},
    )
    agent.store_action(action)
    game.step()

    assert len(client_1.user_manager.users) == 3  # new user added
    assert len(client_1.user_manager.admins) == 2


def test_user_account_disable_user_action(game_and_agent_fixture):
    """Tests the disable user account action."""
    game, agent = game_and_agent_fixture
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    client_1.user_manager.add_user(username="test", password="icles", is_admin=True)
    assert len(client_1.user_manager.users) == 2  # new user added
    assert len(client_1.user_manager.admins) == 2

    test_user = client_1.user_manager.users.get("test")
    assert test_user
    assert test_user.disabled is not True

    # disable test account
    action = (
        "NODE_ACCOUNTS_DISABLE_USER",
        {
            "node_id": 0,
            "username": "test",
        },
    )
    agent.store_action(action)
    game.step()
    assert test_user.disabled


def test_user_account_change_password_action(game_and_agent_fixture):
    """Tests the change password user account action."""
    game, agent = game_and_agent_fixture
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    client_1.user_manager.add_user(username="test", password="icles", is_admin=True)

    test_user = client_1.user_manager.users.get("test")
    assert test_user.password == "icles"

    # change account password
    action = (
        "NODE_ACCOUNTS_CHANGE_PASSWORD",
        {"node_id": 0, "username": "test", "current_password": "icles", "new_password": "2Hard_2_Hack"},
    )
    agent.store_action(action)
    game.step()

    assert test_user.password == "2Hard_2_Hack"
