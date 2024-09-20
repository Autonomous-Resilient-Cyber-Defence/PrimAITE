# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from enum import Enum
from typing import List

from pydantic import BaseModel

PORT_LOOKUP: dict[str, int] = dict(
    UNUSED=-1,
    NONE=0,
    WOL=9,
    FTP_DATA=20,
    FTP=21,
    SSH=22,
    SMTP=25,
    DNS=53,
    HTTP=80,
    POP3=110,
    SFTP=115,
    NTP=123,
    IMAP=143,
    SNMP=161,
    SNMP_TRAP=162,
    ARP=219,
    LDAP=389,
    HTTPS=443,
    SMB=445,
    IPP=631,
    SQL_SERVER=1433,
    MYSQL=3306,
    RDP=3389,
    RTP=5004,
    RTP_ALT=5005,
    DNS_ALT=5353,
    HTTP_ALT=8080,
    HTTPS_ALT=8443,
    POSTGRES_SERVER=5432,
)


class UDPHeader(BaseModel):
    """
    Represents a UDP header for the transport layer of a Network Frame.

    :param src_port: Source port.
    :param dst_port: Destination port.

    :Example:

    >>> udp_header = UDPHeader(
    ...     src_port=Port["HTTP_ALT"],
    ...     dst_port=Port["HTTP"],
    ... )
    """

    src_port: int
    dst_port: int


class TCPFlags(Enum):
    """
    Enum representing TCP control flags used in a TCP connection.

    Flags are used to indicate a particular state of the connection or provide additional information.

    Members:
    - SYN: (1) - Used in the first step of connection establishment phase or 3-way handshake process between two hosts.
    - ACK: (2) - Used to acknowledge packets that are successfully received by the host.
    - FIN: (4) - Used to request connection termination when there is no more data from the sender.
    - RST: (8) - Used to terminate the connection if there is an issue with the TCP connection.
    """

    SYN = 1
    ACK = 2
    FIN = 4
    RST = 8


class TCPHeader(BaseModel):
    """
    Represents a TCP header for the transport layer of a Network Frame.

    :param src_port: Source port.
    :param dst_port: Destination port.
    :param flags: TCP flags (list of TCPFlags members).

    :Example:

    >>> tcp_header = TCPHeader(
    ...     src_port=Port["HTTP_ALT"],
    ...     dst_port=Port["HTTP"],
    ...     flags=[TCPFlags.SYN, TCPFlags.ACK]
    ... )
    """

    src_port: int
    dst_port: int
    flags: List[TCPFlags] = [TCPFlags.SYN]
