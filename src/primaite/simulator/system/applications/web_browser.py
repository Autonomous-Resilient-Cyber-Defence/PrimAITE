from ipaddress import IPv4Address
from typing import Dict, Optional
from urllib.parse import urlparse

from primaite.simulator.network.protocols.http import HTTPRequestMethod, HTTPRequestPacket, HTTPResponsePacket
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.services.dns.dns_client import DNSClient


class WebBrowser(Application):
    """
    Represents a web browser in the simulation environment.

    The application requests and loads web pages using its domain name and requesting IP addresses using DNS.
    """

    domain_name_ip_address: Optional[IPv4Address] = None
    "The IP address of the domain name for the webpage."

    latest_response: HTTPResponsePacket = None
    """Keeps track of the latest HTTP response."""

    def __init__(self, **kwargs):
        kwargs["name"] = "WebBrowser"
        kwargs["protocol"] = IPProtocol.TCP
        # default for web is port 80
        if kwargs.get("port") is None:
            kwargs["port"] = Port.HTTP

        super().__init__(**kwargs)
        self.run()

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of the WebBrowser.

        :return: A dictionary capturing the current state of the WebBrowser and its child objects.
        """
        pass

    def reset_component_for_episode(self, episode: int):
        """
        Resets the Application component for a new episode.

        This method ensures the Application is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues.
        """
        self.domain_name_ip_address = None
        self.latest_response = None

    def get_webpage(self, url: str) -> bool:
        """
        Retrieve the webpage.

        This should send a request to the web server which also requests for a list of users

        :param: url: The address of the web page the browser requests
        :type: url: str
        """
        # reset latest response
        self.latest_response = None

        try:
            parsed_url = urlparse(url)
        except Exception:
            self.sys_log.error(f"{url} is not a valid URL")
            return False

        # get the IP address of the domain name via DNS
        dns_client: DNSClient = self.software_manager.software["DNSClient"]

        domain_exists = dns_client.check_domain_exists(target_domain=parsed_url.hostname)

        # if domain does not exist, the request fails
        if not domain_exists:
            return False

        # set current domain name IP address
        self.domain_name_ip_address = dns_client.dns_cache[parsed_url.hostname]

        # create HTTPRequest payload
        payload = HTTPRequestPacket(request_method=HTTPRequestMethod.GET, request_url=url)

        # send request
        return self.send(
            payload=payload,
            dest_ip_address=self.domain_name_ip_address,
            dest_port=parsed_url.port if parsed_url.port else Port.HTTP,
        )

    def send(
        self,
        payload: HTTPRequestPacket,
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

    def receive(self, payload: HTTPResponsePacket, session_id: Optional[str] = None, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        :param payload: The payload to be sent.
        :param session_id: The Session ID the payload is to originate from. Optional.
        :return: True if successful, False otherwise.
        """
        if not isinstance(payload, HTTPResponsePacket):
            self.sys_log.error(f"{self.name} received a packet that is not an HTTPResponsePacket")
            return False
        self.sys_log.info(f"{self.name}: Received HTTP {payload.status_code.value}")
        self.latest_response = payload
        return True
