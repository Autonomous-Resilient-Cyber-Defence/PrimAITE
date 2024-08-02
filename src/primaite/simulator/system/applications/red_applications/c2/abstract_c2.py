# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from enum import Enum
from ipaddress import IPv4Address
from typing import Dict, Optional

from pydantic import validate_call

from primaite.simulator.network.protocols.masquerade import MasqueradePacket
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.core.session_manager import Session

# TODO:
# Create test that leverage all the functionality needed for the different TAPs
# Create a .RST doc
# Potentially? A notebook which demonstrates a custom red agent using the c2 server for various means.


class C2Command(Enum):
    """Enumerations representing the different commands the C2 suite currently supports."""

    RANSOMWARE_CONFIGURE = "Ransomware Configure"
    "Instructs the c2 beacon to configure the ransomware with the provided options."

    RANSOMWARE_LAUNCH = "Ransomware Launch"
    "Instructs the c2 beacon to execute the installed ransomware."

    TERMINAL = "Terminal"
    "Instructs the c2 beacon to execute the provided terminal command."

    # The terminal command should also be able to pass a session which can be used for remote connections.


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
    """

    c2_connection_active: bool = False
    """Indicates if the c2 server and c2 beacon are currently connected."""

    c2_remote_connection: IPv4Address = None
    """The IPv4 Address of the remote c2 connection. (Either the IP of the beacon or the server)."""

    # These two attributes are set differently in the c2 server and c2 beacon.
    # The c2 server parses the keep alive and sets these accordingly.
    # The c2 beacon will set this attributes upon installation and configuration

    current_masquerade_protocol: IPProtocol = IPProtocol.TCP
    """The currently chosen protocol that the C2 traffic is masquerading as. Defaults as TCP."""

    current_masquerade_port: Port = Port.HTTP
    """The currently chosen port that the C2 traffic is masquerading as. Defaults at HTTP."""

    current_c2_session: Session = None
    """The currently active session that the C2 Traffic is using. Set after establishing connection."""

    def describe_state(self) -> Dict:
        """
        Describe the state of the C2 application.

        :return: A dictionary representation of the C2 application's state.
        :rtype: Dict
        """
        return super().describe_state()

    # TODO: Update this post application/services requiring to listen to multiple ports
    def __init__(self, **kwargs):
        """Initialise the C2 applications to by default listen for HTTP traffic."""
        kwargs["port"] = Port.HTTP  # TODO: Update this post application/services requiring to listen to multiple ports
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)

    # Validate call ensures we are only handling Masquerade Packets.
    @validate_call
    def _handle_c2_payload(self, payload: MasqueradePacket, session_id: Optional[str] = None) -> bool:
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

    # Abstract method
    # Used in C2 server to parse and receive the output of commands sent to the c2 beacon.
    @abstractmethod
    def _handle_command_output(payload):
        """Abstract Method: Used in C2 server to prase and receive the output of commands sent to the c2 beacon."""
        pass

    # Abstract method
    # Used in C2 beacon to parse and handle commands received from the c2 server.
    @abstractmethod
    def _handle_command_input(payload):
        """Abstract Method: Used in C2 beacon to parse and handle commands received from the c2 server."""
        pass

    def _handle_keep_alive(self, payload: MasqueradePacket, session_id: Optional[str]) -> bool:
        """Abstract Method: The C2 Server and the C2 Beacon handle the KEEP ALIVEs differently."""

    # from_network_interface=from_network_interface
    def receive(self, payload: MasqueradePacket, session_id: Optional[str] = None, **kwargs) -> bool:
        """Receives masquerade packets. Used by both c2 server and c2 beacon.

        Defining the `Receive` method so that the application can receive packets via the session manager.
        These packets are then immediately handed to ._handle_c2_payload.

        :param payload: The Masquerade Packet to be received.
        :type payload: MasqueradePacket
        :param session_id: The transport session_id that the payload is originating from.
        :type session_id: str
        """
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
        # Checking that the c2 application is capable of performing both actions and has an enabled NIC
        # (Using NOT to improve code readability)
        if self.c2_remote_connection is None:
            self.sys_log.error(
                f"{self.name}: Unable to Establish connection as the C2 Server's IP Address has not been given."
            )

        if not self._can_perform_network_action():
            self.sys_log.warning(f"{self.name}: Unable to perform network actions.")
            return False

        # We also Pass masquerade proto`col/port so that the c2 server can reply on the correct protocol/port.
        # (This also lays the foundations for switching masquerade port/protocols mid episode.)
        keep_alive_packet = MasqueradePacket(
            masquerade_protocol=self.current_masquerade_protocol,
            masquerade_port=self.current_masquerade_port,
            payload_type=C2Payload.KEEP_ALIVE,
            command=None,
        )
        # C2 Server will need to configure c2_remote_connection after it receives it's first keep alive.
        if self.send(
            payload=keep_alive_packet,
            dest_ip_address=self.c2_remote_connection,
            dest_port=self.current_masquerade_port,
            ip_protocol=self.current_masquerade_protocol,
            session_id=session_id,
        ):
            self.keep_alive_sent = True
            self.sys_log.info(f"{self.name}: Keep Alive sent to {self.c2_remote_connection}")
            self.sys_log.debug(f"{self.name}: on {self.current_masquerade_port} via {self.current_masquerade_protocol}")
            return True
        else:
            self.sys_log.warning(
                f"{self.name}: failed to send a Keep Alive. The node may be unable to access the ``network."
            )
            return False

    def _resolve_keep_alive(self, payload: MasqueradePacket, session_id: Optional[str]) -> bool:
        """
        Parses the Masquerade Port/Protocol within the received Keep Alive packet.

        Used to dynamically set the Masquerade Port and Protocol based on incoming traffic.

        Returns True on successfully extracting and configuring the masquerade port/protocols.
        Returns False otherwise.

        :param payload: The Keep Alive payload received.
        :type payload: MasqueradePacket
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

        # TODO: Validation on Ports (E.g only allow HTTP, FTP etc)
        # Potentially compare to IPProtocol & Port children? Depends on how listening on multiple ports is implemented.

        # Setting the Ports
        self.current_masquerade_port = payload.masquerade_port
        self.current_masquerade_protocol = payload.masquerade_protocol

        # This statement is intended to catch on the C2 Application that is listening for connection. (C2 Beacon)
        if self.c2_remote_connection is None:
            self.sys_log.debug(f"{self.name}: Attempting to configure remote C2 connection based off received output.")
            self.c2_remote_connection = self.current_c2_session.with_ip_address

        self.c2_connection_active = True  # Sets the connection to active
        self.keep_alive_inactivity = 0  # Sets the keep alive inactivity to zero

        return True
