from ipaddress import IPv4Address
from typing import Any, Optional

from primaite.simulator.network.protocols.http import (
    HTTPRequestMethod,
    HTTPRequestPacket,
    HTTPResponsePacket,
    HTTPStatusCode,
)
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.simulator.system.services.service import Service


class WebServerService(Service):
    """Class used to represent a Web Server Service in simulation."""

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
        self.file_system.create_file(file_name="index.html", folder_name="primaite", real=True)

    def _process_http_request(self, payload: HTTPRequestPacket, session_id: Optional[str] = None) -> bool:
        """
        Parse the HTTPRequestPacket.

        :param: payload: Payload containing th HTTPRequestPacket
        :type: payload: HTTPRequestPacket

        :param: session_id: Session id of the http request
        :type: session_id: Optional[str]
        """
        response = HTTPResponsePacket()

        self.sys_log.info(f"{self.name}: Received HTTP {payload.request_method.name} {payload.request_url}")

        # check the type of HTTP request
        if payload.request_method == HTTPRequestMethod.GET:
            response = self._handle_get_request(payload=payload)

        elif payload.request_method == HTTPRequestMethod.POST:
            pass

        else:
            # send a method not allowed response
            response.status_code = HTTPStatusCode.METHOD_NOT_ALLOWED

        # send response to web client
        self.send(payload=response, session_id=session_id)

        # return true if response is OK
        return response.status_code == HTTPStatusCode.OK

    def _handle_get_request(self, payload: HTTPRequestPacket) -> HTTPResponsePacket:
        """
        Handle a GET HTTP request.

        :param: payload: HTTP request payload
        :type: payload: HTTPRequestPacket
        """
        response = HTTPResponsePacket(status_code=HTTPStatusCode.BAD_REQUEST, payload=payload)
        try:
            # get data from DatabaseServer
            db_client: DatabaseClient = self.software_manager.software["DatabaseClient"]
            # get all users
            if db_client.query("SELECT * FROM user;"):
                # query succeeded
                response.status_code = HTTPStatusCode.OK

            return response
        except Exception:
            # something went wrong on the server
            response.status_code = HTTPStatusCode.INTERNAL_SERVER_ERROR
            return response

    def send(
        self,
        payload: HTTPResponsePacket,
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
        # check if the payload is an HTTPPacket
        if not isinstance(payload, HTTPRequestPacket):
            self.sys_log.error("Payload is not an HTTPPacket")
            return False

        return self._process_http_request(payload=payload, session_id=session_id)
