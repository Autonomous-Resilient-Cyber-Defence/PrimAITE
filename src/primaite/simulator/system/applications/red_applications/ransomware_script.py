from enum import IntEnum
from ipaddress import IPv4Address
from typing import Dict, Optional

from primaite.game.science import simulate_trial
from primaite.interface.request import RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.database_client import DatabaseClient


class RansomwareAttackStage(IntEnum):
    """
    Enumeration representing different attack stages of the ransomware script.

    This enumeration defines the various stages a data manipulation attack can be in during its lifecycle
    in the simulation.
    Each stage represents a specific phase in the attack process.
    """

    NOT_STARTED = 0
    "Indicates that the attack has not started yet."
    DOWNLOAD = 1
    "Installing the Encryption Script - Testing"
    INSTALL = 2
    "The stage where logon procedures are simulated."
    ACTIVATE = 3
    "Operating Status Changes"
    PROPAGATE = 4
    "Represents the stage of performing a horizontal port scan on the target."
    COMMAND_AND_CONTROL = 5
    "Represents the stage of setting up a rely C2 Beacon (Not Implemented)"
    PAYLOAD = 6
    "Stage of actively attacking the target."
    SUCCEEDED = 7
    "Indicates the attack has been successfully completed."
    FAILED = 8
    "Signifies that the attack has failed."


class RansomwareScript(Application):
    """Ransomware Kill Chain - Designed to be used by the TAP001 Agent on the example layout Network.

    :ivar payload: The attack stage query payload. (Default Corrupt)
    :ivar target_scan_p_of_success: The probability of success for the target scan stage.
    :ivar c2_beacon_p_of_success: The probability of success for the c2_beacon stage
    :ivar ransomware_encrypt_p_of_success: The probability of success for the ransomware 'attack' (encrypt) stage.
    :ivar repeat: Whether to repeat attacking once finished.
    """

    server_ip_address: Optional[IPv4Address] = None
    """IP address of node which hosts the database."""
    server_password: Optional[str] = None
    """Password required to access the database."""
    payload: Optional[str] = "ENCRYPT"
    "Payload String for the payload stage"
    target_scan_p_of_success: float = 0.9
    "Probability of the target scan succeeding: Default 0.9"
    c2_beacon_p_of_success: float = 0.9
    "Probability of the c2 beacon setup stage succeeding: Default 0.9"
    ransomware_encrypt_p_of_success: float = 0.9
    "Probability of the ransomware attack succeeding: Default 0.9"
    repeat: bool = False
    "If true, the Denial of Service bot will keep performing the attack."
    attack_stage: RansomwareAttackStage = RansomwareAttackStage.NOT_STARTED
    "The ransomware attack stage. See RansomwareAttackStage Class"

    def __init__(self, **kwargs):
        kwargs["name"] = "RansomwareScript"
        kwargs["port"] = Port.NONE
        kwargs["protocol"] = IPProtocol.NONE

        super().__init__(**kwargs)

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        return state

    @property
    def _host_db_client(self) -> DatabaseClient:
        """Return the database client that is installed on the same machine as the Ransomware Script."""
        db_client = self.software_manager.software.get("DatabaseClient")
        if db_client is None:
            self.sys_log.warning(f"{self.__class__.__name__} cannot find a database client on its host.")
        return db_client

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        rm.add_request(
            name="execute",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.attack())),
        )
        return rm

    def _activate(self):
        """
        Simulate the install process as the initial stage of the attack.

        Advances the attack stage to 'ACTIVATE' attack state.
        """
        if self.attack_stage == RansomwareAttackStage.INSTALL:
            self.sys_log.info(f"{self.name}: Activated!")
            self.attack_stage = RansomwareAttackStage.ACTIVATE

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep to the bot, triggering the application loop.

        :param timestep: The timestep value to update the bot's state.
        """
        pass

    def run(self) -> bool:
        """Calls the parent classes execute method before starting the application loop."""
        super().run()
        return True

    def _application_loop(self) -> bool:
        """
        The main application loop of the script, handling the attack process.

        This is the core loop where the bot sequentially goes through the stages of the attack.
        """
        if not self._can_perform_action():
            return False
        if self.server_ip_address and self.payload:
            self.sys_log.info(f"{self.name}: Running")
            self.attack_stage = RansomwareAttackStage.NOT_STARTED
            self._local_download()
            self._install()
            self._activate()
            self._perform_target_scan()
            self._setup_beacon()
            self._perform_ransomware_encrypt()

            if self.repeat and self.attack_stage in (
                RansomwareAttackStage.SUCCEEDED,
                RansomwareAttackStage.FAILED,
            ):
                self.attack_stage = RansomwareAttackStage.NOT_STARTED
            return True
        else:
            self.sys_log.warning(f"{self.name}: Failed to start as it requires both a target_ip_address and payload.")
            return False

    def configure(
        self,
        server_ip_address: IPv4Address,
        server_password: Optional[str] = None,
        payload: Optional[str] = None,
        target_scan_p_of_success: Optional[float] = None,
        c2_beacon_p_of_success: Optional[float] = None,
        ransomware_encrypt_p_of_success: Optional[float] = None,
        repeat: bool = True,
    ):
        """
        Configure the Ransomware Script to communicate with a DatabaseService.

        :param server_ip_address: The IP address of the Node the DatabaseService is on.
        :param server_password: The password on the DatabaseService.
        :param payload: The attack stage query (Encrypt / Delete)
        :param target_scan_p_of_success: The probability of success for the target scan stage.
        :param c2_beacon_p_of_success: The probability of success for the c2_beacon stage
        :param ransomware_encrypt_p_of_success: The probability of success for the ransomware 'attack' (encrypt) stage.
        :param repeat: Whether to repeat attacking once finished.
        """
        if server_ip_address:
            self.server_ip_address = server_ip_address
        if server_password:
            self.server_password = server_password
        if payload:
            self.payload = payload
        if target_scan_p_of_success:
            self.target_scan_p_of_success = target_scan_p_of_success
        if c2_beacon_p_of_success:
            self.c2_beacon_p_of_success = c2_beacon_p_of_success
        if ransomware_encrypt_p_of_success:
            self.ransomware_encrypt_p_of_success = ransomware_encrypt_p_of_success
        if repeat:
            self.repeat = repeat
        self.sys_log.info(
            f"{self.name}: Configured the {self.name} with {server_ip_address=}, {payload=}, {server_password=}, "
            f"{repeat=}."
        )

    def _install(self):
        """
        Simulate the install stage in the kill-chain.

        Advances the attack stage to 'ACTIVATE' if successful.

        From this attack stage onwards.
        the ransomware application is now visible from this point onwardin the observation space.
        """
        if self.attack_stage == RansomwareAttackStage.DOWNLOAD:
            self.sys_log.info(f"{self.name}: Malware installed on the local file system")
            downloads_folder = self.file_system.get_folder(folder_name="downloads")
            ransomware_file = downloads_folder.get_file(file_name="ransom_script.pdf")
            ransomware_file.num_access += 1
            self.attack_stage = RansomwareAttackStage.INSTALL

    def _setup_beacon(self):
        """
        Simulates setting up a c2 beacon; currently a pseudo step for increasing red variance.

        Advances the attack stage to 'COMMAND AND CONTROL` if successful.

        :param p_of_sucess: Probability of a successful c2 setup (Advancing this step),
                            by default the success rate is 0.5
        """
        if self.attack_stage == RansomwareAttackStage.PROPAGATE:
            self.sys_log.info(f"{self.name} Attempting to set up C&C Beacon - Scan 1/2")
            if simulate_trial(self.c2_beacon_p_of_success):
                self.sys_log.info(f"{self.name} C&C Successful setup - Scan 2/2")
                c2c_setup = True  # TODO Implement the c2c step via an FTP Application/Service
                if c2c_setup:
                    self.attack_stage = RansomwareAttackStage.COMMAND_AND_CONTROL

    def _perform_target_scan(self):
        """
        Perform a simulated port scan to check for open SQL ports.

        Advances the attack stage to `PROPAGATE` if successful.

        :param p_of_success: Probability of successful port scan, by default 0.1.
        """
        if self.attack_stage == RansomwareAttackStage.ACTIVATE:
            # perform a port scan to identify that the SQL port is open on the server
            self.sys_log.info(f"{self.name}: Scanning for vulnerable databases - Scan 0/2")
            if simulate_trial(self.target_scan_p_of_success):
                self.sys_log.info(f"{self.name}: Found a target database! Scan 1/2")
                port_is_open = True  # TODO Implement a NNME Triggering scan as a seperate Red Application
                if port_is_open:
                    self.attack_stage = RansomwareAttackStage.PROPAGATE

    def attack(self) -> bool:
        """Perform the attack steps after opening the application."""
        if not self._can_perform_action():
            self.sys_log.warning("Ransomware application is unable to perform it's actions.")
            self.run()
        self.num_executions += 1
        return self._application_loop()

    def _perform_ransomware_encrypt(self):
        """
        Execute the Ransomware Encrypt payload on the target.

        Advances the attack stage to `COMPLETE` if successful, or 'FAILED' if unsuccessful.
        :param p_of_success: Probability of successfully performing ransomware encryption, by default 0.1.
        """
        if self._host_db_client is None:
            self.sys_log.info(f"{self.name}: Failed to connect to db_client - Ransomware Script")
            self.attack_stage = RansomwareAttackStage.FAILED
            return

        self._host_db_client.server_ip_address = self.server_ip_address
        self._host_db_client.server_password = self.server_password
        if self.attack_stage == RansomwareAttackStage.COMMAND_AND_CONTROL:
            if simulate_trial(self.ransomware_encrypt_p_of_success):
                self.sys_log.info(f"{self.name}: Attempting to launch payload")
                if not len(self._host_db_client.connections):
                    self._host_db_client.connect()
                if len(self._host_db_client.connections):
                    self._host_db_client.query(self.payload)
                    self.sys_log.info(f"{self.name} Payload delivered: {self.payload}")
                    attack_successful = True
                    if attack_successful:
                        self.sys_log.info(f"{self.name}: Payload Successful")
                        self.attack_stage = RansomwareAttackStage.SUCCEEDED
                    else:
                        self.sys_log.info(f"{self.name}: Payload failed")
                        self.attack_stage = RansomwareAttackStage.FAILED
        else:
            self.sys_log.warning("Attack Attempted to launch too quickly")
            self.attack_stage = RansomwareAttackStage.FAILED

    def _local_download(self):
        """Downloads itself via the onto the local file_system."""
        if self.attack_stage == RansomwareAttackStage.NOT_STARTED:
            if self._local_download_verify():
                self.attack_stage = RansomwareAttackStage.DOWNLOAD
            else:
                self.sys_log.info("Malware failed to create a installation location")
                self.attack_stage = RansomwareAttackStage.FAILED
        else:
            self.sys_log.info("Malware failed to download")
            self.attack_stage = RansomwareAttackStage.FAILED

    def _local_download_verify(self) -> bool:
        """Verifies a download location - Creates one if needed."""
        for folder in self.file_system.folders:
            if self.file_system.folders[folder].name == "downloads":
                self.file_system.num_file_creations += 1
                return True

        self.file_system.create_folder("downloads")
        self.file_system.create_file(folder_name="downloads", file_name="ransom_script.pdf")
        return True
