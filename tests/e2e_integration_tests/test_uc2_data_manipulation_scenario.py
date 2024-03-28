import yaml

from primaite.game.game import PrimaiteGame
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.data_manipulation_bot import DataManipulationBot
from primaite.simulator.system.services.database.database_service import DatabaseService
from tests import TEST_ASSETS_ROOT


def test_data_manipulation(uc2_network):
    """Tests the UC2 data manipulation scenario end-to-end. Is a work in progress."""
    client_1: Computer = uc2_network.get_node_by_hostname("client_1")
    db_manipulation_bot: DataManipulationBot = client_1.software_manager.software.get("DataManipulationBot")

    database_server: Server = uc2_network.get_node_by_hostname("database_server")
    db_service: DatabaseService = database_server.software_manager.software.get("DatabaseService")

    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software.get("DatabaseClient")

    db_service.backup_database()

    # First check that the DB client on the web_server can successfully query the users table on the database
    assert db_client.query("SELECT")

    # Now we run the DataManipulationBot
    db_manipulation_bot.attack()

    # Now check that the DB client on the web_server cannot query the users table on the database
    assert not db_client.query("SELECT")

    # Now restore the database
    db_service.restore_backup()

    # Now check that the DB client on the web_server can successfully query the users table on the database
    assert db_client.query("SELECT")


def test_application_install_uninstall_on_uc2():
    """Test Application install and uninstall via agent actions mid episode."""
    with open(TEST_ASSETS_ROOT / "configs/test_application_install.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    env = PrimaiteGymEnv(game_config=cfg)
    env.agent.flatten_obs = False
    env.reset()

    _, _, _, _, _ = env.step(0)
    domcon = env.game.simulation.network.get_node_by_hostname("domain_controller")

    _, _, _, _, _ = env.step(78)
    assert "DoSBot" in domcon.software_manager.software

    _, _, _, _, _ = env.step(79)

    assert "DoSBot" not in domcon.software_manager.software
    assert "WebBrowser" in domcon.software_manager.software

    _, _, _, _, _ = env.step(80)
    assert "WebBrowser" not in domcon.software_manager.software
