from primaite.game.agent.observations import NicObservation
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.nmne import set_nmne_config
from primaite.simulator.sim_container import Simulation
from primaite.simulator.system.applications.database_client import DatabaseClient


def test_capture_nmne(uc2_network):
    """
    Conducts a test to verify that Malicious Network Events (MNEs) are correctly captured.

    This test involves a web server querying a database server and checks if the MNEs are captured
    based on predefined keywords in the network configuration. Specifically, it checks the capture
    of the "DELETE" SQL command as a malicious network event.
    """
    web_server: Server = uc2_network.get_node_by_hostname("web_server")  # noqa
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]  # noqa
    db_client.connect()

    db_server: Server = uc2_network.get_node_by_hostname("database_server")  # noqa

    web_server_nic = web_server.network_interface[1]
    db_server_nic = db_server.network_interface[1]

    # Set the NMNE configuration to capture DELETE queries as MNEs
    nmne_config = {
        "capture_nmne": True,  # Enable the capture of MNEs
        "nmne_capture_keywords": ["DELETE"],  # Specify "DELETE" SQL command as a keyword for MNE detection
    }

    # Apply the NMNE configuration settings
    set_nmne_config(nmne_config)

    # Assert that initially, there are no captured MNEs on both web and database servers
    assert web_server_nic.nmne == {}
    assert db_server_nic.nmne == {}

    # Perform a "SELECT" query
    db_client.query("SELECT")

    # Check that it does not trigger an MNE capture.
    assert web_server_nic.nmne == {}
    assert db_server_nic.nmne == {}

    # Perform a "DELETE" query
    db_client.query("DELETE")

    # Check that the web server's outbound interface and the database server's inbound interface register the MNE
    assert web_server_nic.nmne == {"direction": {"outbound": {"keywords": {"*": 1}}}}
    assert db_server_nic.nmne == {"direction": {"inbound": {"keywords": {"*": 1}}}}

    # Perform another "SELECT" query
    db_client.query("SELECT")

    # Check that no additional MNEs are captured
    assert web_server_nic.nmne == {"direction": {"outbound": {"keywords": {"*": 1}}}}
    assert db_server_nic.nmne == {"direction": {"inbound": {"keywords": {"*": 1}}}}

    # Perform another "DELETE" query
    db_client.query("DELETE")

    # Check that the web server and database server interfaces register an additional MNE
    assert web_server_nic.nmne == {"direction": {"outbound": {"keywords": {"*": 2}}}}
    assert db_server_nic.nmne == {"direction": {"inbound": {"keywords": {"*": 2}}}}


def test_describe_state_nmne(uc2_network):
    """
    Conducts a test to verify that Malicious Network Events (MNEs) are correctly represented in the nic state.

    This test involves a web server querying a database server and checks if the MNEs are captured
    based on predefined keywords in the network configuration. Specifically, it checks the capture
    of the "DELETE" SQL command as a malicious network event. It also checks that running describe_state
    only shows MNEs since the last time describe_state was called.
    """
    web_server: Server = uc2_network.get_node_by_hostname("web_server")  # noqa
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]  # noqa
    db_client.connect()

    db_server: Server = uc2_network.get_node_by_hostname("database_server")  # noqa

    web_server_nic = web_server.network_interface[1]
    db_server_nic = db_server.network_interface[1]

    # Set the NMNE configuration to capture DELETE queries as MNEs
    nmne_config = {
        "capture_nmne": True,  # Enable the capture of MNEs
        "nmne_capture_keywords": ["DELETE"],  # Specify "DELETE" SQL command as a keyword for MNE detection
    }

    # Apply the NMNE configuration settings
    set_nmne_config(nmne_config)

    # Assert that initially, there are no captured MNEs on both web and database servers
    web_server_nic_state = web_server_nic.describe_state()
    db_server_nic_state = db_server_nic.describe_state()
    uc2_network.apply_timestep(timestep=0)
    assert web_server_nic_state["nmne"] == {}
    assert db_server_nic_state["nmne"] == {}

    # Perform a "SELECT" query
    db_client.query("SELECT")

    # Check that it does not trigger an MNE capture.
    web_server_nic_state = web_server_nic.describe_state()
    db_server_nic_state = db_server_nic.describe_state()
    uc2_network.apply_timestep(timestep=0)
    assert web_server_nic_state["nmne"] == {}
    assert db_server_nic_state["nmne"] == {}

    # Perform a "DELETE" query
    db_client.query("DELETE")

    # Check that the web server's outbound interface and the database server's inbound interface register the MNE
    web_server_nic_state = web_server_nic.describe_state()
    db_server_nic_state = db_server_nic.describe_state()
    uc2_network.apply_timestep(timestep=0)
    assert web_server_nic_state["nmne"] == {"direction": {"outbound": {"keywords": {"*": 1}}}}
    assert db_server_nic_state["nmne"] == {"direction": {"inbound": {"keywords": {"*": 1}}}}

    # Perform another "SELECT" query
    db_client.query("SELECT")

    # Check that no additional MNEs are captured
    web_server_nic_state = web_server_nic.describe_state()
    db_server_nic_state = db_server_nic.describe_state()
    uc2_network.apply_timestep(timestep=0)
    assert web_server_nic_state["nmne"] == {}
    assert db_server_nic_state["nmne"] == {}

    # Perform another "DELETE" query
    db_client.query("DELETE")

    # Check that the web server and database server interfaces register an additional MNE
    web_server_nic_state = web_server_nic.describe_state()
    db_server_nic_state = db_server_nic.describe_state()
    uc2_network.apply_timestep(timestep=0)
    assert web_server_nic_state["nmne"] == {"direction": {"outbound": {"keywords": {"*": 1}}}}
    assert db_server_nic_state["nmne"] == {"direction": {"inbound": {"keywords": {"*": 1}}}}


def test_capture_nmne_observations(uc2_network):
    """
    Tests the NicObservation class's functionality within a simulated network environment.

    This test ensures the observation space, as defined by instances of NicObservation, accurately reflects the
    number of MNEs detected based on network activities over multiple iterations.

    The test employs a series of "DELETE" SQL operations, considered as MNEs, to validate the dynamic update
    and accuracy of the observation space related to network interface conditions. It confirms that the
    observed NIC states match expected MNE activity levels.
    """
    # Initialise a new Simulation instance and assign the test network to it.
    sim = Simulation()
    sim.network = uc2_network

    web_server: Server = uc2_network.get_node_by_hostname("web_server")
    db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]
    db_client.connect()

    # Set the NMNE configuration to capture DELETE queries as MNEs
    nmne_config = {
        "capture_nmne": True,  # Enable the capture of MNEs
        "nmne_capture_keywords": ["DELETE"],  # Specify "DELETE" SQL command as a keyword for MNE detection
    }

    # Apply the NMNE configuration settings
    set_nmne_config(nmne_config)

    # Define observations for the NICs  of the database and web servers
    db_server_nic_obs = NicObservation(where=["network", "nodes", "database_server", "NICs", 1])
    web_server_nic_obs = NicObservation(where=["network", "nodes", "web_server", "NICs", 1])

    # Iterate through a set of test cases to simulate multiple DELETE queries
    for i in range(0, 20):
        # Perform a "DELETE" query each iteration
        for j in range(i):
            db_client.query("DELETE")

        # Observe the current state of NMNEs from the NICs of both the database and web servers
        state = sim.describe_state()
        db_nic_obs = db_server_nic_obs.observe(state)["nmne"]
        web_nic_obs = web_server_nic_obs.observe(state)["nmne"]

        # Define expected NMNE values based on the iteration count
        if i > 10:
            expected_nmne = 3  # High level of detected MNEs after 10 iterations
        elif i > 5:
            expected_nmne = 2  # Moderate level after more than 5 iterations
        elif i > 0:
            expected_nmne = 1  # Low level detected after just starting
        else:
            expected_nmne = 0  # No MNEs detected

        # Assert that the observed NMNEs match the expected values for both NICs
        assert web_nic_obs["outbound"] == expected_nmne
        assert db_nic_obs["inbound"] == expected_nmne
        uc2_network.apply_timestep(timestep=0)
