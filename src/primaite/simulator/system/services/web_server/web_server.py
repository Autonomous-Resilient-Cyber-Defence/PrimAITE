# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from primaite import getLogger
from primaite.simulator.network.protocols.http import (
    HttpRequestMethod,
    HttpRequestPacket,
    HttpResponsePacket,
    HttpStatusCode,
)
from primaite.simulator.system.applications.database_client import DatabaseClientConnection
from primaite.simulator.system.services.service import Service
from primaite.simulator.system.software import SoftwareHealthState
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import Port, PORT_LOOKUP

_LOGGER = getLogger(__name__)


class WebServer(Service):
    """Class used to represent a Web Server Service in simulation."""

    config: "WebServer.ConfigSchema"

    response_codes_this_timestep: List[HttpStatusCode] = []

    class ConfigSchema(Service.ConfigSchema):
        """ConfigSchema for WebServer."""

        type: str = "WEBSERVER"

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state["response_codes_this_timestep"] = [code.value for code in self.response_codes_this_timestep]
        return state

    def pre_timestep(self, timestep: int) -> None:
        """
        Logic to execute at the start of the timestep - clear the observation-related attributes.

        :param timestep: the current timestep in the episode.
        :type timestep: int
        """
        self.response_codes_this_timestep = []
        return super().pre_timestep(timestep)

    def __init__(self, **kwargs):
        kwargs["name"] = "WebServer"
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        # default for web is port 80
        if kwargs.get("port") is None:
            kwargs["port"] = PORT_LOOKUP["HTTP"]

        super().__init__(**kwargs)
        self._install_web_files()
        self.start()
        self.db_connection: Optional[DatabaseClientConnection] = None

    def _install_web_files(self):
        """
        Installs the files hosted by the web service.

        This is usually HTML, CSS, JS or PHP files requested by browsers to display the webpage.
        """
        # index HTML main file
        self.file_system.create_file(file_name="index.html", folder_name="primaite")

    def _process_http_request(self, payload: HttpRequestPacket, session_id: Optional[str] = None) -> bool:
        """
        Parse the HttpRequestPacket.

        :param: payload: Payload containing th HttpRequestPacket
        :type: payload: HttpRequestPacket

        :param: session_id: Session id of the http request
        :type: session_id: Optional[str]
        """
        response = HttpResponsePacket()

        self.sys_log.info(f"{self.name}: Received HTTP {payload.request_method.name} {payload.request_url}")

        # check the type of HTTP request
        if payload.request_method == HttpRequestMethod.GET:
            response = self._handle_get_request(payload=payload)

        elif payload.request_method == HttpRequestMethod.POST:
            pass

        else:
            # send a method not allowed response
            response.status_code = HttpStatusCode.METHOD_NOT_ALLOWED

        # send response to web client
        self.send(payload=response, session_id=session_id)

        # return true if response is OK
        self.response_codes_this_timestep.append(response.status_code)
        return response.status_code == HttpStatusCode.OK

    def _handle_get_request(self, payload: HttpRequestPacket) -> HttpResponsePacket:
        """
        Handle a GET HTTP request.

        :param: payload: HTTP request payload
        :type: payload: HttpRequestPacket
        """
        response = HttpResponsePacket(status_code=HttpStatusCode.NOT_FOUND, payload=payload)
        try:
            parsed_url = urlparse(payload.request_url)
            path = parsed_url.path.strip("/")

            if len(path) < 1:
                # query succeeded
                response.status_code = HttpStatusCode.OK

            if path.startswith("users"):
                # get data from DatabaseServer
                # get all users
                if not self.db_connection:
                    self._establish_db_connection()

                if self.db_connection.query("SELECT"):
                    # query succeeded
                    self.set_health_state(SoftwareHealthState.GOOD)
                    response.status_code = HttpStatusCode.OK
                else:
                    self.set_health_state(SoftwareHealthState.COMPROMISED)

            return response
        except Exception:  # TODO: refactor this. Likely to cause silent bugs. (ADO ticket #2345 )
            # something went wrong on the server
            response.status_code = HttpStatusCode.INTERNAL_SERVER_ERROR
            return response

    def _establish_db_connection(self) -> None:
        """Establish a connection to db."""
        db_client = self.software_manager.software.get("DatabaseClient")
        self.db_connection: DatabaseClientConnection = db_client.get_new_connection()

    def send(
        self,
        payload: HttpResponsePacket,
        session_id: Optional[str] = None,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = None,
        **kwargs,
    ) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param: payload: The payload to send.
        :param: session_id: The id of the session
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.

        :return: True if successful, False otherwise.
        """
        self.sys_log.info(f"{self.name}: Sending HTTP Response {payload.status_code}")

        return super().send(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id, **kwargs
        )

    def receive(
        self,
        payload: Any,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Receives a payload from the SessionManager.

        :param: payload: The payload to send.
        :param: session_id: The id of the session. Optional.
        """
        if not super().receive(payload=payload, session_id=session_id, **kwargs):
            return False

        # check if the payload is an HTTPPacket
        if not isinstance(payload, HttpRequestPacket):
            self.sys_log.warning(f"{self.name}: Payload is not an HTTPPacket")
            self.sys_log.debug(f"{self.name}: {payload}")
            return False

        return self._process_http_request(payload=payload, session_id=session_id)
