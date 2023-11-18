# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import datetime
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union

import nodeenv
import pytest
import yaml

from primaite import getLogger
from primaite.game.session import PrimaiteSession

# from primaite.environment.primaite_env import Primaite
# from primaite.primaite_session import PrimaiteSession
from primaite.simulator.network.container import Network
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service
from tests.mock_and_patch.get_session_path_mock import temp_user_sessions_path

ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1

_LOGGER = getLogger(__name__)

from primaite import PRIMAITE_PATHS

# PrimAITE v3 stuff
from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.hardware.base import Node


class TestService(Service):
    """Test Service class"""

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        pass


class TestApplication(Application):
    """Test Application class"""

    def describe_state(self) -> Dict:
        pass


@pytest.fixture(scope="function")
def uc2_network() -> Network:
    return arcd_uc2_network()


@pytest.fixture(scope="function")
def service(file_system) -> TestService:
    return TestService(
        name="TestService", port=Port.ARP, file_system=file_system, sys_log=SysLog(hostname="test_service")
    )


@pytest.fixture(scope="function")
def application(file_system) -> TestApplication:
    return TestApplication(
        name="TestApplication", port=Port.ARP, file_system=file_system, sys_log=SysLog(hostname="test_application")
    )


@pytest.fixture(scope="function")
def file_system() -> FileSystem:
    return Node(hostname="fs_node").file_system


# PrimAITE v2 stuff
class TempPrimaiteSession(PrimaiteSession):
    """
    A temporary PrimaiteSession class.

    Uses context manager for deletion of files upon exit.
    """

    @classmethod
    def from_config(cls, config_path: Union[str, Path]) -> "TempPrimaiteSession":
        """Create a temporary PrimaiteSession object from a config file."""
        config_path = Path(config_path)
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return super().from_config(cfg=config)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass


@pytest.fixture
def temp_primaite_session(request, monkeypatch) -> TempPrimaiteSession:
    """Create a temporary PrimaiteSession object."""
    monkeypatch.setattr(PRIMAITE_PATHS, "user_sessions_path", temp_user_sessions_path())
    config_path = request.param[0]
    return TempPrimaiteSession.from_config(config_path=config_path)
