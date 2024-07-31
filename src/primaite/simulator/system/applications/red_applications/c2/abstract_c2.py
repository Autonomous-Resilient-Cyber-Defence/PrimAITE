# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from abc import abstractmethod
from enum import Enum
from ipaddress import IPv4Address
from typing import Dict, Optional

from pydantic import validate_call

from primaite.simulator.network.protocols.masquerade import C2Payload, MasqueradePacket
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application

# TODO:
# Complete C2 Server and C2 Beacon TODOs
# Create test that leverage all the functionality needed for the different TAPs
# Create a .RST doc
# Potentially? A notebook which demonstrates a custom red agent using the c2 server for various means.


class C2Command(Enum):
    """
    Enumerations representing the different commands the C2 suite currently supports.
    """

    RANSOMWARE_CONFIGURE = "Ransomware Configure"
    "Instructs the c2 beacon to configure the ransomware with the provided options."

    RANSOMWARE_LAUNCH = "Ransomware Launch"
    "Instructs the c2 beacon to execute the installed ransomware."

    TERMINAL = "Terminal"
    "Instructs the c2 beacon to execute the provided terminal command."

    # The terminal command should also be able to pass a session which can be used for remote connections.


class AbstractC2(Application):
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
    """The IPv4 Address of the remote c2 connection. (Either the IP of the beacon or the server)"""

    keep_alive_sent: bool = False
    """Indicates if a keep alive has been sent this timestep. Used to prevent packet storms."""

    # We should set the application to NOT_RUNNING if the inactivity count reaches a certain thresh hold.
    keep_alive_inactivity: int = 0
    """Indicates how many timesteps since the last time the c2 application received a keep alive."""

    # These two attributes are set differently in the c2 server and c2 beacon.
    # The c2 server parses the keep alive and sets these accordingly.
    # The c2 beacon will set this attributes upon installation and configuration

    current_masquerade_protocol: Enum = IPProtocol.TCP
    """The currently chosen protocol that the C2 traffic is masquerading as. Defaults as TCP."""

    current_masquerade_port: Enum = Port.HTTP
    """The currently chosen port that the C2 traffic is masquerading as. Defaults at HTTP."""

    # TODO: Move this duplicate method from NMAP class into 'Application' to adhere to DRY principle.
    def _can_perform_network_action(self) -> bool:
        """
        Checks if the C2 application can perform outbound network actions.

        This is done by checking the parent application can_per_action functionality.
        Then checking if there is an enabled NIC that can be used for outbound traffic.

        :return: True if outbound network actions can be performed, otherwise False.
        """
        if not super()._can_perform_action():
            return False

        for nic in self.software_manager.node.network_interface.values():
            if nic.enabled:
                return True
        return False

    def describe_state(self) -> Dict:
        """
        Describe the state of the C2 application.

        :return: A dictionary representation of the C2 application's state.
        :rtype: Dict
        """
        return super().describe_state()

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
            return self._handle_command_input(payload, session_id)

        else:
            self.sys_log.warning(
                f"{self.name} received an unexpected c2 payload:{payload.payload_type}. Dropping Packet."
            )
            return False

    # Abstract method
    # Used in C2 server to prase and receive the output of commands sent to the c2 beacon.
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
        """
        Handles receiving and sending keep alive payloads. This method is only called if we receive a keep alive.

        Returns False if a keep alive was unable to be sent.
        Returns True if a keep alive was successfully sent or already has been sent this timestep.

        :return: True if successfully handled, false otherwise.
        :rtype: Bool
        """
        self.sys_log.info(f"{self.name}: Keep Alive Received from {self.c2_remote_connection}")
        # Using this guard clause to prevent packet storms and recognise that we've achieved a connection.
        if self.keep_alive_sent:
            self.sys_log.info(f"{self.name}: Connection successfully established with {self.c2_remote_connection}")
            self.c2_connection_active = True  # Sets the connection to active
            self.keep_alive_inactivity = 0  # Sets the keep alive inactivity to zero

            # Return early without sending another keep alive and then setting keep alive_sent false for next timestep.
            self.keep_alive_sent = False
            return True

        # If we've reached this part of the method then we've received a keep alive but haven't sent a reply.
        # Therefore we also need to configure the masquerade attributes based off the keep alive sent.
        if not self._resolve_keep_alive(self, payload):
            return False

        # If this method returns true then we have sent successfully sent a keep alive.
        if self._send_keep_alive(self, session_id):
            self.keep_alive_sent = True # Setting the guard clause to true (prevents packet storms.)
            return True

        # Return false if we're unable to send handle the keep alive correctly.
        else:
            return False

    def receive(self, payload: MasqueradePacket, session_id: Optional[str] = None) -> bool:
        """Receives masquerade packets. Used by both c2 server and c2 client.

        :param payload: The Masquerade Packet to be received.
        :param session: The transport session that the payload is originating from.
        """
        return self._handle_c2_payload(payload, session_id)

    def _send_keep_alive(self, session_id: Optional[str]) -> bool:
        """Sends a C2 keep alive payload to the self.remote_connection IPv4 Address."""
        # Checking that the c2 application is capable of performing both actions and has an enabled NIC
        # (Using NOT to improve code readability)
        if self.c2_remote_connection == None:
            self.sys_log.error(f"{self.name}: Unable to Establish connection as the C2 Server's IP Address has not been given.")
        
        if not self._can_perform_network_action():
            self.sys_log.warning(f"{self.name}: Unable to perform network actions.")
            return False

        # We also Pass masquerade protocol/port so that the c2 server can reply on the correct protocol/port.
        # (This also lays the foundations for switching masquerade port/protocols mid episode.)
        keep_alive_packet = MasqueradePacket(
            masquerade_protocol=self.current_masquerade_protocol,
            masquerade_port=self.current_masquerade_port,
            payload_type=C2Payload.KEEP_ALIVE,
        )

        # C2 Server will need to c2_remote_connection after it receives it's first keep alive.
        if self.send(
            self,
            payload=keep_alive_packet,
            dest_ip_address=self.c2_remote_connection,
            port=self.current_masquerade_port,
            protocol=self.current_masquerade_protocol,
            session_id=session_id,
        ):
            self.sys_log.info(f"{self.name}: Keep Alive sent to {self.c2_remote_connection}")
            self.sys_log.debug(f"{self.name}: on {self.current_masquerade_port} via {self.current_masquerade_protocol}")
            self.receive(payload=keep_alive_packet)
            return True
        else:
            self.sys_log.warning(
                f"{self.name}: failed to send a Keep Alive. The node may be unable to access the network."
            )
            return False


    def _resolve_keep_alive(self, payload: MasqueradePacket) -> bool:
        """
        Parses the Masquerade Port/Protocol within the received Keep Alive packet.

        Used to dynamically set the Masquerade Port and Protocol based on incoming traffic.

        Returns True on successfully extracting and configuring the masquerade port/protocols.
        Returns False otherwise.
        
        :param payload: The Keep Alive payload received.
        :type payload: MasqueradePacket
        :return: True on successful configuration, false otherwise.
        :rtype: bool
        """
        # Validating that they are valid Enums.
        if payload.masquerade_port or payload.masquerade_protocol != Enum:
            self.sys_log.warning(f"{self.name}: Received invalid Masquerade type. Port: {type(payload.masquerade_port)} Protocol: {type(payload.masquerade_protocol)}")
            return False
        # TODO: Validation on Ports (E.g only allow HTTP, FTP etc)
        # Potentially compare to IPProtocol & Port children (Same way that abstract TAP does it with kill chains)
        
        # Setting the Ports
        self.current_masquerade_port = payload.masquerade_port
        self.current_masquerade_protocol = payload.masquerade_protocol
        return True