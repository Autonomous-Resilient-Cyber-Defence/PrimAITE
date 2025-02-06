# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import copy
from pathlib import Path
from typing import Union

import yaml

from primaite.game.game import PrimaiteGame, SERVICE_TYPES_MAPPING
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_client import DNSClient
from tests import TEST_ASSETS_ROOT

TEST_CONFIG = TEST_ASSETS_ROOT / "configs/software_fixing_duration.yaml"
ONE_ITEM_CONFIG = TEST_ASSETS_ROOT / "configs/fixing_duration_one_item.yaml"

TestApplications = ["dummy-application", "broadcast-test-client"]


def load_config(config_path: Union[str, Path]) -> PrimaiteGame:
    """Returns a PrimaiteGame object which loads the contents of a given yaml path."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return PrimaiteGame.from_config(cfg)


def test_default_fixing_duration():
    """Test that software with no defined fixing duration in config uses the default fixing duration of 2."""
    game = load_config(TEST_CONFIG)
    client_2: Computer = game.simulation.network.get_node_by_hostname("client_2")

    database_client: DatabaseClient = client_2.software_manager.software.get("database-client")
    assert database_client.config.fixing_duration == 2

    dns_client: DNSClient = client_2.software_manager.software.get("dns-client")
    assert dns_client.config.fixing_duration == 2


def test_fixing_duration_set_from_config():
    """Test to check that the fixing duration set for applications and services works as intended."""
    game = load_config(TEST_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    # in config - services take 3 timesteps to fix
    for service in [
        "dns-client",
        "dns-server",
        "database-service",
        "web-server",
        "ftp-client",
        "ftp-server",
        "ntp-server",
    ]:
        assert client_1.software_manager.software.get(service) is not None
        assert client_1.software_manager.software.get(service).config.fixing_duration == 3

    # in config - applications take 1 timestep to fix
    # remove test applications from list
    applications = set(Application._registry) - set(TestApplications)

    for application in ["ransomware-script", "web-browser", "data-manipulation-bot", "dos-bot", "database-client"]:
        assert client_1.software_manager.software.get(application) is not None
        assert client_1.software_manager.software.get(application).config.fixing_duration == 1


def test_fixing_duration_for_one_item():
    """Test that setting fixing duration for one application does not affect other components."""
    game = load_config(ONE_ITEM_CONFIG)
    client_1: Computer = game.simulation.network.get_node_by_hostname("client_1")

    # in config - services take 3 timesteps to fix
    for service in ["dns-client", "dns-server", "web-server", "ftp-client", "ftp-server", "ntp-server"]:
        assert client_1.software_manager.software.get(service) is not None
        assert client_1.software_manager.software.get(service).config.fixing_duration == 2

    # in config - applications take 1 timestep to fix
    # remove test applications from list
    for applications in ["ransomware-script", "web-browser", "data-manipulation-bot", "dos-bot"]:
        assert client_1.software_manager.software.get(applications) is not None
        assert client_1.software_manager.software.get(applications).config.fixing_duration == 2

    database_client: DatabaseClient = client_1.software_manager.software.get("database-client")
    assert database_client.config.fixing_duration == 1

    database_service: DatabaseService = client_1.software_manager.software.get("database-service")
    assert database_service.config.fixing_duration == 5
