from enum import Enum
from typing import List, Union

from pydantic import BaseModel


class Port(Enum):
    """Enumeration of common known TCP/UDP ports used by protocols for operation of network applications."""

    WOL = 9
    "Wake-on-Lan (WOL) - Used to turn or awaken a computer from sleep mode by a network message."
    FTP_DATA = 20
    "File Transfer [Default Data]"
    FTP = 21
    "File Transfer Protocol (FTP) - FTP control (command)"
    SSH = 22
    "Secure Shell (SSH) - Used for secure remote access and command execution."
    SMTP = 25
    "Simple Mail Transfer Protocol (SMTP) - Used for email delivery between servers."
    DNS = 53
    "Domain Name System (DNS) - Used for translating domain names to IP addresses."
    HTTP = 80
    "HyperText Transfer Protocol (HTTP) - Used for web traffic."
    POP3 = 110
    "Post Office Protocol version 3 (POP3) - Used for retrieving emails from a mail server."
    SFTP = 115
    "Secure File Transfer Protocol (SFTP) - Used for secure file transfer over SSH."
    NTP = 123
    "Network Time Protocol (NTP) - Used for clock synchronization between computer systems."
    IMAP = 143
    "Internet Message Access Protocol (IMAP) - Used for retrieving emails from a mail server."
    SNMP = 161
    "Simple Network Management Protocol (SNMP) - Used for network device management."
    SNMP_TRAP = 162
    "SNMP Trap - Used for sending SNMP notifications (traps) to a network management system."
    ARP = 219
    "Address resolution Protocol - Used to connect a MAC address to an IP address."
    LDAP = 389
    "Lightweight Directory Access Protocol (LDAP) - Used for accessing and modifying directory information."
    HTTPS = 443
    "HyperText Transfer Protocol Secure (HTTPS) - Used for secure web traffic."
    SMB = 445
    "Server Message Block (SMB) - Used for file sharing and printer sharing in Windows environments."
    IPP = 631
    "Internet Printing Protocol (IPP) - Used for printing over the internet or an intranet."
    SQL_SERVER = 1433
    "Microsoft SQL Server Database Engine - Used for communication with the SQL Server."
    MYSQL = 3306
    "MySQL Database Server - Used for MySQL database communication."
    RDP = 3389
    "Remote Desktop Protocol (RDP) - Used for remote desktop access to Windows machines."
    RTP = 5004
    "Real-time Transport Protocol (RTP) - Used for transmitting real-time media, e.g., audio and video."
    RTP_ALT = 5005
    "Alternative port for RTP (RTP_ALT) - Used in some configurations for transmitting real-time media."
    DNS_ALT = 5353
    "Alternative port for DNS (DNS_ALT) - Used in some configurations for DNS service."
    HTTP_ALT = 8080
    "Alternative port for HTTP (HTTP_ALT) - Often used as an alternative HTTP port for web applications."
    HTTPS_ALT = 8443
    "Alternative port for HTTPS (HTTPS_ALT) - Used in some configurations for secure web traffic."
    POSTGRES_SERVER = 5432
    "Postgres SQL Server."


class UDPHeader(BaseModel):
    """
    Represents a UDP header for the transport layer of a Network Frame.

    :param src_port: Source port.
    :param dst_port: Destination port.

    :Example:

    >>> udp_header = UDPHeader(
    ...     src_port=Port.HTTP_ALT,
    ...     dst_port=Port.HTTP,
    ... )
    """

    src_port: Union[Port, int]
    dst_port: Union[Port, int]


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
    ...     src_port=Port.HTTP_ALT,
    ...     dst_port=Port.HTTP,
    ...     flags=[TCPFlags.SYN, TCPFlags.ACK]
    ... )
    """

    src_port: Port
    dst_port: Port
    flags: List[TCPFlags] = [TCPFlags.SYN]
