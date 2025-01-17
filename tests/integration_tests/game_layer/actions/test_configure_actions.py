# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import pytest
from pydantic import ValidationError

from primaite.game.agent.actions.software import (
    ConfigureDatabaseClientAction,
    ConfigureDoSBotAction,
    ConfigureRansomwareScriptAction,
)
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.file_system.file_system_item_abc import FileSystemItemHealthStatus
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.dos_bot import DoSBot
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.utils.validation.port import PORT_LOOKUP
from tests import TEST_ASSETS_ROOT
from tests.conftest import ControlledAgent

APP_CONFIG_YAML = TEST_ASSETS_ROOT / "configs/install_and_configure_apps.yaml"


class TestConfigureDatabaseAction:
    def test_configure_ip_password(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(DatabaseClient)
        db_client: DatabaseClient = client_1.software_manager.software["DatabaseClient"]

        action = (
            "configure_database_client",
            {
                "node_name": "client_1",
                "server_ip_address": "192.168.1.99",
                "server_password": "admin123",
            },
        )
        agent.store_action(action)
        game.step()

        assert db_client.server_ip_address == IPv4Address("192.168.1.99")
        assert db_client.server_password == "admin123"

    def test_configure_ip(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(DatabaseClient)
        db_client: DatabaseClient = client_1.software_manager.software["DatabaseClient"]

        action = (
            "configure_database_client",
            {
                "node_name": "client_1",
                "server_ip_address": "192.168.1.99",
            },
        )
        agent.store_action(action)
        game.step()

        assert db_client.server_ip_address == IPv4Address("192.168.1.99")
        assert db_client.server_password is None

    def test_configure_password(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(DatabaseClient)
        db_client: DatabaseClient = client_1.software_manager.software["DatabaseClient"]
        old_ip = db_client.server_ip_address

        action = (
            "configure_database_client",
            {
                "node_name": "client_1",
                "server_password": "admin123",
            },
        )
        agent.store_action(action)
        game.step()

        assert db_client.server_ip_address == old_ip
        assert db_client.server_password == "admin123"


class TestConfigureRansomwareScriptAction:
    @pytest.mark.parametrize(
        "config",
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
    def test_configure_ip_password(self, game_and_agent, config):
        game, agent = game_and_agent
        agent: ControlledAgent

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(RansomwareScript)
        ransomware_script: RansomwareScript = client_1.software_manager.software["RansomwareScript"]

        old_ip = ransomware_script.server_ip_address
        old_pw = ransomware_script.server_password
        old_payload = ransomware_script.payload

        action = (
            "c2_server_ransomware_configure",
            {"node_name": "client_1", **config},
        )
        agent.store_action(action)
        game.step()

        expected_ip = old_ip if "server_ip_address" not in config else IPv4Address(config["server_ip_address"])
        expected_pw = old_pw if "server_password" not in config else config["server_password"]
        expected_payload = old_payload if "payload" not in config else config["payload"]

        assert ransomware_script.server_ip_address == expected_ip
        assert ransomware_script.server_password == expected_pw
        assert ransomware_script.payload == expected_payload

    def test_invalid_config(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent

        # make sure there is a database client on this node
        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(RansomwareScript)
        ransomware_script: RansomwareScript = client_1.software_manager.software["RansomwareScript"]
        action = (
            "c2_server_ransomware_configure",
            {
                "node_name": "client_1",
                "config": {"server_password": "admin123", "bad_option": 70},
            },
        )
        agent.store_action(action)
        with pytest.raises(ValidationError):
            game.step()


class TestConfigureDoSBot:
    def test_configure_dos_bot(self, game_and_agent):
        game, agent = game_and_agent
        agent: ControlledAgent

        client_1 = game.simulation.network.get_node_by_hostname("client_1")
        client_1.software_manager.install(DoSBot)
        dos_bot: DoSBot = client_1.software_manager.software["DoSBot"]

        action = (
            "configure_dos_bot",
            {
                "node_name": "client_1",
                "target_ip_address": "192.168.1.99",
                "target_port": "POSTGRES_SERVER",
                "payload": "HACC",
                "repeat": False,
                "port_scan_p_of_success": 0.875,
                "dos_intensity": 0.75,
                "max_sessions": 50,
            },
        )
        agent.store_action(action)
        game.step()

        assert dos_bot.target_ip_address == IPv4Address("192.168.1.99")
        assert dos_bot.target_port == PORT_LOOKUP["POSTGRES_SERVER"]
        assert dos_bot.payload == "HACC"
        assert not dos_bot.repeat
        assert dos_bot.port_scan_p_of_success == 0.875
        assert dos_bot.dos_intensity == 0.75
        assert dos_bot.max_sessions == 50


class TestConfigureYAML:
    def test_configure_db_client(self):
        env = PrimaiteGymEnv(env_config=APP_CONFIG_YAML)

        # make sure there's no db client on the node yet
        client_1 = env.game.simulation.network.get_node_by_hostname("client_1")
        assert client_1.software_manager.software.get("DatabaseClient") is None

        # take the install action, check that the db gets installed, step to get it to finish installing
        env.step(1)
        db_client: DatabaseClient = client_1.software_manager.software.get("DatabaseClient")
        assert isinstance(db_client, DatabaseClient)
        assert db_client.operating_state == ApplicationOperatingState.INSTALLING
        env.step(0)
        env.step(0)
        env.step(0)
        env.step(0)

        # configure the ip address and check that it changes, but password doesn't change
        assert db_client.server_ip_address is None
        assert db_client.server_password is None
        env.step(4)
        assert db_client.server_ip_address == IPv4Address("10.0.0.5")
        assert db_client.server_password is None

        # configure the password and check that it changes, make sure this lets us connect to the db
        assert not db_client.connect()
        env.step(5)
        assert db_client.server_password == "correct_password"
        assert db_client.connect()

    def test_c2_server_ransomware_configure(self):
        env = PrimaiteGymEnv(env_config=APP_CONFIG_YAML)
        client_2 = env.game.simulation.network.get_node_by_hostname("client_2")
        assert client_2.software_manager.software.get("RansomwareScript") is None

        # install ransomware script
        env.step(2)
        ransom = client_2.software_manager.software.get("RansomwareScript")
        assert isinstance(ransom, RansomwareScript)
        assert ransom.operating_state == ApplicationOperatingState.INSTALLING
        env.step(0)
        env.step(0)
        env.step(0)
        env.step(0)

        # make sure it's not working yet because it's not configured and there's no db client
        assert not ransom.attack()
        env.step(8)  # install db client on the same node
        env.step(0)
        env.step(0)
        env.step(0)
        env.step(0)  # let it finish installing
        assert not ransom.attack()

        # finally, configure the ransomware script with ip and password
        env.step(6)
        assert ransom.attack()

        db_server = env.game.simulation.network.get_node_by_hostname("server_1")
        db_service: DatabaseService = db_server.software_manager.software.get("DatabaseService")
        assert db_service.db_file.health_status == FileSystemItemHealthStatus.CORRUPT

    def test_configure_dos_bot(self):
        env = PrimaiteGymEnv(env_config=APP_CONFIG_YAML)
        client_3 = env.game.simulation.network.get_node_by_hostname("client_3")
        assert client_3.software_manager.software.get("DoSBot") is None

        # install DoSBot
        env.step(3)
        bot = client_3.software_manager.software.get("DoSBot")
        assert isinstance(bot, DoSBot)
        assert bot.operating_state == ApplicationOperatingState.INSTALLING
        env.step(0)
        env.step(0)
        env.step(0)
        env.step(0)

        # make sure dos bot doesn't work before being configured
        assert not bot.run()
        env.step(7)
        assert bot.run()
