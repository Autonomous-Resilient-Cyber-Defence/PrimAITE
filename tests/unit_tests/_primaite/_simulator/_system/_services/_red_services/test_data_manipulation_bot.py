import pytest

from primaite.simulator.network.hardware.base import Node
from primaite.simulator.network.networks import arcd_uc2_network
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.services.red_services.data_manipulation_bot import (
    DataManipulationAttackStage,
    DataManipulationBot,
)


@pytest.fixture(scope="function")
def dm_client() -> Node:
    network = arcd_uc2_network()
    return network.get_node_by_hostname("client_1")


@pytest.fixture
def dm_bot(dm_client) -> DataManipulationBot:
    return dm_client.software_manager.software["DataManipulationBot"]


def test_create_dm_bot(dm_client):
    data_manipulation_bot: DataManipulationBot = dm_client.software_manager.software["DataManipulationBot"]

    assert data_manipulation_bot.name == "DataManipulationBot"
    assert data_manipulation_bot.port == Port.POSTGRES_SERVER
    assert data_manipulation_bot.protocol == IPProtocol.TCP
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

    assert dm_bot.attack_stage in (DataManipulationAttackStage.COMPLETE, DataManipulationAttackStage.FAILED)
    assert dm_bot.connected
