"""Utility script to start the gate server for running PrimAITE in attached mode."""
from arcd_gate.server.gate_service import GATEService


def start_gate_server():
    """Start the gate server."""
    service = GATEService()
    service.start()


if __name__ == "__main__":
    start_gate_server()
