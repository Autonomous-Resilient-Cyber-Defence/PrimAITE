# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from enum import Enum
from ipaddress import IPv4Address
from typing import Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict

from primaite import getLogger
from primaite.interface.request import RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.protocols.http import (
    HttpRequestMethod,
    HttpRequestPacket,
    HttpResponsePacket,
    HttpStatusCode,
)
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.web_browser import WebBrowser
from primaite.simulator.system.services.dns.dns_client import DNSClient
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP

_LOGGER = getLogger(__name__)


class ExtendedApplication(Application, identifier="ExtendedApplication"):
    """
    Clone of web browser that uses the extension framework instead of being part of PrimAITE directly.

    The application requests and loads web pages using its domain name and requesting IP addresses using DNS.
    """

    target_url: Optional[str] = None

    domain_name_ip_address: Optional[IPv4Address] = None
    "The IP address of the domain name for the webpage."

    latest_response: Optional[HttpResponsePacket] = None
    """Keeps track of the latest HTTP response."""

    history: List["BrowserHistoryItem"] = []
    """Keep a log of visited websites and information about the visit, such as response code."""

    def __init__(self, **kwargs):
        kwargs["name"] = "ExtendedApplication"
        kwargs["protocol"] = PROTOCOL_LOOKUP["TCP"]
        # default for web is port 80
        if kwargs.get("port") is None:
            kwargs["port"] = PORT_LOOKUP["HTTP"]

        super().__init__(**kwargs)
        self.run()

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        rm.add_request(
            name="execute",
            request_type=RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.get_webpage())
            ),  # noqa
        )

        return rm

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of the WebBrowser.

        :return: A dictionary capturing the current state of the WebBrowser and its child objects.
        """
        state = super().describe_state()
        state["history"] = [hist_item.state() for hist_item in self.history]
        return state

    def get_webpage(self, url: Optional[str] = None) -> bool:
        """
        Retrieve the webpage.

        This should send a request to the web server which also requests for a list of users

        :param: url: The address of the web page the browser requests
        :type: url: str
        """
        url = url or self.target_url
        if not self._can_perform_action():
            return False

        self.num_executions += 1  # trying to connect counts as an execution

        # reset latest response
        self.latest_response = HttpResponsePacket(status_code=HttpStatusCode.NOT_FOUND)

        try:
            parsed_url = urlparse(url)
        except Exception:
            self.sys_log.warning(f"{url} is not a valid URL")
            return False

        # get the IP address of the domain name via DNS
        dns_client: DNSClient = self.software_manager.software.get("DNSClient")
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
                self.sys_log.warning(f"{self.name}: Unable to resolve URL {url}")
                return False

        # create HTTPRequest payload
        payload = HttpRequestPacket(request_method=HttpRequestMethod.GET, request_url=url)

        # send request - As part of the self.send call, a response will be received and stored in the
        # self.latest_response variable
        if self.send(
            payload=payload,
            dest_ip_address=self.domain_name_ip_address,
            dest_port=parsed_url.port if parsed_url.port else PORT_LOOKUP["HTTP"],
        ):
            self.sys_log.info(
                f"{self.name}: Received HTTP {payload.request_method.name} "
                f"Response {payload.request_url} - {self.latest_response.status_code.value}"
            )
            self.history.append(
                WebBrowser.BrowserHistoryItem(
                    url=url,
                    status=self.BrowserHistoryItem._HistoryItemStatus.LOADED,
                    response_code=self.latest_response.status_code,
                )
            )
            return self.latest_response.status_code is HttpStatusCode.OK
        else:
            self.sys_log.warning(f"{self.name}: Error sending Http Packet")
            self.sys_log.debug(f"{self.name}: {payload=}")
            self.history.append(
                WebBrowser.BrowserHistoryItem(
                    url=url, status=self.BrowserHistoryItem._HistoryItemStatus.SERVER_UNREACHABLE
                )
            )
            return False

    def send(
        self,
        payload: HttpRequestPacket,
        dest_ip_address: Optional[IPv4Address] = None,
        dest_port: Optional[int] = PORT_LOOKUP["HTTP"],
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
            self.sys_log.warning(f"{self.name} received a packet that is not an HttpResponsePacket")
            self.sys_log.debug(f"{self.name}: {payload=}")
            return False
        self.sys_log.info(f"{self.name}: Received HTTP {payload.status_code.value}")
        self.latest_response = payload
        return True

    class BrowserHistoryItem(BaseModel):
        """Simple representation of browser history, used for tracking success of web requests to calculate rewards."""

        model_config = ConfigDict(extra="forbid")
        """Error if incorrect specification."""

        url: str
        """The URL that was attempted to be fetched by the browser"""

        class _HistoryItemStatus(Enum):
            NOT_SENT = "NOT_SENT"
            PENDING = "PENDING"
            SERVER_UNREACHABLE = "SERVER_UNREACHABLE"
            LOADED = "LOADED"

        status: _HistoryItemStatus = _HistoryItemStatus.PENDING

        response_code: Optional[HttpStatusCode] = None
        """HTTP response code that was received, or PENDING if a response was not yet received."""

        def state(self) -> Dict:
            """Return the contents of this dataclass as a dict for use with describe_state method."""
            if self.status == self._HistoryItemStatus.LOADED:
                outcome = self.response_code.value
            else:
                outcome = self.status.value
            return {"url": self.url, "outcome": outcome}
