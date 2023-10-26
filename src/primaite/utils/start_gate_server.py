"""Utility script to start the gate server for running PrimAITE in attached mode."""
from arcd_gate.server.gate_service import GATEService

service = GATEService()
service.start()
