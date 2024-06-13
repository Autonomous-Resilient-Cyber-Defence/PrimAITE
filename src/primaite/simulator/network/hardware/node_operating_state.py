# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from enum import Enum


class NodeOperatingState(Enum):
    """Enumeration of Node Operating States."""

    ON = 1
    "The node is powered on."
    OFF = 2
    "The node is powered off."
    BOOTING = 3
    "The node is in the process of booting up."
    SHUTTING_DOWN = 4
    "The node is in the process of shutting down."
