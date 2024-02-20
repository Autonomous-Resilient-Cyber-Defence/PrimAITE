from enum import IntEnum
from ipaddress import IPv4Address
from typing import Optional

from primaite import getLogger
from primaite.game.science import simulate_trial
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.database_client import DatabaseClient

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


class DoSBot(DatabaseClient, Application):
    """A bot that simulates a Denial of Service attack."""

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
        self.name = "DoSBot"
        self.max_sessions = 1000  # override normal max sessions

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        _LOGGER.debug(f"Resetting {self.name} state on node {self.software_manager.node.hostname}")
        super().reset_component_for_episode(episode)

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()

        rm.add_request(name="execute", request_type=RequestType(func=lambda request, context: self.run()))

        return rm

    def configure(
        self,
        target_ip_address: IPv4Address,
        target_port: Optional[Port] = Port.POSTGRES_SERVER,
        payload: Optional[str] = None,
        repeat: bool = False,
        port_scan_p_of_success: float = 0.1,
        dos_intensity: float = 1.0,
        max_sessions: int = 1000,
    ):
        """
        Configure the Denial of Service bot.

        :param: target_ip_address: The IP address of the Node containing the target service.
        :param: target_port: The port of the target service. Optional - Default is `Port.HTTP`
        :param: payload: The payload the DoS Bot will throw at the target service. Optional - Default is `None`
        :param: repeat: If True, the bot will maintain the attack. Optional - Default is `True`
        :param: port_scan_p_of_success: The chance of the port scan being sucessful. Optional - Default is 0.1 (10%)
        :param: dos_intensity: The intensity of the DoS attack.
            Multiplied with the application's max session - Default is 1.0
        :param: max_sessions: The maximum number of sessions the DoS bot will attack with. Optional - Default is 1000
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

    def run(self):
        """Run the Denial of Service Bot."""
        super().run()
        self._application_loop()

    def _application_loop(self):
        """
        The main application loop for the Denial of Service bot.

        The loop goes through the stages of a DoS attack.
        """
        if not self._can_perform_action():
            return

        # DoS bot cannot do anything without a target
        if not self.target_ip_address or not self.target_port:
            self.sys_log.error(
                f"{self.name} is not properly configured. {self.target_ip_address=}, {self.target_port=}"
            )
            return

        self.clear_connections()
        self._perform_port_scan(p_of_success=self.port_scan_p_of_success)
        self._perform_dos()

        if self.repeat and self.attack_stage is DoSAttackStage.ATTACKING:
            self.attack_stage = DoSAttackStage.NOT_STARTED
        else:
            self.attack_stage = DoSAttackStage.COMPLETED

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
                    self.sys_log.info(f"{self.name}: ")
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
        self._application_loop()
