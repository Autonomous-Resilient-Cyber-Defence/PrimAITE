from ipaddress import IPv4Address

import pytest

from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.red_applications.dos_bot import DoSAttackStage, DoSBot


@pytest.fixture(scope="function")
def dos_bot() -> DoSBot:
    computer = Computer(
        hostname="compromised_pc", ip_address="192.168.0.1", subnet_mask="255.255.255.0", start_up_duration=0
    )
    computer.power_on()
    computer.software_manager.install(DoSBot)

    dos_bot: DoSBot = computer.software_manager.software.get("DoSBot")
    dos_bot.configure(target_ip_address=IPv4Address("192.168.0.1"))
    dos_bot.set_original_state()
    return dos_bot


def test_dos_bot_creation(dos_bot):
    """Test that the DoS bot is installed on a node."""
    assert dos_bot is not None


def test_dos_bot_reset(dos_bot):
    assert dos_bot.target_ip_address == IPv4Address("192.168.0.1")
    assert dos_bot.target_port is Port.POSTGRES_SERVER
    assert dos_bot.payload is None
    assert dos_bot.repeat is False

    dos_bot.configure(
        target_ip_address=IPv4Address("192.168.1.1"), target_port=Port.HTTP, payload="payload", repeat=True
    )

    # should reset the relevant items
    dos_bot.reset_component_for_episode(episode=0)
    assert dos_bot.target_ip_address == IPv4Address("192.168.0.1")
    assert dos_bot.target_port is Port.POSTGRES_SERVER
    assert dos_bot.payload is None
    assert dos_bot.repeat is False

    dos_bot.configure(
        target_ip_address=IPv4Address("192.168.1.1"), target_port=Port.HTTP, payload="payload", repeat=True
    )
    dos_bot.set_original_state()
    dos_bot.reset_component_for_episode(episode=1)
    # should reset to the configured value
    assert dos_bot.target_ip_address == IPv4Address("192.168.1.1")
    assert dos_bot.target_port is Port.HTTP
    assert dos_bot.payload == "payload"
    assert dos_bot.repeat is True


def test_dos_bot_cannot_run_when_node_offline(dos_bot):
    dos_bot_node: Computer = dos_bot.parent
    assert dos_bot_node.operating_state is NodeOperatingState.ON

    dos_bot_node.power_off()

    for i in range(dos_bot_node.shut_down_duration + 1):
        dos_bot_node.apply_timestep(timestep=i)

    assert dos_bot_node.operating_state is NodeOperatingState.OFF

    dos_bot._application_loop()

    # assert not run
    assert dos_bot.attack_stage is DoSAttackStage.NOT_STARTED


def test_dos_bot_not_configured(dos_bot):
    dos_bot.target_ip_address = None

    dos_bot.operating_state = ApplicationOperatingState.RUNNING
    dos_bot._application_loop()


def test_dos_bot_perform_port_scan(dos_bot):
    dos_bot._perform_port_scan(p_of_success=1)

    assert dos_bot.attack_stage is DoSAttackStage.PORT_SCAN
