from primaite.config.lay_down_config import data_manipulation_config_path
from primaite.config.training_config import main_training_config_path
from primaite.main import run


def test_primaite_main_e2e():
    """Tests the primaite.main.run function end-to-end."""
    run(main_training_config_path(), data_manipulation_config_path())
