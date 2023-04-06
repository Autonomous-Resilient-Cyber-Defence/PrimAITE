# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
Enumerations for APE
"""

from enum import Enum

class TYPE(Enum):
    """
    Node type enumeration
    """

    CCTV = 1
    SWITCH = 2
    COMPUTER = 3
    LINK = 4
    MONITOR = 5
    PRINTER = 6
    LOP = 7
    RTU = 8
    ACTUATOR = 9
    SERVER = 10

class PRIORITY(Enum):
    """
    Node priority enumeration
    """

    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4
    P5 = 5

class HARDWARE_STATE(Enum):
    """
    Node hardware state enumeration
    """

    ON = 1
    OFF = 2
    RESETTING = 3

class SOFTWARE_STATE(Enum):
    """
    O/S or Service state enumeration
    """

    GOOD = 1
    PATCHING = 2
    COMPROMISED = 3
    OVERWHELMED = 4

class NODE_POL_TYPE(Enum):
    """
    Node Pattern of Life type enumeration
    """

    OPERATING = 1
    OS = 2
    SERVICE = 3
    FILE = 4

class NODE_POL_INITIATOR(Enum):
    """
    Node Pattern of Life initiator enumeration
    """

    DIRECT = 1
    IER = 2
    SERVICE = 3

class PROTOCOL(Enum):
    """
    Service protocol enumeration
    """

    LDAP = 0
    FTP = 1
    HTTPS = 2
    SMTP = 3
    RTP = 4
    IPP = 5
    TCP = 6
    NONE = 7

class ACTION_TYPE(Enum):
    """
    Action type enumeration
    """

    NODE = 0
    ACL = 1

class FILE_SYSTEM_STATE(Enum):
    """
    File System State
    """

    GOOD = 1
    CORRUPT = 2
    DESTROYED = 3
    REPAIRING = 4
    RESTORING = 5
