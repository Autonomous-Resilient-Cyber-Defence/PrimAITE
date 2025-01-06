# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable
from pydantic import Field, validate_call

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.protocols.masquerade import C2Packet
from primaite.simulator.system.applications.red_applications.c2 import ExfilOpts, RansomwareOpts, TerminalOpts
from primaite.simulator.system.applications.red_applications.c2.abstract_c2 import AbstractC2, C2Command, C2Payload
from primaite.simulator.system.applications.red_applications.ransomware_script import RansomwareScript
from primaite.simulator.system.services.terminal.terminal import Terminal, TerminalClientConnection
from primaite.utils.validation.ip_protocol import IPProtocol, PROTOCOL_LOOKUP
from primaite.utils.validation.ipv4_address import IPV4Address
from primaite.utils.validation.port import Port, PORT_LOOKUP


class C2Beacon(AbstractC2, identifier="C2Beacon"):
    """
    C2 Beacon Application.

    Represents a vendor generic C2 beacon is used in conjunction with the C2 Server
    to simulate malicious communications and infrastructure within primAITE.

    Must be configured with the C2 Server's IP Address upon installation.
    Please refer to the _configure method for further information.

    Extends the Abstract C2 application to include the following:

    1. Receiving commands from the C2 Server (Command input)
    2. Leveraging the terminal application to execute requests (dependent on the command given)
    3. Sending the RequestResponse back to the C2 Server (Command output)

    Please refer to the Command-and-Control notebook for an in-depth example of the C2 Suite.
    """

    class ConfigSchema(AbstractC2.ConfigSchema):
        """ConfigSchema for C2Beacon."""

        type: str = "C2Beacon"
        c2_server_ip_address: Optional[IPV4Address] = None
        keep_alive_frequency: int = 5
        masquerade_protocol: IPProtocol = PROTOCOL_LOOKUP["TCP"]
        masquerade_port: Port = PORT_LOOKUP["HTTP"]

    config: ConfigSchema = Field(default_factory=lambda: C2Beacon.ConfigSchema())

    keep_alive_attempted: bool = False
    """Indicates if a keep alive has been attempted to be sent this timestep. Used to prevent packet storms."""

    terminal_session: TerminalClientConnection = None
    "The currently in use terminal session."

    def __init__(self, **kwargs):
        kwargs["name"] = "C2Beacon"
        super().__init__(**kwargs)
        self.configure(
            c2_server_ip_address=self.config.c2_server_ip_address,
            keep_alive_frequency=self.config.keep_alive_frequency,
            masquerade_port=self.config.masquerade_port,
            masquerade_protocol=self.config.masquerade_protocol,
        )

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

    def _set_terminal_session(self, username: str, password: str, ip_address: Optional[IPv4Address] = None) -> bool:
        """
        Attempts to create and a terminal session using the parameters given.

        If an IP Address is passed then this method will attempt to create a remote terminal
        session. Otherwise a local terminal session will be created.

        :return: Returns true if a terminal session was successfully set. False otherwise.
        :rtype: Bool
        """
        self.terminal_session is None
        host_terminal: Terminal = self._host_terminal
        self.terminal_session = host_terminal.login(username=username, password=password, ip_address=ip_address)
        return self.terminal_session is not None

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
                    masquerade_protocol=PROTOCOL_LOOKUP[protocol],
                    masquerade_port=PORT_LOOKUP[port],
                )
            )

        rm.add_request("configure", request_type=RequestType(func=_configure))
        return rm

    # Configure is practically setter method for the ``c2.config`` attribute that also ties into the request manager.
    @validate_call
    def configure(
        self,
        c2_server_ip_address: IPv4Address = None,
        keep_alive_frequency: int = 5,
        masquerade_protocol: str = PROTOCOL_LOOKUP["TCP"],
        masquerade_port: int = PORT_LOOKUP["HTTP"],
    ) -> bool:
        """
        Configures the C2 beacon to communicate with the C2 server.

        The C2 Beacon has four different configuration options which can be used to
        modify the networking behaviour between the C2 Server and the C2 Beacon.

        Configuration Option | Option Meaning
        ---------------------|------------------------
        c2_server_ip_address | The IP Address of the C2 Server. (The C2 Server must be running)
        keep_alive_frequency | How often should the C2 Beacon confirm it's connection in timesteps.
        masquerade_protocol  | What protocol should the C2 traffic masquerade as? (HTTP, FTP or DNS)
        masquerade_port      | What port should the C2 traffic use? (TCP or UDP)

        These configuration options are used to reassign the fields in the inherited inner class
        ``config``.

        If a connection is already in progress then this method also sends a keep alive to the C2
        Server in order for the C2 Server to sync with the new configuration settings.

        :param c2_server_ip_address: The IP Address of the C2 Server. Used to establish connection.
        :type c2_server_ip_address: IPv4Address
        :param keep_alive_frequency: The frequency (timesteps) at which the C2 beacon will send keep alive(s).
        :type keep_alive_frequency: Int
        :param masquerade_protocol: The Protocol that C2 Traffic will masquerade as. Defaults to TCP.
        :type masquerade_protocol: Enum (IPProtocol)
        :param masquerade_port: The Port that the C2 Traffic will masquerade as. Defaults to FTP.
        :type masquerade_port: Enum (Port)
        :return: Returns True if the configuration was successful, False otherwise.
        """
        self.c2_remote_connection = IPv4Address(c2_server_ip_address)
        self.config.keep_alive_frequency = keep_alive_frequency
        self.config.masquerade_port = masquerade_port
        self.config.masquerade_protocol = masquerade_protocol
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
        # Send a keep alive to the C2 Server if we already have a keep alive.
        if self.c2_connection_active is True:
            self.sys_log.info(f"{self.name}: Updating C2 Server with updated C2 configuration.")
            return self._send_keep_alive(self.c2_session.uuid if not None else None)
        return True

    def establish(self) -> bool:
        """Establishes connection to the C2 server via a send alive. The C2 Beacon must already be configured."""
        if self.c2_remote_connection is None:
            self.sys_log.info(f"{self.name}: Failed to establish connection. C2 Beacon has not been configured.")
            return False
        self.run()
        self.num_executions += 1
        # Creates a new session if using the establish method.
        return self._send_keep_alive(session_id=None)

    def _handle_command_input(self, payload: C2Packet, session_id: Optional[str]) -> bool:
        """
        Handles the parsing of C2 Commands from C2 Traffic (Masquerade Packets).

        Dependant the C2 Command parsed from the payload, the following methods are called and returned:

        C2 Command           | Internal Method
        ---------------------|------------------------
        RANSOMWARE_CONFIGURE | self._command_ransomware_config()
        RANSOMWARE_LAUNCH    | self._command_ransomware_launch()
        DATA_EXFILTRATION    | self._command_data_exfiltration()
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

        elif command == C2Command.DATA_EXFILTRATION:
            self.sys_log.info(f"{self.name}: Received a Data Exfiltration C2 command.")
            return self._return_command_output(
                command_output=self._command_data_exfiltration(payload), session_id=session_id
            )

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
        output_packet = self._craft_packet(c2_payload=C2Payload.OUTPUT, command_options=command_output)
        if self.send(
            payload=output_packet,
            dest_ip_address=self.c2_remote_connection,
            dest_port=self.config.masquerade_port,
            ip_protocol=self.config.masquerade_protocol,
            session_id=session_id,
        ):
            self.sys_log.info(f"{self.name}: Command output sent to {self.c2_remote_connection}")
            self.sys_log.debug(f"{self.name}: on {self.config.masquerade_port} via {self.config.masquerade_protocol}")
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
        command_opts = RansomwareOpts.model_validate(payload.payload)
        if self._host_ransomware_script is None:
            return RequestResponse(
                status="failure",
                data={"Reason": "Cannot find any instances of a RansomwareScript. Have you installed one?"},
            )
        return RequestResponse.from_bool(
            self._host_ransomware_script.configure(
                server_ip_address=command_opts.server_ip_address, payload=command_opts.payload
            )
        )

    def _command_ransomware_launch(self, payload: C2Packet) -> RequestResponse:
        """
        C2 Command: Ransomware Launch.

        Uses the RansomwareScript's public method .attack() to carry out the
        ransomware attack and uses the .from_bool method to return a RequestResponse

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

    def _command_data_exfiltration(self, payload: C2Packet) -> RequestResponse:
        """
        C2 Command: Data Exfiltration.

        Uses the FTP Client & Server services to perform the data exfiltration.

        This command instructs the C2 Beacon to ssh into the target ip
        and execute a command which causes the FTPClient service to send a

        target file will be moved from the target IP address onto the C2 Beacon's host
        file system.

        However, if no IP is given, then the command will move the target file from this
        machine onto the C2 server. (This logic is performed on the C2)

        :payload C2Packet: The incoming INPUT command.
        :type Masquerade Packet: C2Packet.
        :return: Returns a tuple containing Request Response returned by the Terminal execute method.
        :rtype: Request Response
        """
        if self._host_ftp_server is None:
            self.sys_log.warning(f"{self.name}: C2 Beacon unable to the FTP Server. Unable to resolve command.")
            return RequestResponse(
                status="failure",
                data={"Reason": "Cannot find any instances of both a FTP Server & Client. Are they installed?"},
            )

        command_opts = ExfilOpts.model_validate(payload.payload)

        # Setting up the terminal session and the ftp server
        if not self._set_terminal_session(
            username=command_opts.username, password=command_opts.password, ip_address=command_opts.target_ip_address
        ):
            return RequestResponse(
                status="failure", data={"Reason": "Cannot create a terminal session. Are the credentials correct?"}
            )

        # Using the terminal to start the FTP Client on the remote machine.
        self.terminal_session.execute(command=["service", "start", "FTPClient"])

        # Need to supply to the FTP Client the C2 Beacon's host IP.
        host_network_interfaces = self.software_manager.node.network_interfaces
        local_ip = host_network_interfaces.get(next(iter(host_network_interfaces))).ip_address

        # Creating the FTP creation options.
        ftp_opts = {
            "dest_ip_address": str(local_ip),
            "src_folder_name": command_opts.target_folder_name,
            "src_file_name": command_opts.target_file_name,
            "dest_folder_name": command_opts.exfiltration_folder_name,
            "dest_file_name": command_opts.target_file_name,
        }

        attempt_exfiltration: tuple[bool, RequestResponse] = self._perform_exfiltration(ftp_opts)

        if attempt_exfiltration[0] is False:
            self.sys_log.error(f"{self.name}: File Exfiltration Attempt Failed: {attempt_exfiltration[1].data}")
            return attempt_exfiltration[1]

        # Sending the transferred target data back to the C2 Server to successfully exfiltrate the data out the network.

        return RequestResponse.from_bool(
            self._host_ftp_client.send_file(
                dest_ip_address=self.c2_remote_connection,
                src_folder_name=command_opts.exfiltration_folder_name,  # The Exfil folder is inherited attribute.
                src_file_name=command_opts.target_file_name,
                dest_folder_name=command_opts.exfiltration_folder_name,
                dest_file_name=command_opts.target_file_name,
            )
        )

    def _perform_exfiltration(self, ftp_opts: dict) -> tuple[bool, RequestResponse]:
        """
        Attempts to exfiltrate a target file from a target using the parameters given.

        Uses the current terminal_session to send a command to the
        remote host's FTP Client passing the ExfilOpts as command options.

        This will instruct the FTP client to send the target file to the
        dest_ip_address's destination folder.

        This method assumes that the following:
        1. The self.terminal_session is the remote target.
        2. The target has a functioning FTP Client Service.


        :ExfilOpts: A Pydantic model containing the require configuration options
        :type ExfilOpts: ExfilOpts
        :return: Returns a tuple containing a success boolean and a Request Response..
        :rtype: tuple[bool, RequestResponse
        """
        # Creating the exfiltration folder .
        exfiltration_folder = self.get_exfiltration_folder(ftp_opts.get("dest_folder_name"))

        # Using the terminal to send the target data back to the C2 Beacon.
        exfil_response: RequestResponse = RequestResponse.from_bool(
            self.terminal_session.execute(command=["service", "FTPClient", "send", ftp_opts])
        )

        # Validating that we successfully received the target data.

        if exfil_response.status == "failure":
            self.sys_log.warning(f"{self.name}: Remote connection failure. failed to transfer the target data via FTP.")
            return [False, exfil_response]

        # Target file:
        target_file: str = ftp_opts.get("src_file_name")

        if exfiltration_folder.get_file(target_file) is None:
            self.sys_log.warning(
                f"{self.name}: Unable to locate exfiltrated file on local filesystem. "
                f"Perhaps the file transfer failed?"
            )
            return [
                False,
                RequestResponse(status="failure", data={"reason": "Unable to locate exfiltrated data on file system."}),
            ]

        if self._host_ftp_client is None:
            self.sys_log.warning(f"{self.name}: C2 Beacon unable to the FTP Server. Unable to resolve command.")
            return [
                False,
                RequestResponse(
                    status="failure",
                    data={"Reason": "Cannot find any instances of both a FTP Server & Client. Are they installed?"},
                ),
            ]

        return [
            True,
            RequestResponse(
                status="success",
                data={"Reason": "Located the target file on local file system. Data exfiltration successful."},
            ),
        ]

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
        command_opts = TerminalOpts.model_validate(payload.payload)

        if self._host_terminal is None:
            return RequestResponse(
                status="failure",
                data={"Reason": "Host does not seem to have terminal installed. Unable to resolve command."},
            )

        terminal_output: Dict[int, RequestResponse] = {}

        # Creating a remote terminal session if given an IP Address, otherwise using a local terminal session.
        if not self._set_terminal_session(
            username=command_opts.username, password=command_opts.password, ip_address=command_opts.ip_address
        ):
            return RequestResponse(
                status="failure",
                data={"Reason": "Cannot create a terminal session. Are the credentials correct?"},
            )

        # Converts a singular terminal command: [RequestFormat] into a list with one element [[RequestFormat]]
        # Checks the first element - if this element is a str then there must be multiple commands.
        command_opts.commands = (
            [command_opts.commands] if isinstance(command_opts.commands[0], str) else command_opts.commands
        )

        for index, given_command in enumerate(command_opts.commands):
            # A try catch exception ladder was used but was considered not the best approach
            # as it can end up obscuring visibility of actual bugs (Not the expected ones) and was a temporary solution.
            # TODO: Refactor + add further validation to ensure that a request is correct. (maybe a pydantic method?)
            terminal_output[index] = self.terminal_session.execute(given_command)

        # Reset our remote terminal session.
        self.terminal_session is None
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

    def _confirm_remote_connection(self, timestep: int) -> bool:
        """Checks the suitability of the current C2 Server connection.

        If a connection cannot be confirmed then this method will return false otherwise true.

        :param timestep: The current timestep of the simulation.
        :type timestep: Int
        :return: Returns False if connection was lost. Returns True if connection is active or re-established.
        :rtype bool:
        """
        self.keep_alive_attempted = False  # Resetting keep alive sent.
        if self.keep_alive_inactivity == self.config.keep_alive_frequency:
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
                self.config.keep_alive_frequency,
                self.config.masquerade_protocol,
                self.config.masquerade_port,
            ]
        )
        print(table)
