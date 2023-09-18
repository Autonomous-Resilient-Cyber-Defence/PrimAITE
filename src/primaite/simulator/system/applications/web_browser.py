from ipaddress import IPv4Address
from typing import Any, Dict, Optional

from primaite.simulator.system.applications.application import Application


class WebBrowser(Application):
    """
    Represents a web browser in the simulation environment.

    The application requests and loads web pages using its domain name and requesting IP addresses using DNS.
    """

    domain_name: str
    "The domain name of the webpage."
    domain_name_ip_address: Optional[IPv4Address]
    "The IP address of the domain name for the webpage."
    history: Dict[str]
    "A dict that stores all of the previous domain names."

    def reset_component_for_episode(self, episode: int):
        """
        Resets the Application component for a new episode.

        This method ensures the Application is ready for a new episode, including resetting any
        stateful properties or statistics, and clearing any message queues.
        """
        self.domain_name = ""
        self.domain_name_ip_address = None
        self.history = {}

    def send(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Sends a payload to the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to send.
        :return: True if successful, False otherwise.
        """
        pass

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Receives a payload from the SessionManager.

        The specifics of how the payload is processed and whether a response payload
        is generated should be implemented in subclasses.

        :param payload: The payload to receive.
        :return: True if successful, False otherwise.
        """
        pass
