# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
def test_switched_network(client_switch_server):
    """Tests a node can ping another node via the switch."""
    computer, switch, server = client_switch_server

    assert computer.ping(server.network_interface[1].ip_address)
