# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import Tuple
from uuid import uuid4

import pytest

from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.base import User
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server


@pytest.fixture(scope="function")
def client_server_network() -> Tuple[Computer, Server, Network]:
    network = Network()

    client = Computer(
        hostname="client",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    client.power_on()

    server = Server(
        hostname="server",
        ip_address="192.168.1.3",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server.power_on()

    network.connect(client.network_interface[1], server.network_interface[1])

    return client, server, network


def test_local_login_success(client_server_network):
    client, server, network = client_server_network

    assert not client.user_session_manager.local_user_logged_in

    client.user_session_manager.local_login(username="admin", password="admin")

    assert client.user_session_manager.local_user_logged_in


def test_login_count_increases(client_server_network):
    client, server, network = client_server_network

    admin_user: User = client.user_manager.users["admin"]

    assert admin_user.num_of_logins == 0

    client.user_session_manager.local_login(username="admin", password="admin")

    assert admin_user.num_of_logins == 1

    client.user_session_manager.local_login(username="admin", password="admin")

    # shouldn't change as user is already logged in
    assert admin_user.num_of_logins == 1

    client.user_session_manager.local_logout()

    client.user_session_manager.local_login(username="admin", password="admin")

    assert admin_user.num_of_logins == 2


def test_local_login_failure(client_server_network):
    client, server, network = client_server_network

    assert not client.user_session_manager.local_user_logged_in

    client.user_session_manager.local_login(username="jane.doe", password="12345")

    assert not client.user_session_manager.local_user_logged_in


def test_new_user_local_login_success(client_server_network):
    client, server, network = client_server_network

    assert not client.user_session_manager.local_user_logged_in

    client.user_manager.add_user(username="jane.doe", password="12345")

    client.user_session_manager.local_login(username="jane.doe", password="12345")

    assert client.user_session_manager.local_user_logged_in


def test_new_local_login_clears_previous_login(client_server_network):
    client, server, network = client_server_network

    assert not client.user_session_manager.local_user_logged_in

    current_session_id = client.user_session_manager.local_login(username="admin", password="admin")

    assert client.user_session_manager.local_user_logged_in

    assert client.user_session_manager.local_session.user.username == "admin"

    client.user_manager.add_user(username="jane.doe", password="12345")

    new_session_id = client.user_session_manager.local_login(username="jane.doe", password="12345")

    assert client.user_session_manager.local_user_logged_in

    assert client.user_session_manager.local_session.user.username == "jane.doe"

    assert new_session_id != current_session_id


def test_new_local_login_attempt_same_uses_persists(client_server_network):
    client, server, network = client_server_network

    assert not client.user_session_manager.local_user_logged_in

    current_session_id = client.user_session_manager.local_login(username="admin", password="admin")

    assert client.user_session_manager.local_user_logged_in

    assert client.user_session_manager.local_session.user.username == "admin"

    new_session_id = client.user_session_manager.local_login(username="admin", password="admin")

    assert client.user_session_manager.local_user_logged_in

    assert client.user_session_manager.local_session.user.username == "admin"

    assert new_session_id == current_session_id


def test_remote_login_success(client_server_network):
    # partial test for now until we get the terminal application in so that amn actual remote connection can be made
    client, server, network = client_server_network

    assert not server.user_session_manager.remote_sessions

    remote_session_id = server.user_session_manager.remote_login(
        username="admin", password="admin", remote_ip_address="192.168.1.10"
    )

    assert server.user_session_manager.validate_remote_session_uuid(remote_session_id)

    server.user_session_manager.remote_logout(remote_session_id)

    assert not server.user_session_manager.validate_remote_session_uuid(remote_session_id)


def test_remote_login_failure(client_server_network):
    # partial test for now until we get the terminal application in so that amn actual remote connection can be made
    client, server, network = client_server_network

    assert not server.user_session_manager.remote_sessions

    remote_session_id = server.user_session_manager.remote_login(
        username="jane.doe", password="12345", remote_ip_address="192.168.1.10"
    )

    assert not server.user_session_manager.validate_remote_session_uuid(remote_session_id)


def test_new_user_remote_login_success(client_server_network):
    client, server, network = client_server_network

    server.user_manager.add_user(username="jane.doe", password="12345")

    remote_session_id = server.user_session_manager.remote_login(
        username="jane.doe", password="12345", remote_ip_address="192.168.1.10"
    )

    assert server.user_session_manager.validate_remote_session_uuid(remote_session_id)

    server.user_session_manager.remote_logout(remote_session_id)

    assert not server.user_session_manager.validate_remote_session_uuid(remote_session_id)


def test_max_remote_sessions_same_user(client_server_network):
    client, server, network = client_server_network

    remote_session_ids = [
        server.user_session_manager.remote_login(username="admin", password="admin", remote_ip_address="192.168.1.10")
        for _ in range(server.user_session_manager.max_remote_sessions)
    ]

    assert all([server.user_session_manager.validate_remote_session_uuid(id) for id in remote_session_ids])


def test_max_remote_sessions_different_users(client_server_network):
    client, server, network = client_server_network

    remote_session_ids = []

    for i in range(server.user_session_manager.max_remote_sessions):
        username = str(uuid4())
        password = "12345"
        server.user_manager.add_user(username=username, password=password)

        remote_session_ids.append(
            server.user_session_manager.remote_login(
                username=username, password=password, remote_ip_address="192.168.1.10"
            )
        )

    assert all([server.user_session_manager.validate_remote_session_uuid(id) for id in remote_session_ids])


def test_max_remote_sessions_limit_reached(client_server_network):
    client, server, network = client_server_network

    remote_session_ids = [
        server.user_session_manager.remote_login(username="admin", password="admin", remote_ip_address="192.168.1.10")
        for _ in range(server.user_session_manager.max_remote_sessions)
    ]

    assert all([server.user_session_manager.validate_remote_session_uuid(id) for id in remote_session_ids])

    assert len(server.user_session_manager.remote_sessions) == server.user_session_manager.max_remote_sessions

    fourth_attempt_session_id = server.user_session_manager.remote_login(
        username="admin", password="admin", remote_ip_address="192.168.1.10"
    )

    assert not server.user_session_manager.validate_remote_session_uuid(fourth_attempt_session_id)

    assert all([server.user_session_manager.validate_remote_session_uuid(id) for id in remote_session_ids])


def test_single_remote_logout_others_persist(client_server_network):
    client, server, network = client_server_network

    server.user_manager.add_user(username="jane.doe", password="12345")
    server.user_manager.add_user(username="john.doe", password="12345")

    admin_session_id = server.user_session_manager.remote_login(
        username="admin", password="admin", remote_ip_address="192.168.1.10"
    )

    jane_session_id = server.user_session_manager.remote_login(
        username="jane.doe", password="12345", remote_ip_address="192.168.1.10"
    )

    john_session_id = server.user_session_manager.remote_login(
        username="john.doe", password="12345", remote_ip_address="192.168.1.10"
    )

    server.user_session_manager.remote_logout(admin_session_id)

    assert not server.user_session_manager.validate_remote_session_uuid(admin_session_id)

    assert server.user_session_manager.validate_remote_session_uuid(jane_session_id)

    assert server.user_session_manager.validate_remote_session_uuid(john_session_id)

    server.user_session_manager.remote_logout(jane_session_id)

    assert not server.user_session_manager.validate_remote_session_uuid(admin_session_id)

    assert not server.user_session_manager.validate_remote_session_uuid(jane_session_id)

    assert server.user_session_manager.validate_remote_session_uuid(john_session_id)

    server.user_session_manager.remote_logout(john_session_id)

    assert not server.user_session_manager.validate_remote_session_uuid(admin_session_id)

    assert not server.user_session_manager.validate_remote_session_uuid(jane_session_id)

    assert not server.user_session_manager.validate_remote_session_uuid(john_session_id)
