from ipaddress import IPv4Address
from typing import Dict, Optional
from urllib.parse import urlparse

from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.protocols.http import (
    HttpRequestMethod,
    HttpRequestPacket,
    HttpResponsePacket,
    HttpStatusCode,
)
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.services.dns.dns_client import DNSClient


class WebBrowser(Application):
    """
    Represents a web browser in the simulation environment.

    The application requests and loads web pages using its domain name and requesting IP addresses using DNS.
    """

    target_url: Optional[str] = None

    domain_name_ip_address: Optional[IPv4Address] = None
    "The IP address of the domain name for the webpage."

    latest_response: Optional[HttpResponsePacket] = None
    """Keeps track of the latest HTTP response."""

    def __init__(self, **kwargs):
        kwargs["name"] = "WebBrowser"
        kwargs["protocol"] = IPProtocol.TCP
        # default for web is port 80
        if kwargs.get("port") is None:
            kwargs["port"] = Port.HTTP

        super().__init__(**kwargs)
        self.set_original_state()
        self.run()

    def set_original_state(self):
        """Sets the original state."""
        super().set_original_state()
        vals_to_include = {"target_url", "domain_name_ip_address", "latest_response"}
        self._original_state.update(self.model_dump(include=vals_to_include))

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()
        rm.add_request(
            name="execute", request_type=RequestType(func=lambda request, context: self.get_webpage())  # noqa
        )

        return rm

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of the WebBrowser.

        :return: A dictionary capturing the current state of the WebBrowser and its child objects.
        """
        state = super().describe_state()
        state["last_response_status_code"] = self.latest_response.status_code if self.latest_response else None

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""

    def get_webpage(self) -> bool:
        """
        Retrieve the webpage.

        This should send a request to the web server which also requests for a list of users

        :param: url: The address of the web page the browser requests
        :type: url: str
        """
        url = self.target_url
        if not self._can_perform_action():
            return False

        # reset latest response
        self.latest_response = HttpResponsePacket(status_code=HttpStatusCode.NOT_FOUND)

        try:
            parsed_url = urlparse(url)
        except Exception:
            self.sys_log.error(f"{url} is not a valid URL")
            return False

        # get the IP address of the domain name via DNS
        dns_client: DNSClient = self.software_manager.software["DNSClient"]
        domain_exists = dns_client.check_domain_exists(target_domain=parsed_url.hostname)

        # if domain does not exist, the request fails
        if domain_exists:
            # set current domain name IP address
            self.domain_name_ip_address = dns_client.dns_cache[parsed_url.hostname]
        else:
            # check if url is an ip address
            try:
                self.domain_name_ip_address = IPv4Address(parsed_url.hostname)
            except Exception:
                # unable to deal with this request
                self.sys_log.error(f"{self.name}: Unable to resolve URL {url}")
                return False

        # create HTTPRequest payload
        payload = HttpRequestPacket(request_method=HttpRequestMethod.GET, request_url=url)

        # send request
        if self.send(
            payload=payload,
            dest_ip_address=self.domain_name_ip_address,
            dest_port=parsed_url.port if parsed_url.port else Port.HTTP,
        ):
            self.sys_log.info(
                f"{self.name}: Received HTTP {payload.request_method.name} "
                f"Response {payload.request_url} - {self.latest_response.status_code.value}"
            )
            return self.latest_response.status_code is HttpStatusCode.OK
        else:
            self.sys_log.error(f"Error sending Http Packet {str(payload)}")
            return False

    def send(
        self,
        payload: HttpRequestPacket,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[Port] = Port.HTTP,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Sends a payload to the SessionManager.

        :param payload: The payload to be sent.
        :param dest_ip_address: The ip address of the payload destination.
        :param dest_port: The port of the payload destination.
        :param session_id: The Session ID the payload is to originate from. Optional.

        :return: True if successful, False otherwise.
        """
        self.sys_log.info(f"{self.name}: Sending HTTP {payload.request_method.name} {payload.request_url}")

        return super().send(
            payload=payload, dest_ip_address=dest_ip_address, dest_port=dest_port, session_id=session_id, **kwargs
        )

    def receive(self, payload: HttpResponsePacket, session_id: Optional[str] = None, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload is to originate from. Optional.
        :return: True if successful, False otherwise.
        """
        if not isinstance(payload, HttpResponsePacket):
            self.sys_log.error(f"{self.name} received a packet that is not an HttpResponsePacket")
            return False
        self.sys_log.info(f"{self.name}: Received HTTP {payload.status_code.value}")
        self.latest_response = payload
        return True
