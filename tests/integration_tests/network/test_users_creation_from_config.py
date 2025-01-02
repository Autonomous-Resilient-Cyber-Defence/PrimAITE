# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import yaml

from primaite.game.game import PrimaiteGame
from primaite.simulator.network.hardware.base import UserManager
from tests import TEST_ASSETS_ROOT


def test_users_from_config():
    config_path = TEST_ASSETS_ROOT / "configs" / "basic_node_with_users.yaml"

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    network = PrimaiteGame.from_config(cfg=config_dict).simulation.network

    client_1 = network.get_node_by_hostname("client_1")

    user_manager: UserManager = client_1.software_manager.software["UserManager"]

    assert len(user_manager.users) == 3

    assert user_manager.users["jane.doe"].password == "1234"
    assert user_manager.users["jane.doe"].is_admin

    assert user_manager.users["john.doe"].password == "password_1"
    assert not user_manager.users["john.doe"].is_admin
