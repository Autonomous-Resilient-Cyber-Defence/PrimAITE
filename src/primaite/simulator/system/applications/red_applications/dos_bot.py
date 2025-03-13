# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from enum import IntEnum
from ipaddress import IPv4Address
from typing import Dict, Optional

from pydantic import Field

from primaite import getLogger
from primaite.game.science import simulate_trial
from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.system.applications.database_client import DatabaseClient
from primaite.utils.validation.ipv4_address import ipv4_validator, IPV4Address
from primaite.utils.validation.port import Port, PORT_LOOKUP, port_validator

_LOGGER = getLogger(__name__)


class DoSAttackStage(IntEnum):
    """Enum representing the different stages of a Denial of Service attack."""

    NOT_STARTED = 0
    "Attack not yet started."

    PORT_SCAN = 1
    "Attack is in discovery stage - checking if provided ip and port are open."

    ATTACKING = 2
    "Denial of Service attack is in progress."

    COMPLETED = 3
    "Attack is completed."


class DoSBot(DatabaseClient, discriminator="dos-bot"):
    """A bot that simulates a Denial of Service attack."""

    class ConfigSchema(DatabaseClient.ConfigSchema):
        """ConfigSchema for DoSBot."""

        type: str = "dos-bot"
        target_ip_address: Optional[IPV4Address] = None
        target_port: Port = PORT_LOOKUP["POSTGRES_SERVER"]
        payload: Optional[str] = None
        repeat: bool = False
        port_scan_p_of_success: float = 0.1
        dos_intensity: float = 1.0
        max_sessions: int = 1000

    config: "DoSBot.ConfigSchema" = Field(default_factory=lambda: DoSBot.ConfigSchema())

    target_ip_address: Optional[IPv4Address] = None
    """IP address of the target service."""

    target_port: Optional[Port] = None
    """Port of the target service."""

    payload: Optional[str] = None
    """Payload to deliver to the target service as part of the denial of service attack."""

    repeat: bool = False
    """If true, the Denial of Service bot will keep performing the attack."""

    attack_stage: DoSAttackStage = DoSAttackStage.NOT_STARTED
    """Current stage of the DoS kill chain."""

    port_scan_p_of_success: float = 0.1
    """Probability of port scanning being sucessful."""

    dos_intensity: float = 1.0
    """How much of the max sessions will be used by the DoS when attacking."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dos-bot"
        self.target_ip_address = self.config.target_ip_address
        self.target_port = self.config.target_port
        self.payload = self.config.payload
        self.repeat = self.config.repeat
        self.port_scan_p_of_success = self.config.port_scan_p_of_success
        self.dos_intensity = self.config.dos_intensity
        self.max_sessions = self.config.max_sessions

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()

        rm.add_request(
            name="execute",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.run())),
        )

        def _configure(request: RequestFormat, context: Dict) -> RequestResponse:
            """
            Configure the DoSBot.

            :param request: List with one element that is a dict of options to pass to the configure method.
            :type request: RequestFormat
            :param context: additional context for resolving this action, currently unused
            :type context: dict
            :return: Request Response object with a success code determining if the configuration was successful.
            :rtype: RequestResponse
            """
            if "target_ip_address" in request[-1]:
                request[-1]["target_ip_address"] = ipv4_validator(request[-1]["target_ip_address"])
            if "target_port" in request[-1]:
                request[-1]["target_port"] = port_validator(request[-1]["target_port"])
            return RequestResponse.from_bool(self.configure(**request[-1]))

        rm.add_request("configure", request_type=RequestType(func=_configure))
        return rm

    def configure(
        self,
        target_ip_address: IPv4Address,
        target_port: Optional[int] = PORT_LOOKUP["POSTGRES_SERVER"],
        payload: Optional[str] = None,
        repeat: bool = False,
        port_scan_p_of_success: float = 0.1,
        dos_intensity: float = 1.0,
        max_sessions: int = 1000,
    ) -> bool:
        """
        Configure the Denial of Service bot.

        :param: target_ip_address: The IP address of the Node containing the target service.
        :param: target_port: The port of the target service. Optional - Default is `PORT_LOOKUP["HTTP"]`
        :param: payload: The payload the DoS Bot will throw at the target service. Optional - Default is `None`
        :param: repeat: If True, the bot will maintain the attack. Optional - Default is `True`
        :param: port_scan_p_of_success: The chance of the port scan being successful. Optional - Default is 0.1 (10%)
        :param: dos_intensity: The intensity of the DoS attack.
            Multiplied with the application's max session - Default is 1.0
        :param: max_sessions: The maximum number of sessions the DoS bot will attack with. Optional - Default is 1000
        :return: Always returns True
        :rtype: bool
        """
        self.target_ip_address = target_ip_address
        self.target_port = target_port
        self.payload = payload
        self.repeat = repeat
        self.port_scan_p_of_success = port_scan_p_of_success
        self.dos_intensity = dos_intensity
        self.max_sessions = max_sessions
        self.sys_log.info(
            f"{self.name}: Configured the {self.name} with {target_ip_address=}, {target_port=}, {payload=}, "
            f"{repeat=}, {port_scan_p_of_success=}, {dos_intensity=}, {max_sessions=}."
        )
        return True

    def run(self) -> bool:
        """Run the Denial of Service Bot."""
        super().run()
        return self._application_loop()

    def _application_loop(self) -> bool:
        """
        The main application loop for the Denial of Service bot.

        The loop goes through the stages of a DoS attack.

        :return: True if the application loop could be executed, False otherwise.
        :rtype: bool
        """
        if not self._can_perform_action():
            return False

        # DoS bot cannot do anything without a target
        if not self.target_ip_address or not self.target_port:
            self.sys_log.warning(
                f"{self.name} is not properly configured. {self.target_ip_address=}, {self.target_port=}"
            )
            return False

        self.clear_connections()
        self._perform_port_scan(p_of_success=self.port_scan_p_of_success)
        self._perform_dos()

        if self.repeat and self.attack_stage is DoSAttackStage.ATTACKING:
            self.attack_stage = DoSAttackStage.NOT_STARTED
        else:
            self.attack_stage = DoSAttackStage.COMPLETED
        return True

    def _perform_port_scan(self, p_of_success: Optional[float] = 0.1):
        """
        Perform a simulated port scan to check for open SQL ports.

        Advances the attack stage to `PORT_SCAN` if successful.

        :param p_of_success: Probability of successful port scan, by default 0.1.
        """
        if self.attack_stage == DoSAttackStage.NOT_STARTED:
            # perform a port scan to identify that the SQL port is open on the server
            if simulate_trial(p_of_success):
                self.sys_log.info(f"{self.name}: Performing port scan")
                # perform the port scan
                port_is_open = True  # Temporary; later we can implement NMAP port scan.
                if port_is_open:
                    self.sys_log.debug(f"{self.name}: ")
                    self.attack_stage = DoSAttackStage.PORT_SCAN

    def _perform_dos(self):
        """
        Perform the Denial of Service attack.

        DoSBot does this by clogging up the available connections to a service.
        """
        if not self.attack_stage == DoSAttackStage.PORT_SCAN:
            return
        self.attack_stage = DoSAttackStage.ATTACKING
        self.server_ip_address = self.target_ip_address
        self.port = self.target_port

        dos_sessions = int(float(self.max_sessions) * self.dos_intensity)
        for i in range(dos_sessions):
            self.connect()

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep to the bot, iterate through the application loop.

        :param timestep: The timestep value to update the bot's state.
        """
        super().apply_timestep(timestep=timestep)
        self._application_loop()
