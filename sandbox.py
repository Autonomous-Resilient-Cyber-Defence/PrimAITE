from primaite.config.load import example_config_path, load
from primaite.session.session import PrimaiteSession
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.dns.dns_client import DNSClient

cfg = load(example_config_path())
session = PrimaiteSession.from_config(cfg)
network = session.game.simulation.network

dc = network.get_node_by_hostname("domain_controller")
router = network.get_node_by_hostname("router_1")
client_1 = network.get_node_by_hostname("client_1")
client_2 = network.get_node_by_hostname("client_2")
switch_1 = network.get_node_by_hostname("switch_1")
switch_2 = network.get_node_by_hostname("switch_2")
web_server = network.get_node_by_hostname("web_server")

dns_server = dc.software_manager.software["DNSServer"]
dns_client: DNSClient = client_2.software_manager.software["DNSClient"]
web_db_client: DatabaseClient = web_server.software_manager.software["DatabaseClient"]
web_browser: WebBrowser = client_2.software_manager.software["WebBrowser"]

# print("before calling get webpage")
# router.acl.show()
# dns_server.show()
# client_2.arp.show()
# router.arp.show()
# print()

# print("can get webpage", client_2.software_manager.software["WebBrowser"].get_webpage())
# print("after calling get webpage")
# router.acl.show()
# dns_server.show()
# client_2.arp.show()
# router.arp.show()
# print()
# print("reset")
# print()
# print("im gonna reset")
# print()

# web_db_client.connect()
# web_db_client.run()
# web_browser.run()
# print("client_2", client_2.operating_state)
# print("web_browser", web_browser.operating_state)
# print("can get webpage", client_2.software_manager.software["WebBrowser"].get_webpage())
session.game.reset()
print("can get webpage", client_2.software_manager.software["WebBrowser"].get_webpage())
session.game.reset()
print("can get webpage", client_2.software_manager.software["WebBrowser"].get_webpage())
session.game.reset()
print("can get webpage", client_2.software_manager.software["WebBrowser"].get_webpage())
session.game.reset()
print("can get webpage", client_2.software_manager.software["WebBrowser"].get_webpage())
# print()
#
# print("before calling get webpage")
# router.acl.show()
# dns_server.show()
# client_2.arp.show()
# router.arp.show()
# print()
#
# print("can get webpage", client_2.software_manager.software["WebBrowser"].get_webpage())
# print("after calling get webpage")
# router.acl.show()
# dns_server.show()
# client_2.arp.show()
# router.arp.show()
# print()
