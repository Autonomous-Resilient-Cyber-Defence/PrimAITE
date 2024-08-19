# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from enum import Enum
from ipaddress import IPv4Address
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field, validate_call

from primaite.interface.request import RequestResponse
from primaite.simulator.file_system.file_system import FileSystem, Folder
from primaite.simulator.network.protocols.masquerade import C2Packet
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application, ApplicationOperatingState
from primaite.simulator.system.core.session_manager import Session
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.ftp.ftp_server import FTPServer
from primaite.simulator.system.services.service import ServiceOperatingState
from primaite.simulator.system.software import SoftwareHealthState


class C2Command(Enum):
    """Enumerations representing the different commands the C2 suite currently supports."""

    RANSOMWARE_CONFIGURE = "Ransomware Configure"
    "Instructs the c2 beacon to configure the ransomware with the provided options."

    RANSOMWARE_LAUNCH = "Ransomware Launch"
    "Instructs the c2 beacon to execute the installed ransomware."

    DATA_EXFILTRATION = "Data Exfiltration"
    "Instructs the c2 beacon to attempt to return a file to the C2 Server."

    TERMINAL = "Terminal"
    "Instructs the c2 beacon to execute the provided terminal command."


class C2Payload(Enum):
    """Represents the different types of command and control payloads."""

    KEEP_ALIVE = "keep_alive"
    """C2 Keep Alive payload. Used by the C2 beacon and C2 Server to confirm their connection."""

    INPUT = "input_command"
    """C2 Input Command payload. Used by the C2 Server to send a command to the c2 beacon."""

    OUTPUT = "output_command"
    """C2 Output Command. Used by the C2 Beacon to send the results of a Input command to the c2 server."""


class AbstractC2(Application, identifier="AbstractC2"):
    """
    An abstract command and control (c2) application.

    Extends the application class to provide base functionality for c2 suite applications
    such as c2 beacons and c2 servers.

    Provides the base methods for handling ``Keep Alive`` connections, configuring masquerade ports and protocols
    as well as providing the abstract methods for sending, receiving and parsing commands.

    Defaults to masquerading as HTTP (Port 80) via TCP.

    Please refer to the Command-&-Control notebook for an in-depth example of the C2 Suite.
    """

    c2_connection_active: bool = False
    """Indicates if the c2 server and c2 beacon are currently connected."""

    c2_remote_connection: IPv4Address = None
    """The IPv4 Address of the remote c2 connection. (Either the IP of the beacon or the server)."""

    c2_session: Session = None
    """The currently active session that the C2 Traffic is using. Set after establishing connection."""

    keep_alive_inactivity: int = 0
    """Indicates how many timesteps since the last time the c2 application received a keep alive."""

    class _C2Opts(BaseModel):
        """A Pydantic Schema for the different C2 configuration options."""

        keep_alive_frequency: int = Field(default=5, ge=1)
        """The frequency at which ``Keep Alive`` packets are sent to the C2 Server from the C2 Beacon."""

        masquerade_protocol: IPProtocol = Field(default=IPProtocol.TCP)
        """The currently chosen protocol that the C2 traffic is masquerading as. Defaults as TCP."""

        masquerade_port: Port = Field(default=Port.HTTP)
        """The currently chosen port that the C2 traffic is masquerading as. Defaults at HTTP."""

    c2_config: _C2Opts = _C2Opts()
    """
    Holds the current configuration settings of the C2 Suite.

    The C2 beacon initialise this class through it's internal configure method.

    The C2 Server when receiving a keep alive will initialise it's own configuration
    to match that of the configuration settings passed in the keep alive through _resolve keep alive.

    If the C2 Beacon is reconfigured then a new keep alive is set which causes the
    C2 beacon to reconfigure it's configuration settings.
    """

    def _craft_packet(
        self, c2_payload: C2Payload, c2_command: Optional[C2Command] = None, command_options: Optional[Dict] = {}
    ) -> C2Packet:
        """
        Creates and returns a Masquerade Packet using the parameters given.

        The packet uses the current c2 configuration and parameters given
        to construct the base networking information such as the masquerade
        protocol/port. Additionally all C2 Traffic packets pass the currently
        in use C2 configuration. This ensures that the all C2 applications
        can keep their configuration in sync.

        :param c2_payload: The type of C2 Traffic ot be sent
        :type c2_payload: C2Payload
        :param c2_command: The C2 command to be sent to the C2 Beacon.
        :type c2_command: C2Command.
        :param command_options: The relevant C2 Beacon parameters.F
        :type command_options: Dict
        :return: Returns the construct C2Packet
        :rtype: C2Packet
        """
        constructed_packet = C2Packet(
            masquerade_protocol=self.c2_config.masquerade_protocol,
            masquerade_port=self.c2_config.masquerade_port,
            keep_alive_frequency=self.c2_config.keep_alive_frequency,
            payload_type=c2_payload,
            command=c2_command,
            payload=command_options,
        )
        return constructed_packet

    def describe_state(self) -> Dict:
        """
        Describe the state of the C2 application.

        :return: A dictionary representation of the C2 application's state.
        :rtype: Dict
        """
        return super().describe_state()

    def __init__(self, **kwargs):
        """Initialise the C2 applications to by default listen for HTTP traffic."""
        kwargs["listen_on_ports"] = {Port.HTTP, Port.FTP, Port.DNS}
        kwargs["port"] = Port.NONE
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    @property
    def _host_ftp_client(self) -> Optional[FTPClient]:
        """Return the FTPClient that is installed C2 Application's host.

        This method confirms that the FTP Client is functional via the ._can_perform_action
        method. If the FTP Client service is not in a suitable state (e.g disabled/pause)
        then this method will return None.

        (The FTP Client service is installed by default)

        :return: An FTPClient object is successful, else None
        :rtype: union[FTPClient, None]
        """
        ftp_client: Union[FTPClient, None] = self.software_manager.software.get("FTPClient")
        if ftp_client is None:
            self.sys_log.warning(f"{self.__class__.__name__}: No FTPClient.  Attempting to install.")
            self.software_manager.install(FTPClient)
            ftp_client = self.software_manager.software.get("FTPClient")

        # Force start if the service is stopped.
        if ftp_client.operating_state == ServiceOperatingState.STOPPED:
            if not ftp_client.start():
                self.sys_log.warning(f"{self.__class__.__name__}: cannot start the FTP Client.")

        if not ftp_client._can_perform_action():
            self.sys_log.error(f"{self.__class__.__name__}: is unable to use the FTP service on its host.")
            return

        return ftp_client

    @property
    def _host_ftp_server(self) -> Optional[FTPServer]:
        """
        Returns the FTP Server that is installed C2 Application's host.

        If a FTPServer is not installed then this method will attempt to install one.

        :return: An FTPServer object is successful, else None
        :rtype: Optional[FTPServer]
        """
        ftp_server: Optional[FTPServer] = self.software_manager.software.get("FTPServer")
        if ftp_server is None:
            self.sys_log.warning(f"{self.__class__.__name__}:No FTPServer installed. Attempting to install FTPServer.")
            self.software_manager.install(FTPServer)
            ftp_server = self.software_manager.software.get("FTPServer")

        # Force start if the service is stopped.
        if ftp_server.operating_state == ServiceOperatingState.STOPPED:
            if not ftp_server.start():
                self.sys_log.warning(f"{self.__class__.__name__}: cannot start the FTP Server.")

        if not ftp_server._can_perform_action():
            self.sys_log.error(f"{self.__class__.__name__}: is unable use FTP Server service on its host.")
            return

        return ftp_server

    # Getter property for the get_exfiltration_folder method ()
    @property
    def _host_file_system(self) -> FileSystem:
        """Return the C2 Host's filesystem (Used for exfiltration related commands) ."""
        host_file_system: FileSystem = self.software_manager.file_system
        if host_file_system is None:
            self.sys_log.error(f"{self.__class__.__name__}: does not seem to have a file system!")
        return host_file_system

    def get_exfiltration_folder(self, folder_name: Optional[str] = "exfiltration_folder") -> Optional[Folder]:
        """Return a folder used for storing exfiltrated data. Otherwise returns None."""
        if self._host_file_system is None:
            return
        exfiltration_folder: Union[Folder, None] = self._host_file_system.get_folder(folder_name)
        if exfiltration_folder is None:
            self.sys_log.info(f"{self.__class__.__name__}: Creating a exfiltration folder.")
            return self._host_file_system.create_folder(folder_name=folder_name)

        return exfiltration_folder

    # Validate call ensures we are only handling Masquerade Packets.
    @validate_call
    def _handle_c2_payload(self, payload: C2Packet, session_id: Optional[str] = None) -> bool:
        """Handles masquerade payloads for both c2 beacons and c2 servers.

        Currently, the C2 application suite can handle the following payloads:

        KEEP ALIVE:
        Establishes or confirms connection from the C2 Beacon to the C2 server.
        Sent by both C2 beacons and C2 Servers.

        INPUT:
        Contains a c2 command which must be executed by the C2 beacon.
        Sent by C2 Servers and received by C2 Beacons.

        OUTPUT:
        Contains the output of a c2 command which must be returned to the C2 Server.
        Sent by C2 Beacons and received by C2 Servers

        The payload is passed to a different method dependant on the payload type.

        :param payload: The C2 Payload to be parsed and handled.
        :return: True if the c2 payload was handled successfully, False otherwise.
        :rtype: Bool
        """
        if payload.payload_type == C2Payload.KEEP_ALIVE:
            self.sys_log.info(f"{self.name} received a KEEP ALIVE payload.")
            return self._handle_keep_alive(payload, session_id)

        elif payload.payload_type == C2Payload.INPUT:
            self.sys_log.info(f"{self.name} received an INPUT COMMAND payload.")
            return self._handle_command_input(payload, session_id)

        elif payload.payload_type == C2Payload.OUTPUT:
            self.sys_log.info(f"{self.name} received an OUTPUT COMMAND payload.")
            return self._handle_command_output(payload)

        else:
            self.sys_log.warning(
                f"{self.name} received an unexpected c2 payload:{payload.payload_type}. Dropping Packet."
            )
            return False

    @abstractmethod
    def _handle_command_output(payload):
        """Abstract Method: Used in C2 server to parse and receive the output of commands sent to the c2 beacon."""
        pass

    @abstractmethod
    def _handle_command_input(payload):
        """Abstract Method: Used in C2 beacon to parse and handle commands received from the c2 server."""
        pass

    @abstractmethod
    def _handle_keep_alive(self, payload: C2Packet, session_id: Optional[str]) -> bool:
        """Abstract Method: Each C2 suite handles ``C2Payload.KEEP_ALIVE`` differently."""
        pass

    # from_network_interface=from_network_interface
    def receive(self, payload: any, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives masquerade packets. Used by both c2 server and c2 beacon.

        Defining the `Receive` method so that the application can receive packets via the session manager.
        These packets are then immediately handed to ._handle_c2_payload.

        :param payload: The Masquerade Packet to be received.
        :type payload: C2Packet
        :param session_id: The transport session_id that the payload is originating from.
        :type session_id: str
        :return: Returns a bool if the traffic was received correctly (See _handle_c2_payload.)
        :rtype: bool
        """
        if not isinstance(payload, C2Packet):
            self.sys_log.warning(f"{self.name}: Payload is not an C2Packet")
            self.sys_log.debug(f"{self.name}: {payload}")
            return False

        return self._handle_c2_payload(payload, session_id)

    def _send_keep_alive(self, session_id: Optional[str]) -> bool:
        """Sends a C2 keep alive payload to the self.remote_connection IPv4 Address.

        Used by both the c2 client and the s2 server for establishing and confirming connection.
        This method also contains some additional validation to ensure that the C2 applications
        are correctly configured before sending any traffic.

        :param session_id: The transport session_id that the payload is originating from.
        :type session_id: str
        :returns: Returns True if a send alive was successfully sent. False otherwise.
        :rtype bool:
        """
        # Checking that the c2 application is capable of connecting to remote.
        # Purely a safety guard clause.
        if not (connection_status := self._check_connection()[0]):
            self.sys_log.warning(
                f"{self.name}: Unable to send keep alive due to c2 connection status: {connection_status}."
            )
            return False

        # Passing our current C2 configuration in remain in sync.
        keep_alive_packet = self._craft_packet(c2_payload=C2Payload.KEEP_ALIVE)

        # Sending the keep alive via the .send() method (as with all other applications.)
        if self.send(
            payload=keep_alive_packet,
            dest_ip_address=self.c2_remote_connection,
            dest_port=self.c2_config.masquerade_port,
            ip_protocol=self.c2_config.masquerade_protocol,
            session_id=session_id,
        ):
            # Setting the keep_alive_sent guard condition to True. This is used to prevent packet storms.
            # This prevents the _resolve_keep_alive method from calling this method again (until the next timestep.)
            self.keep_alive_sent = True
            self.sys_log.info(f"{self.name}: Keep Alive sent to {self.c2_remote_connection}")
            self.sys_log.debug(
                f"{self.name}: Keep Alive sent to {self.c2_remote_connection} "
                f"Masquerade Port: {self.c2_config.masquerade_port} "
                f"Masquerade Protocol: {self.c2_config.masquerade_protocol} "
            )
            return True
        else:
            self.sys_log.warning(
                f"{self.name}: Failed to send a Keep Alive. The node may be unable to access networking resources."
            )
            return False

    def _resolve_keep_alive(self, payload: C2Packet, session_id: Optional[str]) -> bool:
        """
        Parses the Masquerade Port/Protocol within the received Keep Alive packet.

        Used to dynamically set the Masquerade Port and Protocol based on incoming traffic.

        Returns True on successfully extracting and configuring the masquerade port/protocols.
        Returns False otherwise.

        :param payload: The Keep Alive payload received.
        :type payload: C2Packet
        :param session_id: The transport session_id that the payload is originating from.
        :type session_id: str
        :return: True on successful configuration, false otherwise.
        :rtype: bool
        """
        # Validating that they are valid Enums.
        if not isinstance(payload.masquerade_port, Port) or not isinstance(payload.masquerade_protocol, IPProtocol):
            self.sys_log.warning(
                f"{self.name}: Received invalid Masquerade Values within Keep Alive."
                f"Port: {payload.masquerade_port} Protocol: {payload.masquerade_protocol}."
            )
            return False

        # Updating the C2 Configuration attribute.

        self.c2_config.masquerade_port = payload.masquerade_port
        self.c2_config.masquerade_protocol = payload.masquerade_protocol
        self.c2_config.keep_alive_frequency = payload.keep_alive_frequency

        self.sys_log.debug(
            f"{self.name}: C2 Config Resolved Config from Keep Alive:"
            f"Masquerade Port: {self.c2_config.masquerade_port}"
            f"Masquerade Protocol: {self.c2_config.masquerade_protocol}"
            f"Keep Alive Frequency: {self.c2_config.keep_alive_frequency}"
        )

        # This statement is intended to catch on the C2 Application that is listening for connection.
        if self.c2_remote_connection is None:
            self.sys_log.debug(f"{self.name}: Attempting to configure remote C2 connection based off received output.")
            self.c2_remote_connection = IPv4Address(self.c2_session.with_ip_address)

        self.c2_connection_active = True  # Sets the connection to active
        self.keep_alive_inactivity = 0  # Sets the keep alive inactivity to zero

        return True

    def _reset_c2_connection(self) -> None:
        """
        Resets all currently established C2 communications to their default setting.

        This method is called once a C2 application considers their remote connection
        severed and reverts back to default settings. Worth noting that that this will
        revert any non-default configuration that a user/agent may have set.
        """
        self.c2_connection_active = False
        self.c2_session = None
        self.keep_alive_inactivity = 0
        self.keep_alive_frequency = 5
        self.c2_remote_connection = None
        self.c2_config.masquerade_port = Port.HTTP
        self.c2_config.masquerade_protocol = IPProtocol.TCP

    @abstractmethod
    def _confirm_remote_connection(self, timestep: int) -> bool:
        """
        Abstract method - Confirms the suitability of the current C2 application remote connection.

        Each application will have perform different behaviour to confirm the remote connection.

        :return: Boolean. True if remote connection is confirmed, false otherwise.
        """

    def apply_timestep(self, timestep: int) -> None:
        """Apply a timestep to the c2_server & c2 beacon.

        Used to keep track of when the c2 server should consider a beacon dead
        and set it's c2_remote_connection attribute to false.

        1. Each timestep the keep_alive_inactivity is increased.

        2. If the keep alive inactivity eclipses that of the keep alive frequency then another keep alive is sent.

        3. If a keep alive response packet is received then the ``keep_alive_inactivity`` attribute is reset.

        Therefore, if ``keep_alive_inactivity`` attribute is not 0 after a keep alive is sent
        then the connection is considered severed and c2 beacon will shut down.

        :param timestep: The current timestep of the simulation.
        :type timestep: Int
        :return bool: Returns false if connection was lost. Returns True if connection is active or re-established.
        :rtype bool:
        """
        if (
            self.operating_state is ApplicationOperatingState.RUNNING
            and self.health_state_actual is SoftwareHealthState.GOOD
        ):
            self.keep_alive_inactivity += 1
            self._confirm_remote_connection(timestep)
        return super().apply_timestep(timestep=timestep)

    def _check_connection(self) -> tuple[bool, RequestResponse]:
        """
        Validation method: Checks that the C2 application is capable of sending C2 Command input/output.

        Performs a series of connection validation to ensure that the C2 application is capable of
        sending and responding to the remote c2 connection. This method is used to confirm connection
        before carrying out Agent Commands hence why this method also returns a tuple
        containing both a success boolean as well as RequestResponse.

        :return: A tuple containing a boolean True/False and a corresponding Request Response
        :rtype: tuple[bool, RequestResponse]
        """
        if not self._can_perform_network_action():
            self.sys_log.warning(f"{self.name}: Unable to make leverage networking resources. Rejecting Command.")
            return (
                False,
                RequestResponse(
                    status="failure", data={"Reason": "Unable to access networking resources. Unable to send command."}
                ),
            )

        if self.c2_remote_connection is False:
            self.sys_log.warning(f"{self.name}: C2 Application has yet to establish connection. Rejecting command.")
            return (
                False,
                RequestResponse(
                    status="failure",
                    data={"Reason": "C2 Application has yet to establish connection. Unable to send command."},
                ),
            )
        else:
            return (
                True,
                RequestResponse(status="success", data={"Reason": "C2 Application is able to send connections."}),
            )
