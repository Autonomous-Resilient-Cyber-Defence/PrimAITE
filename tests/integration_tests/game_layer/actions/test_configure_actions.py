# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest
from pydantic import ValidationError

from primaite.game.agent.actions import ConfigureDatabaseClientAction, ConfigureRansomwareScriptAction
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript
from tests.conftest import ControlledAgent


class TestConfigureDatabaseAction:
    def test_configure_ip_password(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent
        agent.action_manager.actions["CONFIGURE_DATABASE_CLIENT"] = ConfigureDatabaseClientAction(agent.action_manager)

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(DatabaseClient)
        db_client: DatabaseClient = client_1.software_manager.software["DatabaseClient"]

        action = (
            "CONFIGURE_DATABASE_CLIENT",
            {
                "node_id": 0,
                "options": {
                    "server_ip_address": "192.168.1.99",
                    "server_password": "admin123",
                },
            },
        )
        agent.store_action(action)
        game.step()

        assert db_client.server_ip_address == IPv4Address("192.168.1.99")
        assert db_client.server_password == "admin123"

    def test_configure_ip(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent
        agent.action_manager.actions["CONFIGURE_DATABASE_CLIENT"] = ConfigureDatabaseClientAction(agent.action_manager)

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(DatabaseClient)
        db_client: DatabaseClient = client_1.software_manager.software["DatabaseClient"]

        action = (
            "CONFIGURE_DATABASE_CLIENT",
            {
                "node_id": 0,
                "options": {
                    "server_ip_address": "192.168.1.99",
                },
            },
        )
        agent.store_action(action)
        game.step()

        assert db_client.server_ip_address == IPv4Address("192.168.1.99")
        assert db_client.server_password is None

    def test_configure_password(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent
        agent.action_manager.actions["CONFIGURE_DATABASE_CLIENT"] = ConfigureDatabaseClientAction(agent.action_manager)

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(DatabaseClient)
        db_client: DatabaseClient = client_1.software_manager.software["DatabaseClient"]
        old_ip = db_client.server_ip_address

        action = (
            "CONFIGURE_DATABASE_CLIENT",
            {
                "node_id": 0,
                "options": {
                    "server_password": "admin123",
                },
            },
        )
        agent.store_action(action)
        game.step()

        assert db_client.server_ip_address == old_ip
        assert db_client.server_password is "admin123"


class TestConfigureRansomwareScriptAction:
    @pytest.mark.parametrize(
        "options",
        [
            {},
            {"server_ip_address": "181.181.181.181"},
            {"server_password": "admin123"},
            {"payload": "ENCRYPT"},
            {
                "server_ip_address": "181.181.181.181",
                "server_password": "admin123",
                "payload": "ENCRYPT",
            },
        ],
    )
    def test_configure_ip_password(self, game_and_agent, options):
        game, agent = game_and_agent
        agent: ControlledAgent
        agent.action_manager.actions["CONFIGURE_RANSOMWARE_SCRIPT"] = ConfigureRansomwareScriptAction(
            agent.action_manager
        )

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(RansomwareScript)
        ransomware_script: RansomwareScript = client_1.software_manager.software["RansomwareScript"]

        old_ip = ransomware_script.server_ip_address
        old_pw = ransomware_script.server_password
        old_payload = ransomware_script.payload

        action = (
            "CONFIGURE_RANSOMWARE_SCRIPT",
            {"node_id": 0, "options": options},
        )
        agent.store_action(action)
        game.step()

        expected_ip = old_ip if "server_ip_address" not in options else IPv4Address(options["server_ip_address"])
        expected_pw = old_pw if "server_password" not in options else options["server_password"]
        expected_payload = old_payload if "payload" not in options else options["payload"]

        assert ransomware_script.server_ip_address == expected_ip
        assert ransomware_script.server_password == expected_pw
        assert ransomware_script.payload == expected_payload

    def test_invalid_options(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent
        agent.action_manager.actions["CONFIGURE_RANSOMWARE_SCRIPT"] = ConfigureRansomwareScriptAction(
            agent.action_manager
        )

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(RansomwareScript)
        ransomware_script: RansomwareScript = client_1.software_manager.software["RansomwareScript"]
        action = (
            "CONFIGURE_RANSOMWARE_SCRIPT",
            {
                "node_id": 0,
                "options": {"server_password": "admin123", "bad_option": 70},
            },
        )
        agent.store_action(action)
        with pytest.raises(ValidationError):
            game.step()
