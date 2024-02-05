# from ipaddress import IPv4Address
# from typing import Optional, Any
#
# from primaite.simulator.network.hardware.nodes.network.router import RouterInterface, Router
# from primaite.simulator.network.protocols.arp import ARPPacket
# from primaite.simulator.network.transmission.data_link_layer import Frame
# from primaite.simulator.system.services.arp.arp import ARP
#
#
# class RouterARP(ARP):
#     """
#     Inherits from ARPCache and adds router-specific ARP packet processing.
#
#     :ivar SysLog sys_log: A system log for logging messages.
#     :ivar Router router: The router to which this ARP cache belongs.
#     """
#     router: Router
#
#     def get_arp_cache_mac_address(self, ip_address: IPv4Address) -> Optional[str]:
#         arp_entry = self.arp.get(ip_address)
#
#         if arp_entry:
#             return arp_entry.mac_address
#         return None
#
#     def get_arp_cache_network_interface(self, ip_address: IPv4Address) -> Optional[RouterInterface]:
#         arp_entry = self.arp.get(ip_address)
#         if arp_entry:
#             return self.software_manager.node.network_interfaces[arp_entry.network_interface_uuid]
#         return None
#
#     def _process_arp_request(self, arp_packet: ARPPacket, from_network_interface: RouterInterface):
#         super()._process_arp_request(arp_packet, from_network_interface)
#         self.add_arp_cache_entry(
#             ip_address=arp_packet.sender_ip_address, mac_address=arp_packet.sender_mac_addr,
#             network_interface=from_network_interface
#         )
#
#         # If the target IP matches one of the router's NICs
#         for network_interface in self.network_interfaces.values():
#             if network_interface.enabled and network_interface.ip_address == arp_packet.target_ip_address:
#                 arp_reply = arp_packet.generate_reply(from_network_interface.mac_address)
#                 self.send_arp_reply(arp_reply)
#                 return
#
#     def _process_arp_reply(self, arp_packet: ARPPacket, from_network_interface: RouterInterface):
#         if arp_packet.target_ip_address == from_network_interface.ip_address:
#             super()._process_arp_reply(arp_packet, from_network_interface)
#
#     def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
#         """
#         Processes received data, handling ARP packets.
#
#         :param payload: The payload received.
#         :param session_id: The session ID associated with the received data.
#         :param kwargs: Additional keyword arguments.
#         :return: True if the payload was processed successfully, otherwise False.
#         """
#         if not super().receive(payload, session_id, **kwargs):
#             return False
#
#         arp_packet: ARPPacket = payload
#         from_network_interface: RouterInterface = kwargs["from_network_interface"]
#
#         for network_interface in self.network_interfaces.values():
#             # ARP frame is for this Router
#             if network_interface.ip_address == arp_packet.target_ip_address:
#                 if payload.request:
#                     self._process_arp_request(arp_packet=arp_packet, from_network_interface=from_network_interface)
#                 else:
#                     self._process_arp_reply(arp_packet=arp_packet, from_network_interface=from_network_interface)
#                 return True
#
#         # ARP frame is not for this router, pass back down to Router to continue routing
#         frame: Frame = kwargs["frame"]
#         self.router.process_frame(frame=frame, from_network_interface=from_network_interface)
#
#         return True
