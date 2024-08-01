# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.system.applications.red_applications.c2.abstract_c2 import AbstractC2, C2Command
from primaite.simulator.network.protocols.masquerade import C2Payload, MasqueradePacket
from primaite.simulator.core import RequestManager, RequestType
from primaite.interface.request import RequestFormat, RequestResponse
from prettytable import MARKDOWN, PrettyTable
from typing import Dict,Optional

class C2Server(AbstractC2, identifier="C2 Server"):
    # TODO:
    # Implement the request manager and agent actions.
    # Implement the output handling methods. (These need to interface with the actions)
    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()

        def _configure_ransomware_action(request: RequestFormat, context: Dict) -> RequestResponse:
            """Requests - Sends a RANSOMWARE_CONFIGURE C2Command to the C2 Beacon with the given parameters.

            :param request: Request with one element containing a dict of parameters for the configure method.
            :type request: RequestFormat
            :param context: additional context for resolving this action, currently unused
            :type context: dict
            :return: RequestResponse object with a success code reflecting whether the configuration could be applied.
            :rtype: RequestResponse
            """
            # TODO: Parse the parameters from the request to get the parameters
            placeholder: dict = {}
            return self._send_command(given_command=C2Command.RANSOMWARE_CONFIGURE, command_options=placeholder)

        def _launch_ransomware_action(request: RequestFormat, context: Dict) -> RequestResponse:
            """Agent Action - Sends a RANSOMWARE_LAUNCH C2Command to the C2 Beacon with the given parameters.
            
            :param request: Request with one element containing a dict of parameters for the configure method.
            :type request: RequestFormat
            :param context: additional context for resolving this action, currently unused
            :type context: dict
            :return: RequestResponse object with a success code reflecting whether the ransomware was launched.
            :rtype: RequestResponse
            """
            # TODO: Parse the parameters from the request to get the parameters
            placeholder: dict = {}
            return self._send_command(given_command=C2Command.RANSOMWARE_LAUNCH, command_options=placeholder)

        def _remote_terminal_action(request: RequestFormat, context: Dict) -> RequestResponse:
            """Agent Action - Sends a TERMINAL C2Command to the C2 Beacon with the given parameters.
            
            :param request: Request with one element containing a dict of parameters for the configure method.
            :type request: RequestFormat
            :param context: additional context for resolving this action, currently unused
            :type context: dict
            :return: RequestResponse object with a success code reflecting whether the ransomware was launched.
            :rtype: RequestResponse
            """
            # TODO: Parse the parameters from the request to get the parameters
            placeholder: dict = {}
            return self._send_command(given_command=C2Command.RANSOMWARE_LAUNCH, command_options=placeholder)

        rm.add_request(
            name="c2_ransomware_configure",
            request_type=RequestType(func=_configure_ransomware_action),
        )
        rm.add_request(
            name="c2_ransomware_launch",
            request_type=RequestType(func=_launch_ransomware_action),
        )
        rm.add_request(
            name="c2_terminal_command",
            request_type=RequestType(func=_remote_terminal_action),
        )
        return rm

    def __init__(self, **kwargs):
        kwargs["name"] = "C2Server"
        super().__init__(**kwargs)

    def _handle_command_output(self, payload: MasqueradePacket) -> RequestResponse:
        """
        Handles the parsing of C2 Command Output from C2 Traffic (Masquerade Packets)
        as well as then calling the relevant method dependant on the C2 Command.
        
        :param payload: The OUTPUT C2 Payload 
        :type payload: MasqueradePacket
        :return: Returns the Request Response of the C2 Beacon's host terminal service execute method.
        :rtype Request Response:
        """
        self.sys_log.info(f"{self.name}: Received command response from C2 Beacon: {payload}.")
        command_output = payload.payload
        if command_output != MasqueradePacket:
            self.sys_log.warning(f"{self.name}: Received invalid command response: {command_output}.")
            return RequestResponse(status="failure", data={"Received unexpected C2 Response."})
        return command_output
    

    def _send_command(self, given_command: C2Command, command_options: Dict) -> RequestResponse:
        """
        Sends a command to the C2 Beacon.
        
        # TODO: Expand this docustring.

        :param given_command: The C2 command to be sent to the C2 Beacon.
        :type given_command: C2Command.
        :param command_options: The relevant C2 Beacon parameters.
        :type command_options: Dict
        :return: Returns the Request Response of the C2 Beacon's host terminal service execute method.
        :rtype: RequestResponse
        """
        if given_command != C2Payload:
            self.sys_log.warning(f"{self.name}: Received unexpected C2 command. Unable to send command.")
            return RequestResponse(status="failure", data={"Received unexpected C2Command. Unable to send command."})

        self.sys_log.info(f"{self.name}: Attempting to send command {given_command}.")
        command_packet = self._craft_packet(given_command=given_command, command_options=command_options)

        # Need to investigate if this is correct.
        if self.send(payload=command_packet,            
            dest_ip_address=self.c2_remote_connection,
            src_port=self.current_masquerade_port,
            dst_port=self.current_masquerade_port, 
            ip_protocol=self.current_masquerade_protocol,
            session_id=None):
            self.sys_log.info(f"{self.name}: Successfully sent {given_command}.")
            self.sys_log.info(f"{self.name}: Awaiting command response {given_command}.")
            return self._handle_command_output(command_packet)


    # TODO: Perhaps make a new pydantic base model for command_options?
    # TODO: Perhaps make the return optional? Returns False is the packet was unable to be crafted.
    def _craft_packet(self, given_command: C2Command, command_options: Dict) -> MasqueradePacket:
        """
        Creates a Masquerade Packet based off the command parameter and the arguments given.
        
        :param given_command: The C2 command to be sent to the C2 Beacon.
        :type given_command: C2Command.
        :param command_options: The relevant C2 Beacon parameters.F
        :type command_options: Dict
        :return: Returns the construct MasqueradePacket
        :rtype: MasqueradePacket
        """
        # TODO: Validation on command_options.
        constructed_packet = MasqueradePacket(
            masquerade_protocol=self.current_masquerade_protocol,
            masquerade_port=self.current_masquerade_port,
            payload_type=C2Payload.INPUT,
            command=given_command,
            payload=command_options
        )
        return constructed_packet
        
    # Defining this abstract method
    def _handle_command_input(self, payload):
        """C2 Servers currently do not receive input commands coming from the C2 Beacons."""
        self.sys_log.warning(f"{self.name}: C2 Server received an unexpected INPUT payload: {payload}")
        pass


    def show(self, markdown: bool = False):
        """
        Prints a table of the current C2 attributes on a C2 Server.

        :param markdown: If True, outputs the table in markdown format. Default is False.
        """
        table = PrettyTable(["C2 Connection Active", "C2 Remote Connection", "Keep Alive Inactivity"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.name} Running Status"
        table.add_row([self.c2_connection_active, self.c2_remote_connection, self.keep_alive_inactivity])
        print(table)
