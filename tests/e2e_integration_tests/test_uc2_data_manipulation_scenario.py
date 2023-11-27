from primaite.simulator.network.hardware.nodes.computer import Computer
from primaite.simulator.network.hardware.nodes.server import Server
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.red_services.data_manipulation_bot import DataManipulationBot


def test_data_manipulation(uc2_network):
    """Tests the UC2 data manipulation scenario end-to-end. Is a work in progress."""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    db_manipulation_bot: DataManipulationBot = client_1.software_manager.software["DataManipulationBot"]

    database_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = database_server.software_manager.software["DatabaseService"]

    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]

    db_service.backup_database()

    # First check that the DB client on the web_server can successfully query the users table on the database
    assert db_client.query("SELECT")

    # Now we run the DataManipulationBot
    db_manipulation_bot.run()

    # Now check that the DB client on the web_server cannot query the users table on the database
    assert not db_client.query("SELECT")

    # Now restore the database
    db_service.restore_backup()

    # Now check that the DB client on the web_server can successfully query the users table on the database
    assert db_client.query("SELECT")
