"""Agents with predefined behaviours."""
from src.primaite.game.agent.interface import AbstractScriptedAgent


class GreenWebBrowsingAgent(AbstractScriptedAgent):
    """Scripted agent which attempts to send web requests to a target node."""

    raise NotImplementedError


class RedDatabaseCorruptingAgent(AbstractScriptedAgent):
    """Scripted agent which attempts to corrupt the database of the target node."""

    raise NotImplementedError
