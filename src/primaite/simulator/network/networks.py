from ipaddress import IPv4Address

from src.primaite.simulator.network.container import Network
from src.primaite.simulator.network.hardware.base import NIC, NodeOperatingState
from src.primaite.simulator.network.hardware.nodes.computer import Computer
from src.primaite.simulator.network.hardware.nodes.router import ACLAction, Router
from src.primaite.simulator.network.hardware.nodes.server import Server
from src.primaite.simulator.network.hardware.nodes.switch import Switch
from src.primaite.simulator.network.transmission.network_layer import IPProtocol
from src.primaite.simulator.network.transmission.transport_layer import Port
from src.primaite.simulator.system.applications.database_client import DatabaseClient
from src.primaite.simulator.system.services.database.database_service import DatabaseService
from src.primaite.simulator.system.services.dns.dns_server import DNSServer
from src.primaite.simulator.system.services.ftp.ftp_server import FTPServer
from src.primaite.simulator.system.services.red_services.data_manipulation_bot import DataManipulationBot
from src.primaite.simulator.system.services.web_server.web_server import WebServer


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
    network.connect(endpoint_a=router_1.ethernet_ports[1], endpoint_b=switch_1.switch_ports[6])
    router_1.enable_port(1)

    # Switch 2
    switch_2 = Switch(hostname="switch_2", num_ports=6)
    switch_2.power_on()
    network.connect(endpoint_a=router_1.ethernet_ports[2], endpoint_b=switch_2.switch_ports[6])
    router_1.enable_port(2)

    # Client 1
    client_1 = Computer(
        hostname="client_1", ip_address="192.168.2.2", subnet_mask="255.255.255.0", default_gateway="192.168.2.1"
    )
    client_1.power_on()
    network.connect(endpoint_b=client_1.ethernet_port[1], endpoint_a=switch_2.switch_ports[1])

    # Server 1
    server_1 = Server(
        hostname="server_1", ip_address="192.168.1.2", subnet_mask="255.255.255.0", default_gateway="192.168.1.1"
    )
    server_1.power_on()
    network.connect(endpoint_b=server_1.ethernet_port[1], endpoint_a=switch_1.switch_ports[1])

    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)

    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)

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
    router_1 = Router(hostname="router_1", num_ports=5, operating_state=NodeOperatingState.ON)
    router_1.power_on()
    router_1.configure_port(port=1, ip_address="192.168.1.1", subnet_mask="255.255.255.0")
    router_1.configure_port(port=2, ip_address="192.168.10.1", subnet_mask="255.255.255.0")

    # Switch 1
    switch_1 = Switch(hostname="switch_1", num_ports=8, operating_state=NodeOperatingState.ON)
    switch_1.power_on()
    network.connect(endpoint_a=router_1.ethernet_ports[1], endpoint_b=switch_1.switch_ports[8])
    router_1.enable_port(1)

    # Switch 2
    switch_2 = Switch(hostname="switch_2", num_ports=8, operating_state=NodeOperatingState.ON)
    switch_2.power_on()
    network.connect(endpoint_a=router_1.ethernet_ports[2], endpoint_b=switch_2.switch_ports[8])
    router_1.enable_port(2)

    # Client 1
    client_1 = Computer(
        hostname="client_1",
        ip_address="192.168.10.21",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        dns_server=IPv4Address("192.168.1.10"),
        operating_state=NodeOperatingState.ON,
    )
    client_1.power_on()
    network.connect(endpoint_b=client_1.ethernet_port[1], endpoint_a=switch_2.switch_ports[1])
    client_1.software_manager.install(DataManipulationBot)
    db_manipulation_bot: DataManipulationBot = client_1.software_manager.software["DataManipulationBot"]
    db_manipulation_bot.configure(server_ip_address=IPv4Address("192.168.1.14"), payload="DROP TABLE IF EXISTS user;")

    # Client 2
    client_2 = Computer(
        hostname="client_2",
        ip_address="192.168.10.22",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.10.1",
        dns_server=IPv4Address("192.168.1.10"),
        operating_state=NodeOperatingState.ON,
    )
    client_2.power_on()
    network.connect(endpoint_b=client_2.ethernet_port[1], endpoint_a=switch_2.switch_ports[2])

    # Domain Controller
    domain_controller = Server(
        hostname="domain_controller",
        ip_address="192.168.1.10",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        operating_state=NodeOperatingState.ON,
    )
    domain_controller.power_on()
    domain_controller.software_manager.install(DNSServer)

    network.connect(endpoint_b=domain_controller.ethernet_port[1], endpoint_a=switch_1.switch_ports[1])

    # Database Server
    database_server = Server(
        hostname="database_server",
        ip_address="192.168.1.14",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
        operating_state=NodeOperatingState.ON,
    )
    database_server.power_on()
    network.connect(endpoint_b=database_server.ethernet_port[1], endpoint_a=switch_1.switch_ports[3])

    ddl = """
    CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    age INT,
    city VARCHAR(50),
    occupation VARCHAR(50)
    );"""

    user_insert_statements = [
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('John Doe', 'johndoe@example.com', 32, 'New York', 'Engineer');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Jane Smith', 'janesmith@example.com', 27, 'Los Angeles', 'Designer');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Bob Johnson', 'bobjohnson@example.com', 45, 'Chicago', 'Manager');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Alice Lee', 'alicelee@example.com', 22, 'San Francisco', 'Student');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('David Kim', 'davidkim@example.com', 38, 'Houston', 'Consultant');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Emily Chen', 'emilychen@example.com', 29, 'Seattle', 'Software Developer');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Frank Wang', 'frankwang@example.com', 55, 'New York', 'Entrepreneur');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Grace Park', 'gracepark@example.com', 31, 'Los Angeles', 'Marketing Specialist');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Henry Wu', 'henrywu@example.com', 40, 'Chicago', 'Accountant');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Isabella Kim', 'isabellakim@example.com', 26, 'San Francisco', 'Graphic Designer');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Jake Lee', 'jakelee@example.com', 33, 'Houston', 'Sales Manager');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Kelly Chen', 'kellychen@example.com', 28, 'Seattle', 'Web Developer');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Lucas Liu', 'lucasliu@example.com', 42, 'New York', 'Lawyer');",
        # noqa
        "INSERT INTO user (name, email, age, city, occupation) "
        "VALUES ('Maggie Wang', 'maggiewang@example.com', 30, 'Los Angeles', 'Data Analyst');",
        # noqa
    ]
    database_server.software_manager.install(DatabaseService)
    database_service: DatabaseService = database_server.software_manager.software["DatabaseService"]  # noqa
    database_service.start()
    database_service.configure_backup(backup_server=IPv4Address("192.168.1.16"))
    database_service._process_sql(ddl, None)  # noqa
    for insert_statement in user_insert_statements:
        database_service._process_sql(insert_statement, None)  # noqa

    # Web Server
    web_server = Server(
        hostname="web_server",
        ip_address="192.168.1.12",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
        operating_state=NodeOperatingState.ON,
    )
    web_server.power_on()
    web_server.software_manager.install(DatabaseClient)

    database_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]
    database_client.configure(server_ip_address=IPv4Address("192.168.1.14"))
    network.connect(endpoint_b=web_server.ethernet_port[1], endpoint_a=switch_1.switch_ports[2])
    database_client.run()
    database_client.connect()

    web_server.software_manager.install(WebServer)

    # register the web_server to a domain
    dns_server_service: DNSServer = domain_controller.software_manager.software["DNSServer"]  # noqa
    dns_server_service.dns_register("arcd.com", web_server.ip_address)

    # Backup Server
    backup_server = Server(
        hostname="backup_server",
        ip_address="192.168.1.16",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
        operating_state=NodeOperatingState.ON,
    )
    backup_server.power_on()
    backup_server.software_manager.install(FTPServer)
    network.connect(endpoint_b=backup_server.ethernet_port[1], endpoint_a=switch_1.switch_ports[4])

    # Security Suite
    security_suite = Server(
        hostname="security_suite",
        ip_address="192.168.1.110",
        subnet_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns_server=IPv4Address("192.168.1.10"),
        operating_state=NodeOperatingState.ON,
    )
    security_suite.power_on()
    network.connect(endpoint_b=security_suite.ethernet_port[1], endpoint_a=switch_1.switch_ports[7])
    security_suite.connect_nic(NIC(ip_address="192.168.10.110", subnet_mask="255.255.255.0"))
    network.connect(endpoint_b=security_suite.ethernet_port[2], endpoint_a=switch_2.switch_ports[7])

    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.ARP, dst_port=Port.ARP, position=22)

    router_1.acl.add_rule(action=ACLAction.PERMIT, protocol=IPProtocol.ICMP, position=23)

    # Allow PostgreSQL requests
    router_1.acl.add_rule(
        action=ACLAction.PERMIT, src_port=Port.POSTGRES_SERVER, dst_port=Port.POSTGRES_SERVER, position=0
    )

    # Allow DNS requests
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.DNS, dst_port=Port.DNS, position=1)

    # Allow FTP requests
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.FTP, dst_port=Port.FTP, position=2)

    # Open port 80 for web server
    router_1.acl.add_rule(action=ACLAction.PERMIT, src_port=Port.HTTP, dst_port=Port.HTTP, position=3)

    return network
