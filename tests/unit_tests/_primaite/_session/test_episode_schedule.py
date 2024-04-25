# FILEPATH: /home/cade/repos/PrimAITE/tests/unit_tests/_primaite/_session/test_episode_schedule.py

import pytest
import yaml

from primaite.session.episode_schedule import ConstantEpisodeScheduler, EpisodeListScheduler


def test_episode_list_scheduler():
    # Initialize an instance of EpisodeListScheduler

    # Define a schedule and episode data for testing
    schedule = {0: ["episode1"], 1: ["episode2"]}
    episode_data = {"episode1": "data1: 1", "episode2": "data2: 2"}
    base_scenario = """agents: []"""

    scheduler = EpisodeListScheduler(schedule=schedule, episode_data=episode_data, base_scenario=base_scenario)
    # Test when episode number is within the schedule
    result = scheduler(0)
    assert isinstance(result, dict)
    assert yaml.safe_load("data1: 1\nagents: []") == result

    # Test next episode
    result = scheduler(1)
    assert isinstance(result, dict)
    assert yaml.safe_load("data2: 2\nagents: []") == result

    # Test when episode number exceeds the schedule
    result = scheduler(2)
    assert isinstance(result, dict)
    assert yaml.safe_load("data1: 1\nagents: []") == result
    assert scheduler._exceeded_episode_list

    # Test when episode number is a sequence
    scheduler.schedule = {0: ["episode1", "episode2"]}
    result = scheduler(0)
    assert isinstance(result, dict)
    assert yaml.safe_load("data1: 1\ndata2: 2\nagents: []") == result


def test_constant_episode_scheduler():
    # Initialize an instance of ConstantEpisodeScheduler
    config = {"key": "value"}
    scheduler = ConstantEpisodeScheduler(config=config)

    result = scheduler(0)
    assert isinstance(result, dict)
    assert {"key": "value"} == result

    result = scheduler(1)
    assert isinstance(result, dict)
    assert {"key": "value"} == result
