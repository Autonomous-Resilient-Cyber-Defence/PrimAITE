from enum import IntEnum
from ipaddress import IPv4Address
from typing import Optional

from primaite.game.science import simulate_trial
from primaite.simulator.system.applications.application import ApplicationOperatingState
from primaite.simulator.system.applications.database_client import DatabaseClient


class DataManipulationAttackStage(IntEnum):
    """
    Enumeration representing different stages of a data manipulation attack.

    This enumeration defines the various stages a data manipulation attack can be in during its lifecycle in the
    simulation. Each stage represents a specific phase in the attack process.
    """

    NOT_STARTED = 0
    "Indicates that the attack has not started yet."
    LOGON = 1
    "The stage where logon procedures are simulated."
    PORT_SCAN = 2
    "Represents the stage of performing a horizontal port scan on the target."
    ATTACKING = 3
    "Stage of actively attacking the target."
    COMPLETE = 4
    "Indicates the attack has been successfully completed."
    FAILED = 5
    "Signifies that the attack has failed."


class DataManipulationBot(DatabaseClient):
    """A bot that simulates a script which performs a SQL injection attack."""

    server_ip_address: Optional[IPv4Address] = None
    payload: Optional[str] = None
    server_password: Optional[str] = None
    port_scan_p_of_success: float = 0.1
    data_manipulation_p_of_success: float = 0.1

    attack_stage: DataManipulationAttackStage = DataManipulationAttackStage.NOT_STARTED
    repeat: bool = False
    "Whether to repeat attacking once finished."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "DataManipulationBot"

    def configure(
        self,
        server_ip_address: IPv4Address,
        server_password: Optional[str] = None,
        payload: Optional[str] = None,
        port_scan_p_of_success: float = 0.1,
        data_manipulation_p_of_success: float = 0.1,
        repeat: bool = False,
    ):
        """
        Configure the DataManipulatorBot to communicate with a DatabaseService.

        :param server_ip_address: The IP address of the Node the DatabaseService is on.
        :param server_password: The password on the DatabaseService.
        :param payload: The data manipulation query payload.
        :param port_scan_p_of_success: The probability of success for the port scan stage.
        :param data_manipulation_p_of_success: The probability of success for the data manipulation stage.
        :param repeat: Whether to repeat attacking once finished.
        """
        self.server_ip_address = server_ip_address
        self.payload = payload
        self.server_password = server_password
        self.port_scan_p_of_success = port_scan_p_of_success
        self.data_manipulation_p_of_success = data_manipulation_p_of_success
        self.repeat = repeat
        self.sys_log.info(
            f"{self.name}: Configured the {self.name} with {server_ip_address=}, {payload=}, {server_password=}, "
            f"{repeat=}."
        )

    def _logon(self):
        """
        Simulate the logon process as the initial stage of the attack.

        Advances the attack stage to `LOGON` if successful.
        """
        if self.attack_stage == DataManipulationAttackStage.NOT_STARTED:
            # Bypass this stage as we're not dealing with logon for now
            self.sys_log.info(f"{self.name}: ")
            self.attack_stage = DataManipulationAttackStage.LOGON

    def _perform_port_scan(self, p_of_success: Optional[float] = 0.1):
        """
        Perform a simulated port scan to check for open SQL ports.

        Advances the attack stage to `PORT_SCAN` if successful.

        :param p_of_success: Probability of successful port scan, by default 0.1.
        """
        if self.attack_stage == DataManipulationAttackStage.LOGON:
            # perform a port scan to identify that the SQL port is open on the server
            if simulate_trial(p_of_success):
                self.sys_log.info(f"{self.name}: Performing port scan")
                # perform the port scan
                port_is_open = True  # Temporary; later we can implement NMAP port scan.
                if port_is_open:
                    self.sys_log.info(f"{self.name}: ")
                    self.attack_stage = DataManipulationAttackStage.PORT_SCAN

    def _perform_data_manipulation(self, p_of_success: Optional[float] = 0.1):
        """
        Execute the data manipulation attack on the target.

        Advances the attack stage to `COMPLETE` if successful, or 'FAILED' if unsuccessful.

        :param p_of_success: Probability of successfully performing data manipulation, by default 0.1.
        """
        if self.attack_stage == DataManipulationAttackStage.PORT_SCAN:
            # perform the actual data manipulation attack
            if simulate_trial(p_of_success):
                self.sys_log.info(f"{self.name}: Performing data manipulation")
                # perform the attack
                if not self.connected:
                    self.connect()
                    if self.connected:
                        self.query(self.payload)
                        self.sys_log.info(f"{self.name} payload delivered: {self.payload}")
                        attack_successful = True
                        if attack_successful:
                            self.sys_log.info(f"{self.name}: Data manipulation successful")
                            self.attack_stage = DataManipulationAttackStage.COMPLETE
                        else:
                            self.sys_log.info(f"{self.name}: Data manipulation failed")
                            self.attack_stage = DataManipulationAttackStage.FAILED

    def execute(self):
        """
        Execute the Data Manipulation Bot.

        Calls the parent classes execute method before starting the application loop.
        """
        super().execute()
        self._application_loop()

    def _application_loop(self):
        """
        The main application loop of the bot, handling the attack process.

        This is the core loop where the bot sequentially goes through the stages of the attack.
        """
        if self.operating_state != ApplicationOperatingState.RUNNING:
            return
        if self.server_ip_address and self.payload and self.operating_state:
            self.sys_log.info(f"{self.name}: Running")
            self._logon()
            self._perform_port_scan(p_of_success=self.execution_definition.port_scan_p_of_success)
            self._perform_data_manipulation(p_of_success=self.execution_definition.data_manipulation_p_of_success)

            if self.repeat and self.attack_stage in (
                DataManipulationAttackStage.COMPLETE,
                DataManipulationAttackStage.FAILED,
            ):
                self.attack_stage = DataManipulationAttackStage.NOT_STARTED
        else:
            self.sys_log.error(f"{self.name}: Failed to start as it requires both a target_ip_address and payload.")

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep to the bot, triggering the application loop.

        :param timestep: The timestep value to update the bot's state.
        """
        self._application_loop()
