import pytest

from tests.conftest import TempPrimaiteSession

CFG_PATH = "tests/assets/configs/test_primaite_session.yaml"
TRAINING_ONLY_PATH = "tests/assets/configs/train_only_primaite_session.yaml"
EVAL_ONLY_PATH = "tests/assets/configs/eval_only_primaite_session.yaml"


class TestPrimaiteSession:
    @pytest.mark.parametrize("temp_primaite_session", [[CFG_PATH]], indirect=True)
    def test_creating_session(self, temp_primaite_session):
        """Check that creating a session from config works."""
        with temp_primaite_session as session:
            if not isinstance(session, TempPrimaiteSession):
                raise AssertionError

            assert session is not None
            assert session.simulation
            assert len(session.agents) == 3
            assert len(session.rl_agents) == 1

            assert session.policy
            assert session.env

            assert session.simulation.network
            assert len(session.simulation.network.nodes) == 10

    @pytest.mark.parametrize("temp_primaite_session", [[CFG_PATH]], indirect=True)
    def test_start_session(self, temp_primaite_session):
        """Make sure you can go all the way through the session without errors."""
        with temp_primaite_session as session:
            session: TempPrimaiteSession
            session.start_session()
            # TODO: check that env was closed, that the model was saved, etc.

    @pytest.mark.parametrize("temp_primaite_session", [[TRAINING_ONLY_PATH]], indirect=True)
    def test_training_only_session(self, temp_primaite_session):
        """Check that you can run a training-only session."""
        with temp_primaite_session as session:
            session: TempPrimaiteSession
            session.start_session()
            for i in range(100):
                print(session.io_manager.generate_session_path())
            # TODO: include checks that the model was trained, e.g. that the loss changed and checkpoints were saved?

    @pytest.mark.parametrize("temp_primaite_session", [[EVAL_ONLY_PATH]], indirect=True)
    def test_eval_only_session(self, temp_primaite_session):
        """Check that you can load a model and run an eval-only session."""
        with temp_primaite_session as session:
            session: TempPrimaiteSession
            session.start_session()
            # TODO: include checks that the model was loaded and that the eval-only session ran
