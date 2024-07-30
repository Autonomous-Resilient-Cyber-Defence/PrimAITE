# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.system.applications.red_applications.c2.abstract_c2 import AbstractC2, C2Command
from primaite.simulator.network.protocols.masquerade import C2Payload, MasqueradePacket


class C2Server(AbstractC2):
    
    def _handle_command_output(payload):
        """Abstract Method: Used in C2 server to prase and receive the output of commands sent to the c2 beacon."""
        pass
