# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from enum import Enum
from ipaddress import IPv4Address
from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable
from pydantic import validate_call

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.protocols.masquerade import C2Packet
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.red_applications.c2.abstract_c2 import AbstractC2, C2Command, C2Payload
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript
from primaite.simulator.system.services.terminal.terminal import (
    LocalTerminalConnection,
    RemoteTerminalConnection,
    Terminal,
)


class C2Beacon(AbstractC2, identifier="C2Beacon"):
    """
    C2 Beacon Application.

    Represents a vendor generic C2 beacon is used in conjunction with the C2 Server
    to simulate malicious communications and infrastructure within primAITE.

    Must be configured with the C2 Server's IP Address upon installation.

    Extends the Abstract C2 application to include the following:

    1. Receiving commands from the C2 Server (Command input)
    2. Leveraging the terminal application to execute requests (dependant on the command given)
    3. Sending the RequestResponse back to the C2 Server (Command output)
    """

    keep_alive_attempted: bool = False
    """Indicates if a keep alive has been attempted to be sent this timestep. Used to prevent packet storms."""

    local_terminal_session: LocalTerminalConnection = None
    "The currently in use local terminal session."

    remote_terminal_session: RemoteTerminalConnection = None
    "The currently in use remote terminal session"

    @property
    def _host_terminal(self) -> Optional[Terminal]:
        """Return the Terminal that is installed on the same machine as the C2 Beacon."""
        host_terminal: Terminal = self.software_manager.software.get("Terminal")
        if host_terminal is None:
            self.sys_log.warning(f"{self.__class__.__name__} cannot find a terminal on its host.")
        return host_terminal

    @property
    def _host_ransomware_script(self) -> RansomwareScript:
        """Return the RansomwareScript that is installed on the same machine as the C2 Beacon."""
        ransomware_script: RansomwareScript = self.software_manager.software.get("RansomwareScript")
        if ransomware_script is None:
            self.sys_log.warning(f"{self.__class__.__name__} cannot find installed ransomware on its host.")
        return ransomware_script

    def get_terminal_session(self, username: str, password: str) -> Optional[LocalTerminalConnection]:
        """Return an instance of a Local Terminal Connection upon successful login. Otherwise returns None."""
        if self.local_terminal_session is None:
            host_terminal: Terminal = self._host_terminal
            self.local_terminal_session = host_terminal.login(username=username, password=password)

        return self.local_terminal_session

    def get_remote_terminal_session(
        self, username: str, password: str, ip_address: IPv4Address
    ) -> Optional[RemoteTerminalConnection]:
        """Return an instance of a Local Terminal Connection upon successful login. Otherwise returns None."""
        if self.remote_terminal_session is None:
            host_terminal: Terminal = self._host_terminal
            self.remote_terminal_session = host_terminal.login(
                username=username, password=password, ip_address=ip_address
            )

        return self.remote_terminal_session

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
            c2_remote_ip = request[-1].get("c2_server_ip_address")
            if c2_remote_ip is None:
                self.sys_log.error(f"{self.name}: Did not receive C2 Server IP in configuration parameters.")
                RequestResponse(
                    status="failure", data={"No C2 Server IP given to C2 beacon. Unable to configure C2 Beacon"}
                )

            c2_remote_ip = IPv4Address(c2_remote_ip)
            frequency = request[-1].get("keep_alive_frequency")
            protocol = request[-1].get("masquerade_protocol")
            port = request[-1].get("masquerade_port")

            return RequestResponse.from_bool(
                self.configure(
                    c2_server_ip_address=c2_remote_ip,
                    keep_alive_frequency=frequency,
                    masquerade_protocol=IPProtocol[protocol],
                    masquerade_port=Port[port],
                )
            )

        rm.add_request("configure", request_type=RequestType(func=_configure))
        return rm

    def __init__(self, **kwargs):
        kwargs["name"] = "C2Beacon"
        super().__init__(**kwargs)

    @validate_call
    def configure(
        self,
        c2_server_ip_address: IPv4Address = None,
        keep_alive_frequency: int = 5,
        masquerade_protocol: Enum = IPProtocol.TCP,
        masquerade_port: Enum = Port.HTTP,
    ) -> bool:
        """
        Configures the C2 beacon to communicate with the C2 server with following additional parameters.

        # TODO: Expand docustring.

        :param c2_server_ip_address: The IP Address of the C2 Server. Used to establish connection.
        :type c2_server_ip_address: IPv4Address
        :param keep_alive_frequency: The frequency (timesteps) at which the C2 beacon will send keep alive(s).
        :type keep_alive_frequency: Int
        :param masquerade_protocol: The Protocol that C2 Traffic will masquerade as. Defaults as TCP.
        :type masquerade_protocol: Enum (IPProtocol)
        :param masquerade_port: The Port that the C2 Traffic will masquerade as. Defaults to FTP.
        :type masquerade_port: Enum (Port)
        """
        self.c2_remote_connection = IPv4Address(c2_server_ip_address)
        self.c2_config.keep_alive_frequency = keep_alive_frequency
        self.c2_config.masquerade_port = masquerade_port
        self.c2_config.masquerade_protocol = masquerade_protocol
        self.sys_log.info(
            f"{self.name}: Configured {self.name} with remote C2 server connection: {c2_server_ip_address=}."
        )
        self.sys_log.debug(
            f"{self.name}: configured with the following settings:"
            f"Remote C2 Server: {c2_server_ip_address}"
            f"Keep Alive Frequency {keep_alive_frequency}"
            f"Masquerade Protocol: {masquerade_protocol}"
            f"Masquerade Port: {masquerade_port}"
        )
        return True

    def establish(self) -> bool:
        """Establishes connection to the C2 server via a send alive. The C2 Beacon must already be configured."""
        if self.c2_remote_connection is None:
            self.sys_log.info(f"{self.name}: Failed to establish connection. C2 Beacon has not been configured.")
            return False
        self.run()
        self.num_executions += 1
        return self._send_keep_alive(session_id=None)

    def _handle_command_input(self, payload: C2Packet, session_id: Optional[str]) -> bool:
        """
        Handles the parsing of C2 Commands from C2 Traffic (Masquerade Packets).

        Dependant the C2 Command contained within the payload.
        The following methods are called and returned.

        C2 Command           | Internal Method
        ---------------------|------------------------
        RANSOMWARE_CONFIGURE | self._command_ransomware_config()
        RANSOMWARE_LAUNCH    | self._command_ransomware_launch()
        TERMINAL             | self._command_terminal()

        Please see each method individually for further information regarding
        the implementation of these commands.

        :param payload: The INPUT C2 Payload
        :type payload: C2Packet
        :return: The Request Response provided by the terminal execute method.
        :rtype Request Response:
        """
        command = payload.command
        if not isinstance(command, C2Command):
            self.sys_log.warning(f"{self.name}: Received unexpected C2 command. Unable to resolve command")
            return self._return_command_output(
                command_output=RequestResponse(
                    status="failure",
                    data={"Reason": "C2 Beacon received unexpected C2Command. Unable to resolve command."},
                ),
                session_id=session_id,
            )

        if command == C2Command.RANSOMWARE_CONFIGURE:
            self.sys_log.info(f"{self.name}: Received a ransomware configuration C2 command.")
            return self._return_command_output(
                command_output=self._command_ransomware_config(payload), session_id=session_id
            )

        elif command == C2Command.RANSOMWARE_LAUNCH:
            self.sys_log.info(f"{self.name}: Received a ransomware launch C2 command.")
            return self._return_command_output(
                command_output=self._command_ransomware_launch(payload), session_id=session_id
            )

        elif command == C2Command.TERMINAL:
            self.sys_log.info(f"{self.name}: Received a terminal C2 command.")
            return self._return_command_output(command_output=self._command_terminal(payload), session_id=session_id)

        else:
            self.sys_log.error(f"{self.name}: Received an C2 command: {command} but was unable to resolve command.")
            return self._return_command_output(
                RequestResponse(status="failure", data={"Reason": "Unexpected Behaviour. Unable to resolve command."})
            )

    def _return_command_output(self, command_output: RequestResponse, session_id: Optional[str] = None) -> bool:
        """Responsible for responding to the C2 Server with the output of the given command.

        :param command_output: The RequestResponse returned by the terminal application's execute method.
        :type command_output: Request Response
        :param session_id: The current session established with the C2 Server.
        :type session_id: Str
        """
        output_packet = C2Packet(
            masquerade_protocol=self.c2_config.masquerade_protocol,
            masquerade_port=self.c2_config.masquerade_port,
            keep_alive_frequency=self.c2_config.keep_alive_frequency,
            payload_type=C2Payload.OUTPUT,
            payload=command_output,
        )
        if self.send(
            payload=output_packet,
            dest_ip_address=self.c2_remote_connection,
            dest_port=self.c2_config.masquerade_port,
            ip_protocol=self.c2_config.masquerade_protocol,
            session_id=session_id,
        ):
            self.sys_log.info(f"{self.name}: Command output sent to {self.c2_remote_connection}")
            self.sys_log.debug(
                f"{self.name}: on {self.c2_config.masquerade_port} via {self.c2_config.masquerade_protocol}"
            )
            return True
        else:
            self.sys_log.warning(
                f"{self.name}: failed to send a output packet. The node may be unable to access the network."
            )
            return False

    def _command_ransomware_config(self, payload: C2Packet) -> RequestResponse:
        """
        C2 Command: Ransomware Configuration.

        Calls the locally installed RansomwareScript application's configure method
        and passes the given parameters.

        The class attribute self._host_ransomware_script will return None if the host
        does not have an instance of the RansomwareScript.

        :payload C2Packet: The incoming INPUT command.
        :type Masquerade Packet: C2Packet.
        :return: Returns the Request Response returned by the Terminal execute method.
        :rtype: Request Response
        """
        given_config = payload.payload
        if self._host_ransomware_script is None:
            return RequestResponse(
                status="failure",
                data={"Reason": "Cannot find any instances of a RansomwareScript. Have you installed one?"},
            )
        return RequestResponse.from_bool(
            self._host_ransomware_script.configure(
                server_ip_address=given_config["server_ip_address"], payload=given_config["payload"]
            )
        )

    def _command_ransomware_launch(self, payload: C2Packet) -> RequestResponse:
        """
        C2 Command: Ransomware Launch.

        Creates a request that executes the ransomware script.
        This request is then sent to the terminal service in order to be executed.


        :payload C2Packet: The incoming INPUT command.
        :type Masquerade Packet: C2Packet.
        :return: Returns the Request Response returned by the Terminal execute method.
        :rtype: Request Response
        """
        if self._host_ransomware_script is None:
            return RequestResponse(
                status="failure",
                data={"Reason": "Cannot find any instances of a RansomwareScript. Have you installed one?"},
            )
        return RequestResponse.from_bool(self._host_ransomware_script.attack())

    def _command_terminal(self, payload: C2Packet) -> RequestResponse:
        """
        C2 Command: Terminal.

        Creates a request that executes a terminal command.
        This request is then sent to the terminal service in order to be executed.

        :payload C2Packet: The incoming INPUT command.
        :type Masquerade Packet: C2Packet.
        :return: Returns the Request Response returned by the Terminal execute method.
        :rtype: Request Response
        """
        terminal_output: Dict[int, RequestResponse] = {}
        given_commands: list[RequestFormat]

        if self._host_terminal is None:
            return RequestResponse(
                status="failure",
                data={"Reason": "Host does not seem to have terminal installed. Unable to resolve command."},
            )

        given_commands = payload.payload.get("commands")
        given_username = payload.payload.get("username")
        given_password = payload.payload.get("password")
        remote_ip = payload.payload.get("ip_address")

        # Creating a remote terminal session if given an IP Address, otherwise using a local terminal session.
        if remote_ip is None:
            terminal_session = self.get_terminal_session(username=given_username, password=given_password)
        else:
            terminal_session = self.get_remote_terminal_session(
                username=given_username, password=given_password, ip_address=remote_ip
            )

        if terminal_session is None:
            return RequestResponse(
                status="failure", data={"reason": "Terminal Login failed. Cannot create a terminal session."}
            )

        for index, given_command in enumerate(given_commands):
            # A try catch exception ladder was used but was considered not the best approach
            # as it can end up obscuring visibility of actual bugs (Not the expected ones) and was a temporary solution.
            # TODO: Refactor + add further validation to ensure that a request is correct. (maybe a pydantic method?)
            terminal_output[index] = terminal_session.execute(given_command)

        # Reset our remote terminal session.
        self.remote_terminal_session is None
        return RequestResponse(status="success", data=terminal_output)

    def _handle_keep_alive(self, payload: C2Packet, session_id: Optional[str]) -> bool:
        """
        Handles receiving and sending keep alive payloads. This method is only called if we receive a keep alive.

        In the C2 Beacon implementation of this method the c2 connection active boolean
        is set to true and the keep alive inactivity is reset only after sending a keep alive
        as wel as receiving a response back from the C2 Server.

        This is because the C2 Server is the listener and thus will only ever receive packets from
        the C2 Beacon rather than the other way around. (The C2 Beacon is akin to a reverse shell)

        Therefore, we need a response back from the listener (C2 Server)
        before the C2 beacon is able to confirm it's connection.

        Returns False if a keep alive was unable to be sent.
        Returns True if a keep alive was successfully sent or already has been sent this timestep.

        :return: True if successfully handled, false otherwise.
        :rtype: Bool
        """
        self.sys_log.info(f"{self.name}: Keep Alive Received from {self.c2_remote_connection}.")

        # Using this guard clause to prevent packet storms and recognise that we've achieved a connection.
        # This guard clause triggers on the c2 suite that establishes connection.
        if self.keep_alive_attempted is True:
            self.c2_connection_active = True  # Sets the connection to active
            self.keep_alive_inactivity = 0  # Sets the keep alive inactivity to zero
            self.c2_session = self.software_manager.session_manager.sessions_by_uuid[session_id]

            # We set keep alive_attempted here to show that we've achieved connection.
            self.keep_alive_attempted = False
            self.sys_log.warning(f"{self.name}: Connection successfully Established with C2 Server.")
            return True

        # If we've reached this part of the method then we've received a keep alive but haven't sent a reply.
        # Therefore we also need to configure the masquerade attributes based off the keep alive sent.
        if self._resolve_keep_alive(payload, session_id) is False:
            self.sys_log.warning(f"{self.name}: Keep Alive Could not be resolved correctly. Refusing Keep Alive.")
            return False

        self.keep_alive_attempted = True
        # If this method returns true then we have sent successfully sent a keep alive.
        return self._send_keep_alive(session_id)

    def _confirm_connection(self, timestep: int) -> bool:
        """Checks the suitability of the current C2 Server connection.

        If a connection cannot be confirmed then this method will return false otherwise true.

        :param timestep: The current timestep of the simulation.
        :type timestep: Int
        :return: Returns False if connection was lost. Returns True if connection is active or re-established.
        :rtype bool:
        """
        self.keep_alive_attempted = False  # Resetting keep alive sent.
        if self.keep_alive_inactivity == self.c2_config.keep_alive_frequency:
            self.sys_log.info(
                f"{self.name}: Attempting to Send Keep Alive to {self.c2_remote_connection} at timestep {timestep}."
            )
            self._send_keep_alive(session_id=self.c2_session.uuid)
            if self.keep_alive_inactivity != 0:
                self.sys_log.warning(
                    f"{self.name}: Did not receive keep alive from c2 Server. Connection considered severed."
                )
                self._reset_c2_connection()
                self.close()
                return False
        return True

    # Defining this abstract method from Abstract C2
    def _handle_command_output(self, payload: C2Packet):
        """C2 Beacons currently does not need to handle output commands coming from the C2 Servers."""
        self.sys_log.warning(f"{self.name}: C2 Beacon received an unexpected OUTPUT payload: {payload}.")
        pass

    def show(self, markdown: bool = False):
        """
        Prints a table of the current status of the C2 Beacon.

        Displays the current values of the following C2 attributes:

        ``C2 Connection Active``:
        If the C2 Beacon is currently connected to the C2 Server

        ``C2 Remote Connection``:
        The IP of the C2 Server. (Configured by upon installation)

        ``Keep Alive Inactivity``:
        How many timesteps have occurred since the last keep alive.

        ``Keep Alive Frequency``:
        How often should the C2 Beacon attempt a keep alive?

        ``Current Masquerade Protocol``:
        The current protocol that the C2 Traffic is using. (e.g TCP/UDP)

        ``Current Masquerade Port``:
        The current port that the C2 Traffic is using. (e.g HTTP (Port 80))

        :param markdown: If True, outputs the table in markdown format. Default is False.
        """
        table = PrettyTable(
            [
                "C2 Connection Active",
                "C2 Remote Connection",
                "Keep Alive Inactivity",
                "Keep Alive Frequency",
                "Current Masquerade Protocol",
                "Current Masquerade Port",
            ]
        )
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.name} Running Status"
        table.add_row(
            [
                self.c2_connection_active,
                self.c2_remote_connection,
                self.keep_alive_inactivity,
                self.c2_config.keep_alive_frequency,
                self.c2_config.masquerade_protocol,
                self.c2_config.masquerade_port,
            ]
        )
        print(table)
