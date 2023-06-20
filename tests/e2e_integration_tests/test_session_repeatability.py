import time

from primaite import getLogger
from primaite.config.lay_down_config import data_manipulation_config_path
from primaite.main import run_stable_baselines3_a2c, \
    run_stable_baselines3_ppo, run_generic, _update_session_metadata_file, _get_session_path
from primaite.transactions.transactions_to_file import write_transaction_to_file
from tests import TEST_CONFIG_ROOT
from tests.conftest import TestSession, compare_file_content, compare_transaction_file

_LOGGER = getLogger(__name__)


def test_generic_same_results():
    """Runs seeded and deterministic Generic Primaite sessions and checks that the results are the same"""
    print("")
    print("=======================")
    print("Generic test run")
    print("=======================")
    print("")


    # run session 1
    session1 = TestSession(
        TEST_CONFIG_ROOT / "e2e/generic_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    config_values = session1.env.training_config

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = session1.env.episode_steps

    run_generic(
        env=session1.env,
        config_values=session1.env.training_config
    )

    _update_session_metadata_file(session_dir=session1.session_dir, env=session1.env)

    # run session 2
    session2 = TestSession(
        TEST_CONFIG_ROOT / "e2e/generic_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    config_values = session2.env.training_config

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = session2.env.episode_steps

    run_generic(
        env=session2.env,
        config_values=session2.env.training_config
    )

    _update_session_metadata_file(session_dir=session2.session_dir, env=session2.env)

    # wait until the csv files have been closed
    while (not session1.env.csv_file.closed) or (not session2.env.csv_file.closed):
        time.sleep(1)

    # check if both outputs are the same
    assert compare_file_content(
        session1.env.csv_file.name,
        session2.env.csv_file.name,
    ) is True

    # deterministic run
    deterministic = TestSession(
        TEST_CONFIG_ROOT / "e2e/generic_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    deterministic.env.training_config.deterministic = True

    run_generic(
        env=deterministic.env,
        config_values=deterministic.env.training_config
    )

    _update_session_metadata_file(session_dir=deterministic.session_dir, env=deterministic.env)

    # check if both outputs are the same
    assert compare_file_content(
        deterministic.env.csv_file.name,
        TEST_CONFIG_ROOT / "e2e/deterministic_test_outputs/deterministic_generic.csv",
    ) is True


def test_ppo_same_results():
    """Runs seeded and deterministic PPO Primaite sessions and checks that the results are the same"""

    print("")
    print("=======================")
    print("PPO test run")
    print("=======================")
    print("")

    training_session = TestSession(
        TEST_CONFIG_ROOT / "e2e/ppo_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    # Train agent
    training_session.env.training_config.session_type = "TRAINING"

    config_values = training_session.env.training_config

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = training_session.env.episode_steps

    run_stable_baselines3_ppo(
        env=training_session.env,
        config_values=config_values,
        session_path=training_session.session_dir,
        timestamp_str=training_session.timestamp_str,
    )

    write_transaction_to_file(
        transaction_list=training_session.transaction_list,
        session_path=training_session.session_dir,
        timestamp_str=training_session.timestamp_str,
    )

    _update_session_metadata_file(session_dir=training_session.session_dir, env=training_session.env)

    # Evaluate Agent again
    eval_session1 = TestSession(
        TEST_CONFIG_ROOT / "e2e/ppo_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = eval_session1.env.episode_steps
    eval_session1.env.training_config.session_type = "EVALUATE"

    # load the agent that was trained previously
    eval_session1.env.training_config.load_agent = True
    eval_session1.env.training_config.agent_load_file = _get_session_path(training_session.session_timestamp) / f"agent_saved_{training_session.timestamp_str}.zip"

    config_values = eval_session1.env.training_config

    run_stable_baselines3_ppo(
        env=eval_session1.env,
        config_values=config_values,
        session_path=eval_session1.session_dir,
        timestamp_str=eval_session1.timestamp_str,
    )

    write_transaction_to_file(
        transaction_list=eval_session1.transaction_list,
        session_path=eval_session1.session_dir,
        timestamp_str=eval_session1.timestamp_str,
    )

    _update_session_metadata_file(session_dir=eval_session1.session_dir, env=eval_session1.env)

    eval_session2 = TestSession(
        TEST_CONFIG_ROOT / "e2e/ppo_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = eval_session2.env.episode_steps
    eval_session2.env.training_config.session_type = "EVALUATE"

    # load the agent that was trained previously
    eval_session2.env.training_config.load_agent = True
    eval_session2.env.training_config.agent_load_file = _get_session_path(
        training_session.session_timestamp) / f"agent_saved_{training_session.timestamp_str}.zip"

    config_values = eval_session2.env.training_config

    run_stable_baselines3_ppo(
        env=eval_session2.env,
        config_values=config_values,
        session_path=eval_session2.session_dir,
        timestamp_str=eval_session2.timestamp_str,
    )

    write_transaction_to_file(
        transaction_list=eval_session2.transaction_list,
        session_path=eval_session2.session_dir,
        timestamp_str=eval_session2.timestamp_str,
    )

    _update_session_metadata_file(session_dir=eval_session2.session_dir, env=eval_session2.env)

    # check if both eval outputs are the same
    assert compare_transaction_file(
        eval_session1.session_dir / f"all_transactions_{eval_session1.timestamp_str}.csv",
        eval_session2.session_dir / f"all_transactions_{eval_session2.timestamp_str}.csv",
    ) is True

    # deterministic run
    deterministic = TestSession(
        TEST_CONFIG_ROOT / "e2e/ppo_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    deterministic.env.training_config.deterministic = True

    run_stable_baselines3_ppo(
        env=deterministic.env,
        config_values=config_values,
        session_path=deterministic.session_dir,
        timestamp_str=deterministic.timestamp_str,
    )

    write_transaction_to_file(
        transaction_list=deterministic.transaction_list,
        session_path=deterministic.session_dir,
        timestamp_str=deterministic.timestamp_str,
    )

    _update_session_metadata_file(session_dir=deterministic.session_dir, env=deterministic.env)

    # check if both outputs are the same
    assert compare_transaction_file(
        deterministic.session_dir / f"all_transactions_{deterministic.timestamp_str}.csv",
        TEST_CONFIG_ROOT / "e2e/deterministic_test_outputs/deterministic_ppo.csv",
    ) is True


def test_a2c_same_results():
    """Runs seeded and deterministic A2C Primaite sessions and checks that the results are the same"""

    print("")
    print("=======================")
    print("A2C test run")
    print("=======================")
    print("")

    training_session = TestSession(
        TEST_CONFIG_ROOT / "e2e/a2c_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    # Train agent
    training_session.env.training_config.session_type = "TRAINING"

    config_values = training_session.env.training_config

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = training_session.env.episode_steps

    run_stable_baselines3_a2c(
        env=training_session.env,
        config_values=config_values,
        session_path=training_session.session_dir,
        timestamp_str=training_session.timestamp_str,
    )

    write_transaction_to_file(
        transaction_list=training_session.transaction_list,
        session_path=training_session.session_dir,
        timestamp_str=training_session.timestamp_str,
    )

    _update_session_metadata_file(session_dir=training_session.session_dir, env=training_session.env)

    # Evaluate Agent again
    eval_session1 = TestSession(
        TEST_CONFIG_ROOT / "e2e/a2c_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = eval_session1.env.episode_steps
    eval_session1.env.training_config.session_type = "EVALUATE"

    # load the agent that was trained previously
    eval_session1.env.training_config.load_agent = True
    eval_session1.env.training_config.agent_load_file = _get_session_path(
        training_session.session_timestamp) / f"agent_saved_{training_session.timestamp_str}.zip"

    config_values = eval_session1.env.training_config

    run_stable_baselines3_a2c(
        env=eval_session1.env,
        config_values=config_values,
        session_path=eval_session1.session_dir,
        timestamp_str=eval_session1.timestamp_str,
    )

    write_transaction_to_file(
        transaction_list=eval_session1.transaction_list,
        session_path=eval_session1.session_dir,
        timestamp_str=eval_session1.timestamp_str,
    )

    _update_session_metadata_file(session_dir=eval_session1.session_dir, env=eval_session1.env)

    eval_session2 = TestSession(
        TEST_CONFIG_ROOT / "e2e/a2c_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    # Get the number of steps (which is stored in the child config file)
    config_values.num_steps = eval_session2.env.episode_steps
    eval_session2.env.training_config.session_type = "EVALUATE"

    # load the agent that was trained previously
    eval_session2.env.training_config.load_agent = True
    eval_session2.env.training_config.agent_load_file = _get_session_path(
        training_session.session_timestamp) / f"agent_saved_{training_session.timestamp_str}.zip"

    config_values = eval_session2.env.training_config

    run_stable_baselines3_a2c(
        env=eval_session2.env,
        config_values=config_values,
        session_path=eval_session2.session_dir,
        timestamp_str=eval_session2.timestamp_str,
    )

    write_transaction_to_file(
        transaction_list=eval_session2.transaction_list,
        session_path=eval_session2.session_dir,
        timestamp_str=eval_session2.timestamp_str,
    )

    _update_session_metadata_file(session_dir=eval_session2.session_dir, env=eval_session2.env)

    # check if both eval outputs are the same
    assert compare_transaction_file(
        eval_session1.session_dir / f"all_transactions_{eval_session1.timestamp_str}.csv",
        eval_session2.session_dir / f"all_transactions_{eval_session2.timestamp_str}.csv",
    ) is True

    # deterministic run
    deterministic = TestSession(
        TEST_CONFIG_ROOT / "e2e/a2c_deterministic_seeded_training_config.yaml",
        data_manipulation_config_path()
    )

    deterministic.env.training_config.deterministic = True

    run_stable_baselines3_a2c(
        env=deterministic.env,
        config_values=config_values,
        session_path=deterministic.session_dir,
        timestamp_str=deterministic.timestamp_str,
    )

    write_transaction_to_file(
        transaction_list=deterministic.transaction_list,
        session_path=deterministic.session_dir,
        timestamp_str=deterministic.timestamp_str,
    )

    _update_session_metadata_file(session_dir=deterministic.session_dir, env=deterministic.env)

    # check if both outputs are the same
    assert compare_transaction_file(
        deterministic.session_dir / f"all_transactions_{deterministic.timestamp_str}.csv",
        TEST_CONFIG_ROOT / "e2e/deterministic_test_outputs/deterministic_a2c.csv",
    ) is True
