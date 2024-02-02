# class RouterARPCache(ARPCache):
#     """
#     Inherits from ARPCache and adds router-specific ARP packet processing.
#
#     :ivar SysLog sys_log: A system log for logging messages.
#     :ivar Router router: The router to which this ARP cache belongs.
#     """
#
#     def __init__(self, sys_log: SysLog, router: Router):
#         super().__init__(sys_log)
#         self.router: Router = router
#
#     def process_arp_packet(
#         self, from_nic: NIC, frame: Frame, route_table: RouteTable, is_reattempt: bool = False
#     ) -> None:
#         """
#         Processes a received ARP (Address Resolution Protocol) packet in a router-specific way.
#
#         This method is responsible for handling both ARP requests and responses. It processes ARP packets received on a
#         Network Interface Card (NIC) and performs actions based on whether the packet is a request or a reply. This
#         includes updating the ARP cache, forwarding ARP replies, sending ARP requests for unknown destinations, and
#         handling packet TTL (Time To Live).
#
#         The method first checks if the ARP packet is a request or a reply. For ARP replies, it updates the ARP cache
#         and forwards the reply if necessary. For ARP requests, it checks if the target IP matches one of the router's
#         NICs and sends an ARP reply if so. If the destination is not directly connected, it consults the routing table
#         to find the best route and reattempts ARP request processing if needed.
#
#         :param from_nic: The NIC that received the ARP packet.
#         :param frame: The frame containing the ARP packet.
#         :param route_table: The routing table of the router.
#         :param is_reattempt: Flag to indicate if this is a reattempt of processing the ARP packet, defaults to False.
#         """
#         arp_packet = frame.arp
#
#         # ARP Reply
#         if not arp_packet.request:
#             if arp_packet.target_ip_address == from_nic.ip_address:
#                 # reply to the Router specifically
#                 self.sys_log.info(
#                     f"Received ARP response for {arp_packet.sender_ip_address} "
#                     f"from {arp_packet.sender_mac_addr} via NIC {from_nic}"
#                 )
#                 self.add_arp_cache_entry(
#                     ip_address=arp_packet.sender_ip_address,
#                     mac_address=arp_packet.sender_mac_addr,
#                     nic=from_nic,
#                 )
#                 return
#
#             # # Reply for a connected requested
#             # nic = self.get_arp_cache_nic(arp_packet.target_ip_address)
#             # if nic:
#             #     self.sys_log.info(
#             #         f"Forwarding arp reply for {arp_packet.target_ip_address}, from {arp_packet.sender_ip_address}"
#             #     )
#             #     arp_packet.sender_mac_addr = nic.mac_address
#             #     frame.decrement_ttl()
#             #     if frame.ip and frame.ip.ttl < 1:
#             #         self.sys_log.info("Frame discarded as TTL limit reached")
#             #         return
#             #     nic.send_frame(frame)
#             # return
#
#         # ARP Request
#         self.sys_log.info(
#             f"Received ARP request for {arp_packet.target_ip_address} from "
#             f"{arp_packet.sender_mac_addr}/{arp_packet.sender_ip_address} "
#         )
#         # Matched ARP request
#         self.add_arp_cache_entry(
#             ip_address=arp_packet.sender_ip_address, mac_address=arp_packet.sender_mac_addr, nic=from_nic
#         )
#
#         # If the target IP matches one of the router's NICs
#         for nic in self.nics.values():
#             if nic.enabled and nic.ip_address == arp_packet.target_ip_address:
#                 arp_reply = arp_packet.generate_reply(from_nic.mac_address)
#                 self.send_arp_reply(arp_reply, from_nic)
#                 return
#
#         # # Check Route Table
#         # route = route_table.find_best_route(arp_packet.target_ip_address)
#         # if route and route != self.router.route_table.default_route:
#         #     nic = self.get_arp_cache_nic(route.next_hop_ip_address)
#         #
#         #     if not nic:
#         #         if not is_reattempt:
#         #             self.send_arp_request(route.next_hop_ip_address, ignore_networks=[frame.ip.src_ip_address])
#         #             return self.process_arp_packet(from_nic, frame, route_table, is_reattempt=True)
#         #         else:
#         #             self.sys_log.info("Ignoring ARP request as destination unavailable/No ARP entry found")
#         #             return
#         #     else:
#         #         arp_reply = arp_packet.generate_reply(from_nic.mac_address)
#         #         self.send_arp_reply(arp_reply, from_nic)
#         #     return
#
