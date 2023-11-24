import pydantic
import pytest

from tests import TEST_ASSETS_ROOT
from tests.conftest import TempPrimaiteSession

CFG_PATH = TEST_ASSETS_ROOT / "configs/test_primaite_session.yaml"
TRAINING_ONLY_PATH = TEST_ASSETS_ROOT / "configs/train_only_primaite_session.yaml"
EVAL_ONLY_PATH = TEST_ASSETS_ROOT / "configs/eval_only_primaite_session.yaml"
MISCONFIGURED_PATH = TEST_ASSETS_ROOT / "configs/bad_primaite_session.yaml"
MULTI_AGENT_PATH = TEST_ASSETS_ROOT / "configs/multi_agent_session.yaml"


class TestPrimaiteSession:
    @pytest.mark.parametrize("temp_primaite_session", [[CFG_PATH]], indirect=True)
    def test_creating_session(self, temp_primaite_session):
        """Check that creating a session from config works."""
        with temp_primaite_session as session:
            if not isinstance(session, TempPrimaiteSession):
                raise AssertionError

            assert session is not None
            assert session.game.simulation
            assert len(session.game.agents) == 3
            assert len(session.game.rl_agents) == 1

            assert session.policy
            assert session.env

            assert session.game.simulation.network
            assert len(session.game.simulation.network.nodes) == 10

    @pytest.mark.parametrize("temp_primaite_session", [[CFG_PATH]], indirect=True)
    def test_start_session(self, temp_primaite_session):
        """Make sure you can go all the way through the session without errors."""
        with temp_primaite_session as session:
            session: TempPrimaiteSession
            session.start_session()

            session_path = session.io_manager.session_path
            assert session_path.exists()
            print(list(session_path.glob("*")))
            checkpoint_dir = session_path / "checkpoints" / "sb3_final"
            assert checkpoint_dir.exists()
            checkpoint_1 = checkpoint_dir / "sb3_model_640_steps.zip"
            checkpoint_2 = checkpoint_dir / "sb3_model_1280_steps.zip"
            checkpoint_3 = checkpoint_dir / "sb3_model_1920_steps.zip"
            assert checkpoint_1.exists()
            assert checkpoint_2.exists()
            assert not checkpoint_3.exists()

    @pytest.mark.parametrize("temp_primaite_session", [[TRAINING_ONLY_PATH]], indirect=True)
    def test_training_only_session(self, temp_primaite_session):
        """Check that you can run a training-only session."""
        with temp_primaite_session as session:
            session: TempPrimaiteSession
            session.start_session()
            # TODO: include checks that the model was trained, e.g. that the loss changed and checkpoints were saved?

    @pytest.mark.parametrize("temp_primaite_session", [[EVAL_ONLY_PATH]], indirect=True)
    def test_eval_only_session(self, temp_primaite_session):
        """Check that you can load a model and run an eval-only session."""
        with temp_primaite_session as session:
            session: TempPrimaiteSession
            session.start_session()
            # TODO: include checks that the model was loaded and that the eval-only session ran

    @pytest.mark.skip(reason="Slow, reenable later")
    @pytest.mark.parametrize("temp_primaite_session", [[MULTI_AGENT_PATH]], indirect=True)
    def test_multi_agent_session(self, temp_primaite_session):
        """Check that we can run a training session with a multi agent system."""
        with temp_primaite_session as session:
            session.start_session()

    def test_error_thrown_on_bad_configuration(self):
        with pytest.raises(pydantic.ValidationError):
            session = TempPrimaiteSession.from_config(MISCONFIGURED_PATH)

    @pytest.mark.parametrize("temp_primaite_session", [[CFG_PATH]], indirect=True)
    def test_session_sim_reset(self, temp_primaite_session):
        with temp_primaite_session as session:
            session: TempPrimaiteSession
            client_1 = session.game.simulation.network.get_node_by_hostname("client_1")
            client_1.software_manager.uninstall("DataManipulationBot")

            assert "DataManipulationBot" not in client_1.software_manager.software

            session.game.reset()
            client_1 = session.game.simulation.network.get_node_by_hostname("client_1")

            assert "DataManipulationBot" in client_1.software_manager.software
