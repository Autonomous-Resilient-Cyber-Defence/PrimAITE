"""Test env creation and behaviour with different observation spaces."""
import numpy as np
import pytest

from primaite.environment.observations import (
    NodeLinkTable,
    NodeStatuses,
    ObservationsHandler,
)
from primaite.environment.primaite_env import Primaite
from tests import TEST_CONFIG_ROOT
from tests.conftest import _get_primaite_env_from_config


@pytest.fixture
def env(request):
    """Build Primaite environment for integration tests of observation space."""
    marker = request.node.get_closest_marker("env_config_paths")
    training_config_path = marker.args[0]["training_config_path"]
    lay_down_config_path = marker.args[0]["lay_down_config_path"]
    env = _get_primaite_env_from_config(
        training_config_path=training_config_path,
        lay_down_config_path=lay_down_config_path,
    )
    yield env


@pytest.mark.env_config_paths(
    dict(
        training_config_path=TEST_CONFIG_ROOT
        / "obs_tests/main_config_without_obs.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT / "obs_tests/laydown.yaml",
    )
)
def test_default_obs_space(env: Primaite):
    """Create environment with no obs space defined in config and check that the default obs space was created."""
    env.update_environent_obs()

    components = env.obs_handler.registered_obs_components

    assert len(components) == 1
    assert isinstance(components[0], NodeLinkTable)


@pytest.mark.env_config_paths(
    dict(
        training_config_path=TEST_CONFIG_ROOT
        / "obs_tests/main_config_without_obs.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT / "obs_tests/laydown.yaml",
    )
)
def test_registering_components(env: Primaite):
    """Test regitering and deregistering a component."""
    handler = ObservationsHandler()
    component = NodeStatuses(env)
    handler.register(component)
    assert component in handler.registered_obs_components
    handler.deregister(component)
    assert component not in handler.registered_obs_components


@pytest.mark.env_config_paths(
    dict(
        training_config_path=TEST_CONFIG_ROOT
        / "obs_tests/main_config_NODE_LINK_TABLE.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT / "obs_tests/laydown.yaml",
    )
)
class TestNodeLinkTable:
    """Test the NodeLinkTable observation component (in isolation)."""

    def test_obs_shape(self, env: Primaite):
        """Try creating env with box observation space."""
        env.update_environent_obs()

        # we have three nodes and two links, with two service
        # therefore the box observation space will have:
        #   * 5 rows (3 nodes + 2 links)
        #   * 6 columns (four fixed and two for the services)
        assert env.env_obs.shape == (5, 6)

    def test_value(self, env: Primaite):
        """Test that the observation is generated correctly.

        The laydown has:
            * 3 nodes (2 service nodes and 1 active node)
            * 2 services
            * 2 links

        Both nodes have both services, and all states are GOOD, therefore the expected observation value is:

            * Node 1:
                * 1 (id)
                * 1 (good hardware state)
                * 3 (compromised OS state)
                * 1 (good file system state)
                * 1 (good TCP state)
                * 1 (good UDP state)
            * Node 2:
                * 2 (id)
                * 1 (good hardware state)
                * 1 (good OS state)
                * 1 (good file system state)
                * 1 (good TCP state)
                * 4 (overwhelmed UDP state)
            * Node 3 (active node):
                * 3 (id)
                * 1 (good hardware state)
                * 1 (good OS state)
                * 1 (good file system state)
                * 0 (doesn't have service1)
                * 0 (doesn't have service2)
            * Link 1:
                * 4 (id)
                * 0 (n/a hardware state)
                * 0 (n/a OS state)
                * 0 (n/a file system state)
                * 999 (999 traffic for service1)
                * 0 (no traffic for service2)
            * Link 2:
                * 5 (id)
                * 0 (good hardware state)
                * 0 (good OS state)
                * 0 (good file system state)
                * 999 (999 traffic service1)
                * 0 (no traffic for service2)
        """
        # act = np.asarray([0,])
        obs, reward, done, info = env.step(0)  # apply the 'do nothing' action

        assert np.array_equal(
            obs,
            [
                [1, 1, 3, 1, 1, 1],
                [2, 1, 1, 1, 1, 4],
                [3, 1, 1, 1, 0, 0],
                [4, 0, 0, 0, 999, 0],
                [5, 0, 0, 0, 999, 0],
            ],
        )


@pytest.mark.env_config_paths(
    dict(
        training_config_path=TEST_CONFIG_ROOT
        / "obs_tests/main_config_NODE_STATUSES.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT / "obs_tests/laydown.yaml",
    )
)
class TestNodeStatuses:
    """Test the NodeStatuses observation component (in isolation)."""

    def test_obs_shape(self, env: Primaite):
        """Try creating env with NodeStatuses as the only component."""
        assert env.env_obs.shape == (15,)

    def test_values(self, env: Primaite):
        """Test that the hardware and software states are encoded correctly.

        The laydown has:
            * one node with a compromised operating system state
            * one node with two services, and the second service is overwhelmed.
            * all other states are good or null
        Therefore, the expected state is:
            * node 1:
                * hardware = good (1)
                * OS = compromised (3)
                * file system = good (1)
                * service 1 = good (1)
                * service 2 = good (1)
            * node 2:
                * hardware = good (1)
                * OS = good (1)
                * file system = good (1)
                * service 1 = good (1)
                * service 2 = overwhelmed (4)
            * node 3 (switch):
                * hardware = good (1)
                * OS = good (1)
                * file system = good (1)
                * service 1 = n/a (0)
                * service 2 = n/a (0)
        """
        obs, _, _, _ = env.step(0)  # apply the 'do nothing' action
        assert np.array_equal(obs, [1, 3, 1, 1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 0, 0])


@pytest.mark.env_config_paths(
    dict(
        training_config_path=TEST_CONFIG_ROOT
        / "obs_tests/main_config_LINK_TRAFFIC_LEVELS.yaml",
        lay_down_config_path=TEST_CONFIG_ROOT / "obs_tests/laydown.yaml",
    )
)
class TestLinkTrafficLevels:
    """Test the LinkTrafficLevels observation component (in isolation)."""

    def test_obs_shape(self, env: Primaite):
        """Try creating env with MultiDiscrete observation space."""
        env.update_environent_obs()

        # we have two links and two services, so the shape should be 2 * 2
        assert env.env_obs.shape == (2 * 2,)

    def test_values(self, env: Primaite):
        """Test that traffic values are encoded correctly.

        The laydown has:
            * two services
            * three nodes
            * two links
            * an IER trying to send 999 bits of data over both links the whole time (via the first service)
            * link bandwidth of 1000, therefore the utilisation is 99.9%
        """
        obs, reward, done, info = env.step(0)
        obs, reward, done, info = env.step(0)

        # the observation space has combine_service_traffic set to False, so the space has this format:
        # [link1_service1, link1_service2, link2_service1, link2_service2]
        # we send 999 bits of data via link1 and link2 on service 1.
        # therefore the first and third elements should be 6 and all others 0
        # (`7` corresponds to 100% utiilsation and `6` corresponds to 87.5%-100%)
        assert np.array_equal(obs, [6, 0, 6, 0])
