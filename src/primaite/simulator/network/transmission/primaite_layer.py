# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from enum import Enum

from pydantic import BaseModel


class DataStatus(Enum):
    """
    The status of the data in transmission.

    Members:
     - GOOD: 1
     - COMPROMISED: 2
     - CORRUPT: 3
    """

    GOOD = 1
    COMPROMISED = 2
    CORRUPT = 3


class AgentSource(Enum):
    """
    The agent source of the transmission.

    Members:
     - RED: 1
     - GREEN: 2
     - BLUE: 3
    """

    RED = 1
    GREEN = 2
    BLUE = 3


class PrimaiteHeader(BaseModel):
    """A custom header for carrying PrimAITE transmission metadata required for RL."""

    agent_source: AgentSource = AgentSource.GREEN
    data_status: DataStatus = DataStatus.GOOD
