# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address

import yaml

from primaite import getLogger, PRIMAITE_PATHS
from primaite.game.game import PrimaiteGame
from primaite.simulator import LogLevel, SIM_OUTPUT
from primaite.simulator.network.container import Network
from primaite.simulator.network.hardware.nodes.host.computer import Computer
from primaite.simulator.network.hardware.nodes.host.host_node import NIC
from primaite.simulator.network.hardware.nodes.host.server import Server
from primaite.simulator.network.hardware.nodes.network.router import ACLAction, Router
from primaite.simulator.network.hardware.nodes.network.switch import Switch
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.red_applications.data_manipulation_bot import DataManipulationBot
from primaite.simulator.system.services.database.database_service import DatabaseService
from primaite.simulator.system.services.dns.dns_server import DNSServer
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.web_server.web_server import WebServer
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP

_LOGGER = getLogger(__name__)


def client_server_routed() -> Network:
    """
    A basic Client/Server Network routed between subnets.

    +------------+      +------------+      +------------+      +------------+      +------------+
    |            |      |            |      |            |      |            |      |            |
    |  client_1  +------+  switch_2  +------+  router_1  +------+  switch_1  +------+  server_1  |
    |            |      |            |      |            |      |            |      |            |
    +------------+      +------------+      +------------+      +------------+      +------------+

    IP Table:

    """
    network = Network()

    # Router 1
    router_1 = Router(hostname="router_1", num_ports=3)
    router_1.power_on()
    router_1.configure_port(port=1, ip_address="192.168.1.1", subnet_mask="255.255.255.0")
    router_1.configure_port(port=2, ip_address="192.168.2.1", subnet_mask="255.255.255.0")

    # Switch 1
    switch_1 = Switch(hostname="switch_1", num_ports=6)
    switch_1.power_on()
    network.connect(endpoint_a=router_1.network_interface[1], endpoint_b=switch_1.network_interface[6])
    router_1.enable_port(1)

    # Switch 2
    switch_2 = Switch(hostname="switch_2", num_ports=6)
    switch_2.power_on()
    network.connect(endpoint_a=router_1.network_interface[2], endpoint_b=switch_2.network_interface[6])
    router_1.enable_port(2)

    # Client 1
    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.2.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.2.1",
        start_up_duration=0,
    )
    client_1.power_on()
    network.connect(endpoint_b=client_1.network_interface[1], endpoint_a=switch_2.network_interface[1])

    # Server 1
    server_1 = Server(
        hostname="server_1",
        ip_address="192.168.1.2",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    server_1.power_on()
    network.connect(endpoint_b=server_1.network_interface[1], endpoint_a=switch_1.network_interface[1])

    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )

    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)

    return network


def arcd_uc2_network() -> Network:
    """
    Models the ARCD Use Case 2 Network.

                                                                                    +------------+
                                                                                    |  domain_   |
                                                                       +------------+ controller |
                                                                       |            |            |
                                                                       |            +------------+
                                                                       |
                                                                       |
    +------------+                                                     |            +------------+
    |            |                                                     |            |            |
    |  client_1  +---------+                                           |  +---------+ web_server |
    |            |         |                                           |  |         |            |
    +------------+         |                                           |  |         +------------+
                        +--+---------+      +------------+      +------+--+--+
                        |            |      |            |      |            |
                        |  switch_2  +------+  router_1  +------+  switch_1  |
                        |            |      |            |      |            |
                        +--+------+--+      +------------+      +--+---+--+--+
    +------------+         |      |                                |   |  |         +------------+
    |            |         |      |                                |   |  |         |  database  |
    |  client_2  +---------+      |                                |   |  +---------+  _server   |
    |            |                |                                |   |            |            |
    +------------+                |                                |   |            +------------+
                                  |         +------------+         |   |
                                  |         |  security  |         |   |
                                  +---------+   _suite   +---------+   |            +------------+
                                            |            |             |            |  backup_   |
                                            +------------+             +------------+  server    |
                                                                                    |            |
                                                                                    +------------+



    """
    network = Network()

    # Router 1
    router_1 = Router(hostname="router_1", num_ports=5, start_up_duration=0)
    router_1.power_on()
    router_1.configure_port(port=1, ip_address="192.168.1.1", subnet_mask="255.255.255.0")
    router_1.configure_port(port=2, ip_address="192.168.10.1", subnet_mask="255.255.255.0")

    # Switch 1
    switch_1 = Switch(hostname="switch_1", num_ports=8, start_up_duration=0)
    switch_1.power_on()
    network.connect(endpoint_a=router_1.network_interface[1], endpoint_b=switch_1.network_interface[8])
    router_1.enable_port(1)

    # Switch 2
    switch_2 = Switch(hostname="switch_2", num_ports=8, start_up_duration=0)
    switch_2.power_on()
    network.connect(endpoint_a=router_1.network_interface[2], endpoint_b=switch_2.network_interface[8])
    router_1.enable_port(2)

    # Client 1
    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.10.21",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        dns_server=IPv4Address("192.168.1.10"),
        start_up_duration=0,
    )
    client_1.power_on()
    network.connect(endpoint_b=client_1.network_interface[1], endpoint_a=switch_2.network_interface[1])
    client_1.software_manager.install(DatabaseClient)
    db_client_1: DatabaseClient = client_1.software_manager.software.get("DatabaseClient")
    db_client_1.configure(server_ip_address=IPv4Address("192.168.1.14"))
    db_client_1.run()
    web_browser_1 = client_1.software_manager.software.get("WebBrowser")
    web_browser_1.target_url = "http://arcd.com/users/"
    client_1.software_manager.install(DataManipulationBot)
    db_manipulation_bot: DataManipulationBot = client_1.software_manager.software.get("DataManipulationBot")
    db_manipulation_bot.configure(
        server_ip_address=IPv4Address("192.168.1.14"),
        payload="DELETE",
        port_scan_p_of_success=1.0,
        data_manipulation_p_of_success=1.0,
    )

    # Client 2
    client_2 = Computer(
        hostname="client_2",
        ip_address="192.168.10.22",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        dns_server=IPv4Address("192.168.1.10"),
        start_up_duration=0,
    )
    client_2.power_on()
    client_2.software_manager.install(DatabaseClient)
    db_client_2 = client_2.software_manager.software.get("DatabaseClient")
    db_client_2.configure(server_ip_address=IPv4Address("192.168.1.14"))
    db_client_2.run()
    web_browser_2 = client_2.software_manager.software.get("WebBrowser")
    web_browser_2.target_url = "http://arcd.com/users/"
    network.connect(
        endpoint_b=client_2.network_interface[1],
        endpoint_a=switch_2.network_interface[2],
    )

    # Domain Controller
    domain_controller = Server(
        hostname="domain_controller",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        start_up_duration=0,
    )
    domain_controller.power_on()
    domain_controller.software_manager.install(DNSServer)

    network.connect(endpoint_b=domain_controller.network_interface[1], endpoint_a=switch_1.network_interface[1])

    # Database Server
    database_server = Server(
        hostname="database_server",
        ip_address="192.168.1.14",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
        start_up_duration=0,
    )
    database_server.power_on()
    network.connect(endpoint_b=database_server.network_interface[1], endpoint_a=switch_1.network_interface[3])

    database_server.software_manager.install(DatabaseService)
    database_service: DatabaseService = database_server.software_manager.software.get("DatabaseService")  # noqa
    database_service.start()
    database_service.configure_backup(backup_server=IPv4Address("192.168.1.16"))

    # Web Server
    web_server = Server(
        hostname="web_server",
        ip_address="192.168.1.12",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
        start_up_duration=0,
    )
    web_server.power_on()
    web_server.software_manager.install(DatabaseClient)

    database_client: DatabaseClient = web_server.software_manager.software.get("DatabaseClient")
    database_client.configure(server_ip_address=IPv4Address("192.168.1.14"))
    network.connect(endpoint_b=web_server.network_interface[1], endpoint_a=switch_1.network_interface[2])
    database_client.run()
    database_client.connect()

    web_server.software_manager.install(WebServer)

    # register the web_server to a domain
    dns_server_service: DNSServer = domain_controller.software_manager.software.get("DNSServer")  # noqa
    dns_server_service.dns_register("arcd.com", web_server.network_interface[1].ip_address)

    # Backup Server
    backup_server = Server(
        hostname="backup_server",
        ip_address="192.168.1.16",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
        start_up_duration=0,
    )
    backup_server.power_on()
    backup_server.software_manager.install(FTPServer)
    network.connect(endpoint_b=backup_server.network_interface[1], endpoint_a=switch_1.network_interface[4])

    # Security Suite
    security_suite = Server(
        hostname="security_suite",
        ip_address="192.168.1.110",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
        start_up_duration=0,
    )
    security_suite.power_on()
    network.connect(endpoint_b=security_suite.network_interface[1], endpoint_a=switch_1.network_interface[7])
    security_suite.connect_nic(NIC(ip_address="192.168.10.110", subnet_mask="255.255.255.0"))
    network.connect(endpoint_b=security_suite.network_interface[2], endpoint_a=switch_2.network_interface[7])

    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["ARP"], dst_port=PORT_LOOKUP["ARP"], position=22
    )

    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=PROTOCOL_LOOKUP["ICMP"], position=23)

    # Allow PostgreSQL requests
    router_1.acl.add_rule(
        action=ACLAction.PERMIT,
        src_port=PORT_LOOKUP["POSTGRES_SERVER"],
        dst_port=PORT_LOOKUP["POSTGRES_SERVER"],
        position=0,
    )

    # Allow DNS requests
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["DNS"], dst_port=PORT_LOOKUP["DNS"], position=1)

    # Allow FTP requests
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=PORT_LOOKUP["FTP"], dst_port=PORT_LOOKUP["FTP"], position=2)

    # Open port 80 for web server
    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=PORT_LOOKUP["HTTP"], dst_port=PORT_LOOKUP["HTTP"], position=3
    )

    return network


def network_simulator_demo_example() -> Network:
    """Returns a lightly modified version of the ARCD UC2 Network."""
    # Ensure that sys_log will be viewable for demo
    SIM_OUTPUT.sys_log_level = LogLevel.DEBUG
    SIM_OUTPUT.save_sys_logs = True

    network = arcd_uc2_network()
    network.get_node_by_hostname("router_1").route_table.add_route(
        address="192.168.10.0", subnet_mask="255.255.255.0", next_hop_ip_address="192.168.1.2"
    )

    return network


def _get_example_network(path: str) -> Network:
    try:
        with open(path, "r") as file:
            cfg = yaml.safe_load(file)
    except FileNotFoundError:
        msg = f"Failed to locate example network config {path}. Run `primaite setup` to load the example config files."
        _LOGGER.error(msg)
        raise FileNotFoundError(msg)
    game = PrimaiteGame.from_config(cfg)

    return game.simulation.network


def client_server_p2p_network_example() -> Network:
    """Get the Client-Server P2P example network."""
    path = PRIMAITE_PATHS.user_config_path / "example_config" / "client_server_p2p_network_example.yaml"
    return _get_example_network(path)


def basic_lan_network_example() -> Network:
    """Get the basic LAN example network."""
    path = PRIMAITE_PATHS.user_config_path / "example_config" / "basic_lan_network_example.yaml"
    return _get_example_network(path)


def multi_lan_internet_network_example() -> Network:
    """Get Multi-LAN with Internet example network."""
    path = PRIMAITE_PATHS.user_config_path / "example_config" / "multi_lan_internet_network_example.yaml"
    return _get_example_network(path)
