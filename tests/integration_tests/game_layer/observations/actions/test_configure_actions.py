# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

from primaite.game.agent.actions import ConfigureDatabaseClientAction
from primaite.simulator.system.applications.database_client import DatabaseClient
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
