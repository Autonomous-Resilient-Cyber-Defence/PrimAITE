# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
"""Enumerations for APE."""

from enum import Enum, IntEnum


class NodeType(Enum):
    """Node type enumeration."""

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


class Priority(Enum):
    """Node priority enumeration."""

    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4
    P5 = 5


class HardwareState(Enum):
    """Node hardware state enumeration."""

    NONE = 0
    ON = 1
    OFF = 2
    RESETTING = 3
    SHUTTING_DOWN = 4
    BOOTING = 5


class SoftwareState(Enum):
    """Software or Service state enumeration."""

    NONE = 0
    GOOD = 1
    PATCHING = 2
    COMPROMISED = 3
    OVERWHELMED = 4


class NodePOLType(Enum):
    """Node Pattern of Life type enumeration."""

    NONE = 0
    OPERATING = 1
    OS = 2
    SERVICE = 3
    FILE = 4


class NodePOLInitiator(Enum):
    """Node Pattern of Life initiator enumeration."""

    DIRECT = 1
    IER = 2
    SERVICE = 3


class Protocol(Enum):
    """Service protocol enumeration."""

    LDAP = 0
    FTP = 1
    HTTPS = 2
    SMTP = 3
    RTP = 4
    IPP = 5
    TCP = 6
    NONE = 7


class SessionType(Enum):
    """The type of PrimAITE Session to be run."""

    TRAIN = 1
    "Train an agent"
    EVAL = 2
    "Evaluate an agent"
    TRAIN_EVAL = 3
    "Train then evaluate an agent"


class AgentFramework(Enum):
    """The agent algorithm framework/package."""

    CUSTOM = 0
    "Custom Agent"
    SB3 = 1
    "Stable Baselines3"
    RLLIB = 2
    "Ray RLlib"


class DeepLearningFramework(Enum):
    """The deep learning framework."""

    TF = "tf"
    "Tensorflow"
    TF2 = "tf2"
    "Tensorflow 2.x"
    TORCH = "torch"
    "PyTorch"


class AgentIdentifier(Enum):
    """The Red Agent algo/class."""

    A2C = 1
    "Advantage Actor Critic"
    PPO = 2
    "Proximal Policy Optimization"
    HARDCODED = 3
    "The Hardcoded agents"
    DO_NOTHING = 4
    "The DoNothing agents"
    RANDOM = 5
    "The RandomAgent"
    DUMMY = 6
    "The DummyAgent"


class HardCodedAgentView(Enum):
    """The view the deterministic hard-coded agent has of the environment."""

    BASIC = 1
    "The current observation space only"
    FULL = 2
    "Full environment view with actions taken and reward feedback"


class ActionType(Enum):
    """Action type enumeration."""

    NODE = 0
    ACL = 1
    ANY = 2


# TODO: this is not used anymore, write a ticket to delete it.
class ObservationType(Enum):
    """Observation type enumeration."""

    BOX = 0
    MULTIDISCRETE = 1


class FileSystemState(Enum):
    """File System State."""

    GOOD = 1
    CORRUPT = 2
    DESTROYED = 3
    REPAIRING = 4
    RESTORING = 5


class NodeHardwareAction(Enum):
    """Node hardware action."""

    NONE = 0
    ON = 1
    OFF = 2
    RESET = 3


class NodeSoftwareAction(Enum):
    """Node software action."""

    NONE = 0
    PATCHING = 1


class LinkStatus(Enum):
    """Link traffic status."""

    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    OVERLOAD = 4


class SB3OutputVerboseLevel(IntEnum):
    """The Stable Baselines3 learn/eval output verbosity level."""

    NONE = 0
    INFO = 1
    DEBUG = 2
