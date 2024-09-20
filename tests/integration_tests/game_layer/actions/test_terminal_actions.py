# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Tuple

import pytest

from primaite.game.agent.interface import ProxyAgent
from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.base import UserManager
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction
from primaite.simulator.network.transmission.transport_layer import PORT_LOOKUP
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.services.terminal.terminal import RemoteTerminalConnection


@pytest.fixture
def game_and_agent_fixture(game_and_agent):
    """Create a game with a simple agent that can be controlled by the tests."""
    game, agent = game_and_agent

    router = game.simulation.network.get_node_by_hostname("router")
    router.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["SSH"], dst_port=PORT_LOOKUP["SSH"], position=4)

    return (game, agent)


def test_remote_login(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    game, agent = game_and_agent_fixture

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    # create a new user account on server_1 that will be logged into remotely
    server_1_usm: UserManager = server_1.software_manager.software["UserManager"]
    server_1_usm.add_user("user123", "password", is_admin=True)

    action = (
        "SSH_TO_REMOTE",
        {
            "node_id": 0,
            "username": "user123",
            "password": "password",
            "remote_ip": str(server_1.network_interface[1].ip_address),
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"

    connection_established = False
    for conn_str, conn_obj in client_1.terminal.connections.items():
        conn_obj: RemoteTerminalConnection
        if conn_obj.ip_address == server_1.network_interface[1].ip_address:
            connection_established = True
    if not connection_established:
        pytest.fail("Remote SSH connection could not be established")


def test_remote_login_wrong_password(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    game, agent = game_and_agent_fixture

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    # create a new user account on server_1 that will be logged into remotely
    server_1_usm: UserManager = server_1.software_manager.software["UserManager"]
    server_1_usm.add_user("user123", "password", is_admin=True)

    action = (
        "SSH_TO_REMOTE",
        {
            "node_id": 0,
            "username": "user123",
            "password": "wrong_password",
            "remote_ip": str(server_1.network_interface[1].ip_address),
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "failure"

    connection_established = False
    for conn_str, conn_obj in client_1.terminal.connections.items():
        conn_obj: RemoteTerminalConnection
        if conn_obj.ip_address == server_1.network_interface[1].ip_address:
            connection_established = True
    if connection_established:
        pytest.fail("Remote SSH connection was established despite wrong password")


def test_remote_login_change_password(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    game, agent = game_and_agent_fixture

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    # create a new user account on server_1 that will be logged into remotely
    server_1_um: UserManager = server_1.software_manager.software["UserManager"]
    server_1_um.add_user("user123", "password", is_admin=True)

    action = (
        "NODE_ACCOUNTS_CHANGE_PASSWORD",
        {
            "node_id": 1,  # server_1
            "username": "user123",
            "current_password": "password",
            "new_password": "different_password",
        },
    )
    agent.store_action(action)
    game.step()
    assert agent.history[-1].response.status == "success"
    assert server_1_um.users["user123"].password == "different_password"


def test_change_password_logs_out_user(game_and_agent_fixture: Tuple[PrimaiteGame, ProxyAgent]):
    game, agent = game_and_agent_fixture

    server_1: Server = game.simulation.network.get_node_by_hostname("server_1")
    client_1 = game.simulation.network.get_node_by_hostname("client_1")

    # create a new user account on server_1 that will be logged into remotely
    server_1_usm: UserManager = server_1.software_manager.software["UserManager"]
    server_1_usm.add_user("user123", "password", is_admin=True)

    # Log in remotely
    action = (
        "SSH_TO_REMOTE",
        {
            "node_id": 0,
            "username": "user123",
            "password": "password",
            "remote_ip": str(server_1.network_interface[1].ip_address),
        },
    )
    agent.store_action(action)
    game.step()

    # Change password
    action = (
        "NODE_ACCOUNTS_CHANGE_PASSWORD",
        {
            "node_id": 1,  # server_1
            "username": "user123",
            "current_password": "password",
            "new_password": "different_password",
        },
    )
    agent.store_action(action)
    game.step()

    # Assert that the user cannot execute an action
    action = (
        "NODE_SEND_REMOTE_COMMAND",
        {
            "node_id": 0,
            "remote_ip": str(server_1.network_interface[1].ip_address),
            "command": ["file_system", "create", "file", "folder123", "doggo.pdf", False],
        },
    )
    agent.store_action(action)
    game.step()

    assert server_1.file_system.get_folder("folder123") is None
    assert server_1.file_system.get_file("folder123", "doggo.pdf") is None
