# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.system.applications.red_applications.c2.abstract_c2 import AbstractC2, C2Command
from primaite.simulator.network.protocols.masquerade import C2Payload, MasqueradePacket


class C2Server(AbstractC2):
    # TODO:
    # Implement the request manager and agent actions.
    # Implement the output handling methods. (These need to interface with the actions)
    
    def _handle_command_output(payload):
        """Abstract Method: Used in C2 server to parse and receive the output of commands sent to the c2 beacon."""
        pass
    