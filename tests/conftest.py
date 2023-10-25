# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import datetime
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Union
from unittest.mock import patch

import pytest

from primaite import getLogger

# from primaite.environment.primaite_env import Primaite
# from primaite.primaite_session import PrimaiteSession
from primaite.simulator.network.container import Network
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.sys_log import SysLog
from primaite.simulator.system.services.service import Service
from tests.mock_and_patch.get_session_path_mock import get_temp_session_path

ACTION_SPACE_NODE_VALUES = 1
ACTION_SPACE_NODE_ACTION_VALUES = 1

_LOGGER = getLogger(__name__)

# PrimAITE v3 stuff
from primaite.simulator.file_system.file_system import FileSystem
from primaite.simulator.network.hardware.base import Node


class TestService(Service):
    """Test Service class"""

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
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
def file_system() -> FileSystem:
    return Node(hostname="fs_node").file_system


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
# PrimAITE v2 stuff
class TempPrimaiteSession(PrimaiteSession):
    """
    A temporary PrimaiteSession class.

    Uses context manager for deletion of files upon exit.
    """

    def __init__(
        self,
        training_config_path: Union[str, Path],
        lay_down_config_path: Union[str, Path],
    ):
        super().__init__(training_config_path, lay_down_config_path)
        self.setup()

    @property
    def env(self) -> Primaite:
        """Direct access to the env for ease of testing."""
        return self._agent_session._env  # noqa

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        shutil.rmtree(self.session_path)
        _LOGGER.debug(f"Deleted temp session directory: {self.session_path}")


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
@pytest.fixture
def temp_primaite_session(request):
    """
    Provides a temporary PrimaiteSession instance.

    It's temporary as it uses a temporary directory as the session path.

    To use this fixture you need to:

    - parametrize your test function with:

      - "temp_primaite_session"
      - [[path to training config, path to lay down config]]
    - Include the temp_primaite_session fixture as a param in your test
    function.
    - use the temp_primaite_session as a context manager assigning is the
    name 'session'.

    .. code:: python

        from primaite.config.lay_down_config import dos_very_basic_config_path
        from primaite.config.training_config import main_training_config_path
        @pytest.mark.parametrize(
            "temp_primaite_session",
            [
                [main_training_config_path(), dos_very_basic_config_path()]
            ],
            indirect=True
        )
        def test_primaite_session(temp_primaite_session):
            with temp_primaite_session as session:
                # Learning outputs are saved in session.learning_path
                session.learn()

                # Evaluation outputs are saved in session.evaluation_path
                session.evaluate()

                # To ensure that all files are written, you must call .close()
                session.close()

                # If you need to inspect any session outputs, it must be done
                # inside the context manager

            # Now that we've exited the context manager, the
            # session.session_path directory and its contents are deleted
    """
    training_config_path = request.param[0]
    lay_down_config_path = request.param[1]
    with patch("primaite.agents.agent_abc.get_session_path", get_temp_session_path) as mck:
        mck.session_timestamp = datetime.now()

        return TempPrimaiteSession(training_config_path, lay_down_config_path)


@pytest.skip("Deprecated")  # TODO: implement a similar test for primaite v3
@pytest.fixture
def temp_session_path() -> Path:
    """
    Get a temp directory session path the test session will output to.

    :return: The session directory path.
    """
    session_timestamp = datetime.now()
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = Path(tempfile.gettempdir()) / "_primaite" / date_dir / session_path
    session_path.mkdir(exist_ok=True, parents=True)

    return session_path
