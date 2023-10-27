# flake8: noqa
import logging

from primaite import _PRIMAITE_CONFIG, PRIMAITE_PATHS
from primaite.game.session import PrimaiteSession

_PRIMAITE_CONFIG["log_level"] = logging.DEBUG
print(PRIMAITE_PATHS.app_log_dir_path)

import yaml

from primaite.game.agent.interface import AbstractAgent
from primaite.game.session import PrimaiteSession
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.sim_container import Simulation

with open("example_config.yaml", "r") as file:
    cfg = yaml.safe_load(file)
sess = PrimaiteSession.from_config(cfg)

sess.start_session()
