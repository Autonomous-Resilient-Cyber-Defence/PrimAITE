# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.utils.validation.port import Port, PORT_LOOKUP


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
        "node-account-add-user",
        {"node_name": "client_1", "username": "admin_2", "password": "e-tronic-boogaloo", "is_admin": True},
    )
    agent.store_action(action)
    game.step()

    assert len(client_1.user_manager.users) == 2  # new user added
    assert len(client_1.user_manager.admins) == 2

    # add non admin account
    action = (
        "node-account-add-user",
        {"node_name": "client_1", "username": "leeroy.jenkins", "password": "no_plan_needed", "is_admin": False},
    )
    agent.store_action(action)
    game.step()

    assert len(client_1.user_manager.users) == 3  # new user added
    assert len(client_1.user_manager.admins) == 2


def test_user_account_disable_user_action(game_and_agent_fixture):
    """Tests the disable user account action."""
    game, agent = game_and_agent_fixture
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    client_1.user_manager.add_user(username="test", password="password", is_admin=True)
    assert len(client_1.user_manager.users) == 2  # new user added
    assert len(client_1.user_manager.admins) == 2

    test_user = client_1.user_manager.users.get("test")
    assert test_user
    assert test_user.disabled is not True

    # disable test account
    action = (
        "node-account-disable-user",
        {
            "node_name": "client_1",
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

    client_1.user_manager.add_user(username="test", password="password", is_admin=True)

    test_user = client_1.user_manager.users.get("test")
    assert test_user.password == "password"

    # change account password
    action = (
        "node-account-change-password",
        {"node_name": "client_1", "username": "test", "current_password": "password", "new_password": "2Hard_2_Hack"},
    )
    agent.store_action(action)
    game.step()

    assert test_user.password == "2Hard_2_Hack"


def test_user_account_create_terminal_action(game_and_agent_fixture):
    """Tests that agents can use the terminal to create new users."""
    game, agent = game_and_agent_fixture

    router = game.simulation.network.get_node_by_hostname("router")
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["SSH"], dst_port=PORT_LOOKUP["SSH"], position=4)

    server_1 = game.simulation.network.get_node_by_hostname("server_1")
    server_1_usm = server_1.software_manager.software["user-manager"]
    server_1_usm.add_user("user123", "password", is_admin=True)

    action = (
        "node-session-remote-login",
        {
            "node_name": "client_1",
            "username": "user123",
            "password": "password",
            "remote_ip": str(server_1.network_interface[1].ip_address),
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    # Create a new user account via terminal.
    action = (
        "node-send-remote-command",
        {
            "node_name": "client_1",
            "remote_ip": str(server_1.network_interface[1].ip_address),
            "command": ["service", "user-manager", "add_user", "new_user", "new_pass", True],
        },
    )
    agent.store_action(action)
    game.step()
    new_user = server_1.user_manager.users.get("new_user")
    assert new_user
    assert new_user.password == "new_pass"
    assert new_user.disabled is not True


def test_user_account_disable_terminal_action(game_and_agent_fixture):
    """Tests that agents can use the terminal to disable users."""
    game, agent = game_and_agent_fixture
    router = game.simulation.network.get_node_by_hostname("router")
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["SSH"], dst_port=PORT_LOOKUP["SSH"], position=4)

    server_1 = game.simulation.network.get_node_by_hostname("server_1")
    server_1_usm = server_1.software_manager.software["user-manager"]
    server_1_usm.add_user("user123", "password", is_admin=True)

    action = (
        "node-session-remote-login",
        {
            "node_name": "client_1",
            "username": "user123",
            "password": "password",
            "remote_ip": str(server_1.network_interface[1].ip_address),
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    # Disable a user via terminal
    action = (
        "node-send-remote-command",
        {
            "node_name": "client_1",
            "remote_ip": str(server_1.network_interface[1].ip_address),
            "command": ["service", "user-manager", "disable_user", "user123"],
        },
    )
    agent.store_action(action)
    game.step()

    new_user = server_1.user_manager.users.get("user123")
    assert new_user
    assert new_user.disabled is True
