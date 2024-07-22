# class RouterICMP(ICMP):
#     """
#     A class to represent a router's Internet Control Message Protocol (ICMP) handler.
#
#     :param sys_log: System log for logging network events and errors.
#     :type sys_log: SysLog
#     :param arp_cache: The ARP cache for resolving MAC addresses.
#     :type arp_cache: ARPCache
#     :param router: The router to which this ICMP handler belongs.
#     :type router: Router
#     """
#
#     router: Router
#
#     def __init__(self, sys_log: SysLog, arp_cache: ARPCache, router: Router):
#         super().__init__(sys_log, arp_cache)
#         self.router = router
#
#     def process_icmp(self, frame: Frame, from_network_interface: NIC, is_reattempt: bool = False):
#         """
#         Process incoming ICMP frames based on ICMP type.
#
#         :param frame: The incoming frame to process.
#         :param from_network_interface: The network interface where the frame is coming from.
#         :param is_reattempt: Flag to indicate if the process is a reattempt.
#         """
#         if frame.icmp.icmp_type == ICMPType.ECHO_REQUEST:
#             # determine if request is for router interface or whether it needs to be routed
#
#             for network_interface in self.router.network_interfaces.values():
#                 if network_interface.ip_address == frame.ip.dst_ip_address:
#                     if network_interface.enabled:
#                         # reply to the request
#                         if not is_reattempt:
#                             self.sys_log.info(f"Received echo request from {frame.ip.src_ip_address}")
#                         target_mac_address = self.arp.get_arp_cache_mac_address(frame.ip.src_ip_address)
#                         src_nic = self.arp.get_arp_cache_network_interface(frame.ip.src_ip_address)
#                         tcp_header = TCPHeader(src_port=Port.ARP, dst_port=Port.ARP)
#
#                         # Network Layer
#                         ip_packet = IPPacket(
#                             src_ip_address=network_interface.ip_address,
#                             dst_ip_address=frame.ip.src_ip_address,
#                             protocol=IPProtocol.ICMP,
#                         )
#                         # Data Link Layer
#                         ethernet_header = EthernetHeader(
#                             src_mac_addr=src_nic.mac_address, dst_mac_addr=target_mac_address
#                         )
#                         icmp_reply_packet = ICMPPacket(
#                             icmp_type=ICMPType.ECHO_REPLY,
#                             icmp_code=0,
#                             identifier=frame.icmp.identifier,
#                             sequence=frame.icmp.sequence + 1,
#                         )
#                         payload = secrets.token_urlsafe(int(32 / 1.3))  # Standard ICMP 32 bytes size
#                         frame = Frame(
#                             ethernet=ethernet_header,
#                             ip=ip_packet,
#                             tcp=tcp_header,
#                             icmp=icmp_reply_packet,
#                             payload=payload,
#                         )
#                         self.sys_log.info(f"Sending echo reply to {frame.ip.dst_ip_address}")
#
#                         src_nic.send_frame(frame)
#                     return
#
#             # Route the frame
#             self.router.process_frame(frame, from_network_interface)
#
#         elif frame.icmp.icmp_type == ICMPType.ECHO_REPLY:
#             for network_interface in self.router.network_interfaces.values():
#                 if network_interface.ip_address == frame.ip.dst_ip_address:
#                     if network_interface.enabled:
#                         time = frame.transmission_duration()
#                         time_str = f"{time}ms" if time > 0 else "<1ms"
#                         self.sys_log.info(
#                             f"Reply from {frame.ip.src_ip_address}: "
#                             f"bytes={len(frame.payload)}, "
#                             f"time={time_str}, "
#                             f"TTL={frame.ip.ttl}"
#                         )
#                         if not self.request_replies.get(frame.icmp.identifier):
#                             self.request_replies[frame.icmp.identifier] = 0
#                         self.request_replies[frame.icmp.identifier] += 1
#
#                     return
#             # Route the frame
#             self.router.process_frame(frame, from_network_interface)
