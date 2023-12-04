from ipaddress import IPv4Address
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from primaite import getLogger
from primaite.simulator.network.protocols.http import (
    HttpRequestMethod,
    HttpRequestPacket,
    HttpResponsePacket,
    HttpStatusCode,
)
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.service import Service

_LOGGER = getLogger(__name__)


class WebServer(Service):
    """Class used to represent a Web Server Service in simulation."""

    last_response_status_code: Optional[HttpStatusCode] = None

    def set_original_state(self):
        """Sets the original state."""
        _LOGGER.debug(f"Setting WebServer original state on node {self.software_manager.node.hostname}")
        super().set_original_state()
        vals_to_include = {"last_response_status_code"}
        self._original_state.update(self.model_dump(include=vals_to_include))

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        _LOGGER.debug(f"Resetting WebServer state on node {self.software_manager.node.hostname}")
        super().reset_component_for_episode(episode)

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state["last_response_status_code"] = (
            self.last_response_status_code.value if isinstance(self.last_response_status_code, HttpStatusCode) else None
        )
        return state

    def __init__(self, **kwargs):
        kwargs["name"] = "WebServer"
        kwargs["protocol"] = IPProtocol.TCP
        # default for web is port 80
        if kwargs.get("port") is None:
            kwargs["port"] = Port.HTTP

        super().__init__(**kwargs)
        self._install_web_files()
        self.start()

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
        self.last_response_status_code = response.status_code
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
                db_client: DatabaseClient = self.software_manager.software.get("DatabaseClient")
                # get all users
                if db_client.query("SELECT"):
                    # query succeeded
                    response.status_code = HttpStatusCode.OK

            return response
        except Exception:
            # something went wrong on the server
            response.status_code = HttpStatusCode.INTERNAL_SERVER_ERROR
            return response

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
            self.sys_log.error("Payload is not an HTTPPacket")
            return False

        return self._process_http_request(payload=payload, session_id=session_id)
