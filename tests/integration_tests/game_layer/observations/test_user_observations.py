# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import pytest

from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.transmission.transport_layer import PORT_LOOKUP
from tests import TEST_ASSETS_ROOT

DATA_MANIPULATION_CONFIG = TEST_ASSETS_ROOT / "configs" / "data_manipulation.yaml"


@pytest.fixture
def env_with_ssh() -> PrimaiteGymEnv:
    """Build data manipulation environment with SSH port open on router."""
    env = PrimaiteGymEnv(DATA_MANIPULATION_CONFIG)
    env.agent.flatten_obs = False
    router: Router = env.game.simulation.network.get_node_by_hostname("router_1")
    router.acl.add_rule(ACLAction.PERMIT, src_port=PORT_LOOKUP["SSH"], dst_port=PORT_LOOKUP["SSH"], position=3)
    return env


def extract_login_numbers_from_obs(obs):
    """Traverse the observation dictionary and return number of user sessions for all nodes."""
    login_nums = {}
    for node_name, node_obs in obs["NODES"].items():
        login_nums[node_name] = node_obs.get("users")
    return login_nums


class TestUserObservations:
    """Test that the RouterObservation, FirewallObservation, and HostObservation have the correct number of logins."""

    def test_no_sessions_at_episode_start(self, env_with_ssh):
        """Test that all of the login observations start at 0 before any logins occur."""
        obs, *_ = env_with_ssh.step(0)
        logins_obs = extract_login_numbers_from_obs(obs)
        for o in logins_obs.values():
            assert o["local_login"] == 0
            assert o["remote_sessions"] == 0

    def test_single_login(self, env_with_ssh: PrimaiteGymEnv):
        """Test that performing a remote login increases the remote_sessions observation by 1."""
        client_1 = env_with_ssh.game.simulation.network.get_node_by_hostname("client_1")
        client_1.terminal._send_remote_login("admin", "admin", "192.168.1.14")  # connect to database server via ssh
        obs, *_ = env_with_ssh.step(0)
        logins_obs = extract_login_numbers_from_obs(obs)
        db_srv_logins_obs = logins_obs.pop("HOST2")  # this is the index of db server
        assert db_srv_logins_obs["local_login"] == 0
        assert db_srv_logins_obs["remote_sessions"] == 1
        for o in logins_obs.values():  # the remaining obs after popping HOST2
            assert o["local_login"] == 0
            assert o["remote_sessions"] == 0

    def test_logout(self, env_with_ssh: PrimaiteGymEnv):
        """Test that remote_sessions observation correctly decreases upon logout."""
        client_1 = env_with_ssh.game.simulation.network.get_node_by_hostname("client_1")
        client_1.terminal._send_remote_login("admin", "admin", "192.168.1.14")  # connect to database server via ssh
        db_srv = env_with_ssh.game.simulation.network.get_node_by_hostname("database_server")
        db_srv.user_manager.change_user_password("admin", "admin", "different_pass")  # changing password logs out user

        obs, *_ = env_with_ssh.step(0)
        logins_obs = extract_login_numbers_from_obs(obs)
        for o in logins_obs.values():
            assert o["local_login"] == 0
            assert o["remote_sessions"] == 0

    def test_max_observable_sessions(self, env_with_ssh: PrimaiteGymEnv):
        """Log in from 5 remote places and check that only a max of 3 is shown in the observation."""
        MAX_OBSERVABLE_SESSIONS = 3
        # Right now this is hardcoded as 3 in HostObservation, FirewallObservation, and RouterObservation
        obs, *_ = env_with_ssh.step(0)
        logins_obs = extract_login_numbers_from_obs(obs)
        db_srv_logins_obs = logins_obs.pop("HOST2")  # this is the index of db server

        db_srv = env_with_ssh.game.simulation.network.get_node_by_hostname("database_server")
        db_srv.user_session_manager.remote_session_timeout_steps = 20
        db_srv.user_session_manager.max_remote_sessions = 5
        node_names = ("client_1", "client_2", "backup_server", "security_suite", "domain_controller")

        for i, node_name in enumerate(node_names):
            node = env_with_ssh.game.simulation.network.get_node_by_hostname(node_name)
            node.terminal._send_remote_login("admin", "admin", "192.168.1.14")

            obs, *_ = env_with_ssh.step(0)
            logins_obs = extract_login_numbers_from_obs(obs)
            db_srv_logins_obs = logins_obs.pop("HOST2")  # this is the index of db server

            assert db_srv_logins_obs["remote_sessions"] == min(MAX_OBSERVABLE_SESSIONS, i + 1)
            assert len(db_srv.user_session_manager.remote_sessions) == i + 1
