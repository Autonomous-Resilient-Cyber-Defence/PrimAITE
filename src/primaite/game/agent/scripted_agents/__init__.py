# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""Agents that automatically choose their behaviour according to scripted rules."""
from primaite.game.agent import interface
from primaite.game.agent.scripted_agents import (
    abstract_tap,
    data_manipulation_bot,
    probabilistic_agent,
    random_agent,
    TAP001,
    TAP003,
)

__all__ = (
    "abstract_tap",
    "data_manipulation_bot",
    "interface",
    "probabilistic_agent",
    "random_agent",
    "TAP001",
    "TAP003",
)
