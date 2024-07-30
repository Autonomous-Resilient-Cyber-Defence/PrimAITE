# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from primaite.simulator.system.applications.red_applications.c2.abstract_c2 import AbstractC2, C2Command
#from primaite.simulator.system.services.terminal.terminal import Terminal
from primaite.simulator.core import RequestManager, RequestType
from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.network.protocols.masquerade import C2Payload, MasqueradePacket
from primaite.simulator.network.transmission.network_layer import IPProtocol
from ipaddress import IPv4Address
from typing import Dict,Optional
from primaite.simulator.network.transmission.transport_layer import Port
from enum import Enum
from primaite.simulator.system.software import SoftwareHealthState
from primaite.simulator.system.applications.application import ApplicationOperatingState

class C2Beacon(AbstractC2):
    """
    C2 Beacon Application.

    Represents a generic C2 beacon which can be used in conjunction with the C2 Server
    to simulate malicious communications within primAITE.

    Must be configured with the C2 Server's Ip Address upon installation.
    
    Extends the Abstract C2 application to include the following:

    1. Receiving commands from the C2 Server (Command input)
    2. Leveraging the terminal application to execute requests (dependant on the command given)
    3. Sending the RequestResponse back to the C2 Server (Command output)
    """
    
    keep_alive_frequency: int = 5
    "The frequency at which ``Keep Alive`` packets are sent to the C2 Server from the C2 Beacon."

    # TODO:
    # Implement the placeholder command methods
    # Implement the keep alive frequency.
    # Implement a command output method that sends the RequestResponse to the C2 server.
    # Uncomment the terminal Import and the terminal property after terminal PR

    #@property
    #def _host_terminal(self) -> Terminal:
    #    """Return the Terminal that is installed on the same machine as the C2 Beacon."""
    #    host_terminal: Terminal = self.software_manager.software.get("Terminal")
    #    if host_terminal: is None:
    #        self.sys_log.warning(f"{self.__class__.__name__} cannot find a terminal on its host.")
    #    return host_terminal

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        rm.add_request(
            name="execute",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.establish())),
        )

        def _configure(request: RequestFormat, context: Dict) -> RequestResponse:
            """
            Request for configuring the C2 Beacon.

            :param request: Request with one element containing a dict of parameters for the configure method.
            :type request: RequestFormat
            :param context: additional context for resolving this action, currently unused
            :type context: dict
            :return: RequestResponse object with a success code reflecting whether the configuration could be applied.
            :rtype: RequestResponse
            """
            server_ip = request[-1].get("c2_server_ip_address")
            if server_ip == None:
                self.sys_log.error(f"{self.name}: Did not receive C2 Server IP in configuration parameters.")
                RequestResponse(status="failure", data={"No C2 Server IP given to C2 beacon. Unable to configure C2 Beacon"})

            c2_remote_ip = IPv4Address(c2_remote_ip)
            frequency = request[-1].get("keep_alive_frequency")
            protocol= request[-1].get("masquerade_protocol")
            port = request[-1].get("masquerade_port")
            return RequestResponse.from_bool(self.configure(c2_server_ip_address=server_ip,
                                                            keep_alive_frequency=frequency,
                                                            masquerade_protocol=protocol,
                                                            masquerade_port=port))

        rm.add_request("configure", request_type=RequestType(func=_configure))
        return rm
    
    def __init__(self, **kwargs):
        self.name = "C2Beacon"
        super.__init__(**kwargs)
    
    def configure(
        self,
        c2_server_ip_address: IPv4Address = None,
        keep_alive_frequency: Optional[int] = 5,
        masquerade_protocol: Optional[Enum] = IPProtocol.TCP,
        masquerade_port: Optional[Enum] = Port.HTTP,
    ) -> bool:
        """
        Configures the C2 beacon to communicate with the C2 server with following additional parameters.


        :param c2_server_ip_address: The IP Address of the C2 Server. Used to establish connection.
        :type c2_server_ip_address: IPv4Address
        :param keep_alive_frequency: The frequency (timesteps) at which the C2 beacon will send keep alive(s).
        :type keep_alive_frequency: Int
        :param masquerade_protocol: The Protocol that C2 Traffic will masquerade as. Defaults as TCP.
        :type masquerade_protocol: Enum (IPProtocol)
        :param masquerade_port: The Port that the C2 Traffic will masquerade as. Defaults to FTP.
        :type masquerade_port: Enum (Port)
        """
        self.c2_remote_connection = c2_server_ip_address
        self.keep_alive_frequency = keep_alive_frequency
        self.current_masquerade_port = masquerade_port
        self.current_masquerade_protocol = masquerade_protocol
        self.sys_log.info(
            f"{self.name}: Configured {self.name} with remote C2 server connection: {c2_server_ip_address=}."
        )
        self.sys_log.debug(f"{self.name}: configured with the following settings:"
                           f"Remote C2 Server: {c2_server_ip_address}"
                           f"Keep Alive Frequency {keep_alive_frequency}"
                           f"Masquerade Protocol: {masquerade_protocol}"
                           f"Masquerade Port: {masquerade_port}")
        return True


    # I THINK that once the application is running it can respond to incoming traffic but I'll need to test this later.
    def establish(self) -> bool:
        """Establishes connection to the C2 server via a send alive. Must be called after the C2 Beacon is configured."""
        self.run()
        self._send_keep_alive()
        self.num_executions += 1
        

    def _handle_command_input(self, payload: MasqueradePacket) -> bool:
        """
        Handles the parsing of C2 Commands from C2 Traffic (Masquerade Packets)
        as well as then calling the relevant method dependant on the C2 Command.
        
        :param payload: The INPUT C2 Payload 
        :type payload: MasqueradePacket
        :return: The Request Response provided by the terminal execute method.
        :rtype Request Response:
        """
        command = payload.payload_type
        if command != C2Payload:
            self.sys_log.warning(f"{self.name}: Received unexpected C2 command. Unable to resolve command")
            return self._return_command_output(RequestResponse(status="failure", data={"Received unexpected C2Command. Unable to resolve command."}))

        if command == C2Command.RANSOMWARE_CONFIGURE:
            self.sys_log.info(f"{self.name}: Received a ransomware configuration C2 command.")
            return self._return_command_output(self._command_ransomware_config(payload))

        elif command == C2Command.RANSOMWARE_LAUNCH:
            self.sys_log.info(f"{self.name}: Received a ransomware launch C2 command.")
            return self._return_command_output(self._command_ransomware_launch(payload))

        elif payload.payload_type == C2Command.TERMINAL:
            self.sys_log.info(f"{self.name}: Received a terminal C2 command.")
            return self._return_command_output(self._command_terminal(payload))

        else:
            self.sys_log.error(f"{self.name}: Received an C2 command: {command} but was unable to resolve command.")
            return self._return_command_output(RequestResponse(status="failure", data={"Unexpected Behaviour. Unable to resolve command."}))


    def _return_command_output(self, command_output: RequestResponse) -> bool:
        """Responsible for responding to the C2 Server with the output of the given command."""
        output_packet = MasqueradePacket(
            masquerade_protocol=self.current_masquerade_protocol,
            masquerade_port=self.current_masquerade_port,
            payload_type=C2Payload.OUTPUT,
            payload=command_output
        )
        if self.send(
            self,
            payload=output_packet,
            dest_ip_address=self.c2_remote_connection,
            port=self.current_masquerade_port,
            protocol=self.current_masquerade_protocol,
        ):
            self.sys_log.info(f"{self.name}: Command output sent to {self.c2_remote_connection}")
            self.sys_log.debug(f"{self.name}: on {self.current_masquerade_port} via {self.current_masquerade_protocol}")
            return True
        else:
            self.sys_log.warning(
                f"{self.name}: failed to send a output packet. The node may be unable to access the network."
            )
            return False

    def _command_ransomware_config(self, payload: MasqueradePacket) -> RequestResponse:
        """
        C2 Command: Ransomware Configuration

        Creates a request that configures the ransomware based off the configuration options given.
        This request is then sent to the terminal service in order to be executed.

        :return: Returns the Request Response returned by the Terminal execute method.
        :rtype: Request Response
        """
        pass
        #return self._host_terminal.execute(command)

    def _command_ransomware_launch(self, payload: MasqueradePacket) -> RequestResponse:
        """
        C2 Command: Ransomware Execute

        Creates a request that executes the ransomware script.
        This request is then sent to the terminal service in order to be executed.

        :return: Returns the Request Response returned by the Terminal execute method.
        :rtype: Request Response
        
        Creates a Request that launches the ransomware.
        """
        pass
        #return self._host_terminal.execute(command)

    def _command_terminal(self, payload: MasqueradePacket) -> RequestResponse:
        """
        C2 Command: Ransomware Execute

        Creates a request that executes the ransomware script.
        This request is then sent to the terminal service in order to be executed.

        :return: Returns the Request Response returned by the Terminal execute method.
        :rtype: Request Response
        
        Creates a Request that launches the ransomware.
        """
        pass
        #return self._host_terminal.execute(command)


    # Not entirely sure if this actually works.
    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep to the c2_beacon. 
        Used to keep track of when the c2 beacon should send another keep alive.

        The following logic is applied:

        1. Each timestep the keep_alive_inactivity is increased.

        2. If the keep alive inactivity eclipses that of the keep alive frequency then another keep alive is sent.

        3. If the c2 beacon receives a keep alive response packet then the ``keep_alive_inactivity`` attribute is set to 0
        
        Therefore, if ``keep_alive_inactivity`` attribute is not 0, then the connection is considered severed and c2 beacon will shut down.
        
        :param timestep: The current timestep of the simulation.
        """
        super().apply_timestep(timestep=timestep)
        if self.operating_state is ApplicationOperatingState.RUNNING and self.health_state_actual is SoftwareHealthState.GOOD:
            self.keep_alive_inactivity += 1
            if not self._check_c2_connection(timestep):
                self.sys_log.error(f"{self.name}: Connection Severed - Application Closing.")
                self.clear_connections()
                self.close()
        return


    def _check_c2_connection(self, timestep) -> bool:
        """Checks the C2 Server connection. If a connection cannot be confirmed then the c2 beacon will halt and close."""
        if self.keep_alive_inactivity > self.keep_alive_frequency:
            self.sys_log.info(f"{self.name}: Keep Alive sent to {self.c2_remote_connection} at timestep {timestep}.")
            self._send_keep_alive()
            if self.keep_alive_inactivity != 0:
                self.sys_log.warning(f"{self.name}: Did not receive keep alive from c2 Server. Connection considered severed.")
                return False
        return True