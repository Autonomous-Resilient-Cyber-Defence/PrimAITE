# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
import pytest

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.red_applications.data_manipulation_bot import (
    DataManipulationAttackStage,
    DataManipulationBot,
)
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


@pytest.fixture(scope="function")
def dm_client() -> Node:
    network = arcd_uc2_network()
    return network.get_node_by_hostname("client_1")


@pytest.fixture
def dm_bot(dm_client) -> DataManipulationBot:
    return dm_client.software_manager.software.get("data-manipulation-bot")


def test_create_dm_bot(dm_client):
    data_manipulation_bot: DataManipulationBot = dm_client.software_manager.software.get("data-manipulation-bot")

    assert data_manipulation_bot.name == "data-manipulation-bot"
    assert data_manipulation_bot.port == PORT_LOOKUP["NONE"]
    assert data_manipulation_bot.protocol == PROTOCOL_LOOKUP["NONE"]
    assert data_manipulation_bot.payload == "DELETE"


def test_dm_bot_logon(dm_bot):
    dm_bot.attack_stage = DataManipulationAttackStage.NOT_STARTED

    dm_bot._logon()

    assert dm_bot.attack_stage == DataManipulationAttackStage.LOGON


def test_dm_bot_perform_port_scan_no_success(dm_bot):
    dm_bot.attack_stage = DataManipulationAttackStage.LOGON

    dm_bot._perform_port_scan(p_of_success=0.0)

    assert dm_bot.attack_stage == DataManipulationAttackStage.LOGON


def test_dm_bot_perform_port_scan_success(dm_bot):
    dm_bot.attack_stage = DataManipulationAttackStage.LOGON

    dm_bot._perform_port_scan(p_of_success=1.0)

    assert dm_bot.attack_stage == DataManipulationAttackStage.PORT_SCAN


def test_dm_bot_perform_data_manipulation_no_success(dm_bot):
    dm_bot.attack_stage = DataManipulationAttackStage.PORT_SCAN

    dm_bot._perform_data_manipulation(p_of_success=0.0)

    assert dm_bot.attack_stage == DataManipulationAttackStage.PORT_SCAN


def test_dm_bot_perform_data_manipulation_success(dm_bot):
    dm_bot.attack_stage = DataManipulationAttackStage.PORT_SCAN
    dm_bot.operating_state = ApplicationOperatingState.RUNNING

    dm_bot._perform_data_manipulation(p_of_success=1.0)

    assert dm_bot.attack_stage in (DataManipulationAttackStage.SUCCEEDED, DataManipulationAttackStage.FAILED)
    assert len(dm_bot._host_db_client.client_connections)


def test_dm_bot_fails_without_db_client(dm_client):
    dm_client.software_manager.uninstall("database-client")
    dm_bot = dm_client.software_manager.software.get("data-manipulation-bot")
    assert dm_bot._host_db_client is None
    dm_bot.attack_stage = DataManipulationAttackStage.PORT_SCAN
    dm_bot._perform_data_manipulation(p_of_success=1.0)
    assert dm_bot.attack_stage is DataManipulationAttackStage.FAILED
