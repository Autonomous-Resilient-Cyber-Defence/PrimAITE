# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

import random
from enum import Enum, IntEnum
from typing import Dict, List, Literal, Optional, Tuple, Type, Union

from gymnasium.core import ObsType
from prettytable import MARKDOWN, PrettyTable
from pydantic import Field, PositiveInt

from primaite.game.agent.interface import RequestResponse
from primaite.game.agent.scripted_agents.abstract_tap import (
    AbstractTAP,
    KillChainOptions,
    KillChainStageOptions,
    KillChainStageProgress,
)
from primaite.utils.validation.ip_protocol import IPProtocol, PROTOCOL_LOOKUP
from primaite.utils.validation.ipv4_address import IPV4Address, StrIP
from primaite.utils.validation.port import Port, PORT_LOOKUP


class MobileMalwareKillChainOptions(KillChainOptions):
    """Model Validation for the TAP001's implementation of the mobile malware kill chain."""

    class _ActivateOptions(KillChainStageOptions):
        pass

    class _PropagateOptions(KillChainStageOptions):
        scan_attempts: PositiveInt = 1
        """The amount of scan actions the tap001 is permitted to take until the PROPAGATE stage is considered failed."""
        repeat_scan: bool = False
        """Optional boolean flag to control repeat scan behaviour after an the initial scan."""
        network_addresses: List[str]
        """An ordered list which contains the network addresses for the propagate step to follow.

            At current, Agents have no way of probing the simulation for routing information (Such as traceroute)

            Therefore, to propagate through the an network, a list of each network address must be
            be provided to the TAP001 agent. The TAP001 agent will scan each address in
            the sequential order.
        """

    class _CommandAndControlOptions(KillChainStageOptions):
        keep_alive_frequency: PositiveInt = 5
        """The frequency of ``keep_alives`` that the C2 Beacon will be configured to use."""
        masquerade_port: Port = 80
        """The port that the C2 Beacon will be configured to use."""
        masquerade_protocol: IPProtocol = "tcp"
        """The protocol that the C2 Beacon will be configured to use."""
        c2_server_name: str = ""
        """The hostname of the C2_Server that the C2 Beacon is intended to use."""
        c2_server_ip: StrIP

    class _PayloadOptions(KillChainStageOptions):
        payload: Optional[str] = "ENCRYPT"
        """The query used on payload kill chain step. Defaults to Encrypt."""
        exfiltrate: bool = True
        """Boolean which indicates if TAP001 should exfiltrate the target database.db file."""
        corrupt: bool = True
        """Boolean which indicates if TAP001 should launch the RansomwareScript."""
        exfiltration_folder_name: Optional[str] = None
        """The folder used to store the database.db file after successful exfiltration."""
        target_username: str = "admin"
        """The username used to login into a target node in order to perform file exfiltration."""
        target_password: str = "admin"
        """The password used to login into a target node in order to perform file exfiltration."""
        continue_on_failed_exfil: bool = True
        """Whether TAP001 should continue to encrypt if the exfiltration fails."""

    ACTIVATE: _ActivateOptions = Field(default_factory=lambda: MobileMalwareKillChainOptions._ActivateOptions())
    PROPAGATE: _PropagateOptions = Field(default_factory=lambda: MobileMalwareKillChainOptions._PropagateOptions())
    COMMAND_AND_CONTROL: _CommandAndControlOptions = Field(
        default_factory=lambda: MobileMalwareKillChainOptions._CommandAndControlOptions()
    )
    PAYLOAD: _PayloadOptions = Field(default_factory=lambda: MobileMalwareKillChainOptions._PayloadOptions())


class MobileMalwareKillChain(IntEnum):
    """
    Enumeration representing different attack stages of the mobile malware kill chain.

    This enumeration defines the various stages in the mobile malware kill chain
    can be in during its lifecycle in the simulation.
    Each stage represents a specific phase in the attack process.
    """

    DOWNLOAD = 1
    "Malware is downloaded onto the tap001's starting client."
    INSTALL = 2
    "The malware is activated which initiates it's malicious functions."
    ACTIVATE = 3
    "The malware installs itself onto the terminal, attempting to gain persistence."
    PROPAGATE = 4
    "The malware attempts to spread to other systems or networks, looking for vulnerable services."
    COMMAND_AND_CONTROL = 5
    "The malware establishes a connection to an external command and control server."
    PAYLOAD = 6
    "The malware performs its intended malicious activities, dependent on payload."

    # These Enums must be included in all kill chains.
    # Due to limitations in Python and Enums, it is not possible to inherit these Enums from an base class.

    NOT_STARTED = 100
    "Indicates that the Kill Chain has not started."
    SUCCEEDED = 200
    "Indicates that the kill chain has succeeded."
    FAILED = 300
    "Indicates that the attack has failed."

    def initial_stage(self) -> "MobileMalwareKillChain":
        """Returns the first stage in the kill chain. Used by Abstract TAP for TAP Agent Setup."""
        return self.DOWNLOAD


class PortStatus(Enum):
    """
    Enumeration which represent TAP001's "Knowledge" of a port in the simulation.

    Used to by the Propagate kill chain stage to track the current understanding of the
    simulation by the TAP001 agent.

    Additionally, also used to define failure and success clauses.
    """

    UNKNOWN = 0
    "Indicates that the status of the port is unknown."
    OPEN = 1
    "Indicates that the port is open in the simulation."
    CLOSED = 2
    "Indicates that the port is closed in the simulation."


class TAP001(AbstractTAP, discriminator="tap-001"):
    """
    TAP001 | Mobile Malware -- Ransomware Variant.

    Currently, implements the ransomware variant Mobile Malware kill chain.

    This Threat Actor Profile (TAP) represents ransomware.
    After gaining access to a host, the ransomware scans the
    network to find the target database and then corrupts it.

    At current, TAP001's final stage (corruption) is limited to
    database servers.

    Please see the TAP001-Kill-Chain-E2E.ipynb for more information.
    """

    class AgentSettingsSchema(AbstractTAP.AgentSettingsSchema):
        """TAP001's AgentSettings schema (Expands upon the inherited AbstractTAP `AgentSettingsSchema`)."""

        target_ips: Optional[List[StrIP]] = []
        default_target_ip: StrIP
        kill_chain: MobileMalwareKillChainOptions  # = Field(default_factory=lambda: MobileMalwareKillChainOptions())

    class ConfigSchema(AbstractTAP.ConfigSchema):
        """Config Schema for the TAP001 agent."""

        type: Literal["tap-001"] = "tap-001"
        agent_settings: "TAP001.AgentSettingsSchema" = Field(default_factory=lambda: TAP001.AgentSettingsSchema())

    config: ConfigSchema  # = Field(default_factory=lambda: TAP001.ConfigSchema())

    selected_kill_chain: Type[MobileMalwareKillChain] = MobileMalwareKillChain

    last_scan_timestep: list[int] = []
    "Timesteps when the agent has performed scans. Used for reading agent action history"
    last_scan_type: Optional[Literal["Ping", "Port"]] = None
    "The type of scan that was previously performed."
    scans_complete: int = 0
    "Number of scans completed"
    networks_scanned: int = 0
    "Number of subnets that have been scanned"
    permitted_attempts: int = 10
    "The permitted amount of scans allowed before the scan is considered to have failed"
    c2_settings: dict = {}
    "Dictionary containing all C2 stage relevant user settings."
    payload_settings: dict = {}
    "Dictionary containing all Payload stage relevant internal and user settings."
    chosen_application: str = ""
    """The name of the agent's currently chosen application."""
    target_ip: Optional[IPV4Address] = None
    """TAP001's current target ip. This attribute is changed dynamically through out the kill chain."""

    network_knowledge: Dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_agent()

    def _progress_kill_chain(self) -> None:
        """Private Method used to progress the kill chain to the next stage."""
        if self.next_kill_chain_stage == MobileMalwareKillChain.PAYLOAD:  # Covering final stage edge case.
            self.current_kill_chain_stage = self.selected_kill_chain(self.current_kill_chain_stage + 1)
            self.next_kill_chain_stage = self.selected_kill_chain.SUCCEEDED
        else:
            # Otherwise, set the current stage to the previous next and increment the next kill chain stage.
            self.current_kill_chain_stage = self.next_kill_chain_stage

            if self.current_kill_chain_stage == self.selected_kill_chain.SUCCEEDED:
                self.next_kill_chain_stage = self.selected_kill_chain.NOT_STARTED
            else:
                self.next_kill_chain_stage = self.selected_kill_chain(self.current_kill_chain_stage + 1)

        self.current_stage_progress = KillChainStageProgress.PENDING

    def setup_agent(self) -> None:
        """Responsible for agent setup upon episode reset.

        Explicitly this method performs the following:
        1. Loads the inherited attribute 'selected_kill_chain' with the MobileMalwareKillChain
        2. Selects the starting node frm the given user TAP settings.
        3. Selects the target node frm the given user TAP settings.
        4. Sets the next execution timestep to the given user tap settings - The starting step.
        5. Sets the TAP's current host as the selected starting node.
        6. instantiates the required class attributes for performing the PROPAGATE step.
        """
        # TAP Boilerplate Setup
        self._setup_agent_kill_chain(MobileMalwareKillChain)

        # TAP001 Specific Setup
        self._select_start_node()
        self._select_target_ip()
        self._set_next_execution_timestep(self.config.agent_settings.start_step)
        self.current_host = self.starting_node

        # The permitted amount of scans allowed before the scan is considered to have failed.
        self.permitted_attempts = self.config.agent_settings.kill_chain.PROPAGATE.scan_attempts

        # The current simulation knowledge.
        self.network_knowledge: Dict = {
            "target_found": False,  # Used for the propagate step
            # Using Enums rather than close open Set
            # _scan_failure_handler clauses will assume that a target does not have a open port an action too early
            # If we use "target_port" = False as the default value.
            # As we need to perform to a Port Scan Before a target_port can be confirmed as either open or closed.
            "target_port": PortStatus.UNKNOWN,
            "target_ip": self.target_ip,
            "next_scan_target": self.config.agent_settings.kill_chain.PROPAGATE.network_addresses[0],  # Local Subnet
            "live_hosts": {},  # Previous scan action results.
        }

        # User supplied and internal C2 settings
        self.c2_settings: Dict = {
            "c2_server": self.config.agent_settings.kill_chain.COMMAND_AND_CONTROL.c2_server_name,
            "c2_server_ip_address": self.config.agent_settings.kill_chain.COMMAND_AND_CONTROL.c2_server_ip,
            "keep_alive_frequency": self.config.agent_settings.kill_chain.COMMAND_AND_CONTROL.keep_alive_frequency,
            "masquerade_protocol": self.config.agent_settings.kill_chain.COMMAND_AND_CONTROL.masquerade_protocol,
            "masquerade_port": self.config.agent_settings.kill_chain.COMMAND_AND_CONTROL.masquerade_port,
            "beacon_configured": False,
        }
        # User supplied and internal Payload Stage Settings
        self.payload_settings: Dict = {
            "target_file_name": "database.db",
            "target_folder_name": "database",
            "exfiltration_folder_name": self.config.agent_settings.kill_chain.PAYLOAD.exfiltration_folder_name,
            "target_ip_address": self.target_ip,
            "target_username": self.config.agent_settings.kill_chain.PAYLOAD.target_username,
            "target_password": self.config.agent_settings.kill_chain.PAYLOAD.target_password,
            "corrupt": self.config.agent_settings.kill_chain.PAYLOAD.corrupt,
            "exfiltrate": self.config.agent_settings.kill_chain.PAYLOAD.exfiltrate,
            "continue_on_failed_exfil": self.config.agent_settings.kill_chain.PAYLOAD.continue_on_failed_exfil,
        }

    def get_action(self, obs: ObsType, timestep: int) -> Tuple[str, Dict]:
        """Follows the TAP001's Mobile Malware Kill Chain.

        Calls the next TAP001 Action Stage. Uses private methods to schedule kill chain stages.
        See TAP001-Kill-Chain-E2E.ipynb for further information on the TAP001 agent.

        :param obs: Current observation for this agent.
        :type obs: ObsType
        :param timestep: The current simulation timestep, used for scheduling actions
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        if timestep < self.next_execution_timestep or self.actions_concluded:
            return "do-nothing", {}  # bypasses self.chosen_action

        # self.current_timestep is currently the previous execution timestep
        # So it can be used to index action history.
        if not self._tap_return_handler(self.current_timestep):
            # Propagate kill chain stage handles simulation failure independently.
            # See _scan_setup_handler for more information.
            if self.current_kill_chain_stage == MobileMalwareKillChain.PROPAGATE:
                pass
            elif (
                (self.current_kill_chain_stage == MobileMalwareKillChain.PAYLOAD)
                and (self.current_stage_progress == KillChainStageProgress.IN_PROGRESS)
                and (self.payload_settings["continue_on_failed_exfil"])
            ):
                pass
            else:
                # Repeating the previously chosen action if the last action was unsuccessful.
                self._set_next_execution_timestep(timestep + self.config.agent_settings.frequency)
                self._tap_outcome_handler(MobileMalwareKillChain)
                self.update_current_timestep(new_timestep=timestep)
                self._set_next_execution_timestep(timestep + self.config.agent_settings.frequency)
                return self.chosen_action

        self.update_current_timestep(new_timestep=timestep)
        self._set_next_execution_timestep(
            timestep + self.config.agent_settings.frequency
        )  # Sets the next execution step.

        self._tap_outcome_handler(MobileMalwareKillChain)  # Handles successes and failures

        # The kill chain is called in reverse order
        # The kill chain sequence must be called in reverse order to ensure proper execution.
        # Otherwise the guard clauses within these methods that check for the correct kill chain stage
        # Will no longer function as intended and lead to multiple methods overwriting self.chosen_action

        self._payload()  # Final kill chain stage
        self._c2c()
        self._propagate()
        self._activate()
        self._install()
        self._download()
        self._tap_start(MobileMalwareKillChain)  # First kill chain stage

        return self.chosen_action

    def _download(self) -> None:
        """Mobile Malware | Download Stage.

        First stage in the Mobile Malware Kill Chain.
        Requires Two CAOS actions before progressing to the next kill chain stage.

        Performs the each action in the following order:
        - Creates a folder called "downloads" via node-folder-create
        - Creates a "malware_dropper.ps1" file via node-folder-create

        OBS Impact:
        STARTING_HOST:FOLDERS:FOLDER:*
        STARTING_HOST:FOLDERS:FOLDER:FILES:FILE:*
        STARTING_HOST:num_file_creations
        STARTING_HOST:num_file_deletions
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.DOWNLOAD:  # No Probability on Download
            # Execution flow _download kill chain stage
            if self.current_stage_progress == KillChainStageProgress.PENDING:
                self.current_host = self.starting_node
                self.logger.info(f"TAP001 reached the {self.current_kill_chain_stage.name} stage")
                self.logger.info(
                    f"The malware dropper is attempting to download onto {self.current_host}'s downloads folder!"
                )
                self.chosen_action = "node-folder-create", {
                    "node_name": self.current_host,
                    "folder_name": "downloads",
                }
                self.current_stage_progress = KillChainStageProgress.IN_PROGRESS
            # Execution flow for the second execution
            elif self.current_stage_progress == KillChainStageProgress.IN_PROGRESS:
                self.logger.info(f"The malware has entered {self.current_host}'s downloads folder!")
                self.chosen_action = "node-file-create", {
                    "node_name": self.current_host,
                    "folder_name": "downloads",
                    "file_name": "malware_dropper.ps1",
                    "force": True,
                }
                self.current_stage_progress = KillChainStageProgress.FINISHED
            # Progresses the kill chain after the second execution.
            if self.current_stage_progress == KillChainStageProgress.FINISHED:
                self._progress_kill_chain()

    def _install(self) -> None:
        """Mobile Malware | Install Stage.

        Second stage in the Mobile Malware Kill Chain.
        Accesses the previously created file "malware_dropper.ps1" via node-file-access

        Observation Space Impact(s):

        STARTING_HOST:FOLDERS:FOLDER:FILES:FILE:NUM_FILE_ACCESS
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.INSTALL:  # No Probability on Install
            self.logger.info(f"TAP001 reached the {self.current_kill_chain_stage.name} stage.")
            self.logger.info(f"The malware is attempting to gain persistence on {self.target_ip}.")
            self.current_host = self.starting_node
            self.chosen_action = "node-file-access", {
                "node_name": self.current_host,
                "folder_name": "downloads",
                "file_name": "malware_dropper.ps1",
            }
            # This stage only takes one action so there is no need for self.current_stage_progress
            self._progress_kill_chain()

    def _activate(self) -> None:
        """Mobile Malware | Activate Stage.

        First stage in the Mobile Malware Kill Chain.
        Requires One CAOS action before progressing to the next kill chain stage.

        Installs RansomwareScript via node-application-install

        Observation Space Impact(s):

        STARTING_HOST:APPLICATIONS:APPLICATION:*
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.ACTIVATE:  # No Probability on Activate
            # Upon stage entry perform the following:
            self.logger.info(f"TAP001 {self.config.ref} has reached the {self.current_kill_chain_stage.name} stage")
            # Select the starting host
            self.current_host = self.starting_node

            # Selecting the ransomware-script as the next application to install
            self.chosen_application = "ransomware-script"

            self.current_stage_progress = KillChainStageProgress.FINISHED

            self.logger.info(f"Attempting to install {self.chosen_application} on {self.starting_node}")

            self.chosen_action = "node-application-install", {
                "node_name": self.current_host,
                "application_name": self.chosen_application,
            }
            self._progress_kill_chain()

    def _propagate(self) -> None:
        """Mobile Malware | Propagate Stage.

        Fourth stage in the Insider kill chain.
        Performs a trial using the given user PROPAGATE stage probability.

        This stage requires dynamic interaction within the simulation
        and thus the amount of steps required to progress the stage
        is dependent on the TAP's chosen target and starting node.

        Port Scan Action(s):
        node-nmap-port-scan
        node-nmap-ping-scan
        node-network-service-recon

        Observation Space Impact(s):

        *:NICS:NIC:TRAFFIC:PROTOCOL:PORT:*
        STARTING_HOST:APPLICATIONS:APPLICATION:OPERATING_STATUS:operating_status
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.PROPAGATE:
            # If the _propagate stage is already in progress: Continue.
            if self.current_stage_progress == KillChainStageProgress.IN_PROGRESS:
                self.current_stage_progress = self._scan_handler()
                if self.current_stage_progress == KillChainStageProgress.FINISHED:
                    self._progress_kill_chain()
            # Otherwise: Trial propagate stage probability and start the scan.
            else:
                if self._agent_trial_handler(self.config.agent_settings.kill_chain.PROPAGATE.probability):
                    if self.current_stage_progress == KillChainStageProgress.PENDING:
                        self.logger.info(f"TAP001 reached the {self.current_kill_chain_stage.name} stage")
                        self.current_host = self.starting_node
                        # Resets Propagate relevant attributes
                        # Prevents repeating kill chains from starting propagate with extra knowledge.
                        self._propagate_reset()
                    self.logger.info(f"Attempting to scan the network in order to locate {self.target_ip}!")

                    self.chosen_action = "node-nmap-ping-scan", {
                        "source_node": self.current_host,
                        "target_ip_address": self.network_knowledge.get("next_scan_target"),
                        "show": False,
                    }

                    self.scans_complete = 1  # Setting the scan count to one.
                    self.last_scan_timestep.append(self.current_timestep)  # Appending the last_scan_timestep
                    self.last_scan_type = "Ping"  # Setting the last_scan_type to Ping
                    self.current_stage_progress = KillChainStageProgress.IN_PROGRESS
                else:
                    if self.config.agent_settings.repeat_kill_chain_stages == False:
                        self.current_kill_chain_stage = self.selected_kill_chain.FAILED
                    self.chosen_action = "do-nothing", {}

    def _c2c(self) -> None:
        """Mobile Malware | Command and Control Stage.

        Fourth stage in the Insider kill chain.
        The current implementation installs, configures and setups the C2 Suite via
        the following CAOS actions which are this method calls in the order below:

        1. Installs the C2 Beacon on the starting node. ``node-application-install``
        2. Configures the C2 Beacon to the C2 Server using given TAP settings. ``configure-c2-beacon``
        3. Establishes connection. ``node-application-execute```.

        For a in-depth explanation of the C2 Suite please refer to the ``C2-E2E-notebook``.

        Observation Space Impact(s):
        STARTING_HOST:NICS:NIC:TRAFFIC:PROTOCOL:PORT:*
        STARTING_HOST:APPLICATIONS:APPLICATION:OPERATING_STATUS:operating_status
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.COMMAND_AND_CONTROL:
            self.chosen_application = "c2-beacon"
            # Execution flow for the Command and Control stage:
            if self.current_stage_progress == KillChainStageProgress.PENDING:
                # Performing a probability check on the first C2 action. Similar to Propagate. This is performed once.
                if self._agent_trial_handler(self.config.agent_settings.kill_chain.COMMAND_AND_CONTROL.probability):
                    self.logger.info(f"TAP001 reached the {self.current_kill_chain_stage.name} stage.")
                    self.logger.info("Attempting to install C2 Beacon on starting host.")
                    self.chosen_action = "node-application-install", {
                        "node_name": self.current_host,
                        "application_name": self.chosen_application,
                    }
                    self.current_stage_progress = KillChainStageProgress.IN_PROGRESS
                    self.c2_settings.update({"beacon_installed": False})  # For repeat kill chains.
                else:
                    self.chosen_action = "do-nothing", {}
                    if not self.config.agent_settings.repeat_kill_chain_stages:
                        self.current_kill_chain_stage = self.selected_kill_chain.FAILED

            elif self.current_stage_progress == KillChainStageProgress.IN_PROGRESS:
                if self.c2_settings.get("beacon_configured") == False:
                    self.logger.info("Attempting to configure C2 Beacon.")

                    config = {
                        "c2_server_ip_address": self.c2_settings.get("c2_server_ip_address"),
                        "keep_alive_frequency": self.c2_settings.get("keep_alive_frequency"),
                        "masquerade_port": self.c2_settings.get("masquerade_port"),
                        "masquerade_protocol": self.c2_settings.get("masquerade_protocol"),
                    }

                    self.chosen_action = "configure-c2-beacon", {"node_name": self.current_host, **config}
                    # Triggers the below else statement upon re-entering this method
                    self.c2_settings.update({"beacon_configured": True})
                else:
                    self.logger.info("Attempting to connect C2 Beacon to C2 Server.")
                    self.chosen_action = "node-application-execute", {
                        "node_name": self.current_host,
                        "application_name": self.chosen_application,
                    }

                    self._progress_kill_chain()

    def _payload(self) -> None:
        """Mobile Malware | Payload Stage.

        Fifth and final stage in the Mobile Malware Kill Chain.
        Requires a single CAOS action before progressing to the next kill chain stage.

        Performs c2-server-ransomware-launch CAOS Action.
        This causes the ransomware to send a malicious payload to the target
        database to which causes database.db file to enter into a corrupted state.

        Observation Space Impact(s):

        TARGET_HOST:FOLDERS:FOLDER:FILES:FILE:*
        STARTING_HOST:APPLICATIONS:APPLICATION:OPERATING_STATUS
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.PAYLOAD:
            if self.current_stage_progress == KillChainStageProgress.IN_PROGRESS:
                self.current_stage_progress = self._payload_handler()

            # Performing a probability trial on payload.
            if self.current_stage_progress == KillChainStageProgress.PENDING:
                if self._agent_trial_handler(self.config.agent_settings.kill_chain.PAYLOAD.probability):
                    self.logger.info(f"TAP001 reached the {self.current_kill_chain_stage.name} stage.")
                    self.current_host = self.c2_settings["c2_server"]
                    self.chosen_action = "c2-server-ransomware-configure", {
                        "node_name": self.current_host,
                        "server_ip_address": self.target_ip,
                        "payload": "ENCRYPT",
                    }
                    self.current_stage_progress = KillChainStageProgress.IN_PROGRESS
                else:
                    self.chosen_action = "do-nothing", {}
                    if not self.config.agent_settings.repeat_kill_chain_stages:
                        self.current_kill_chain_stage = self.selected_kill_chain.FAILED

            if self.current_stage_progress == KillChainStageProgress.FINISHED:
                self._progress_kill_chain()

    def _payload_handler(self) -> KillChainStageProgress:
        """Private method which handles the payload kill chain stage.

        This method is responsible for setting the chosen_action attribute
        to either encrypt, exfiltrate the target's database.db file dependent
        on user given settings.

        Returns ``KillChainStageProgress.FINISHED`` if all actions have been completed
        or ``KillChainStageProgress.IN_PROGRESS`` if further actions are required
        to complete this stage.

        :rtype: KillChainStageProgress
        """
        if self.payload_settings["exfiltrate"] == True:
            self.chosen_action = "c2-server-data-exfiltrate", {
                "node_name": self.current_host,
                "target_file_name": self.payload_settings.get("target_file_name"),
                "target_folder_name": self.payload_settings.get("target_folder_name"),
                "exfiltration_folder_name": self.payload_settings.get("exfiltration_folder_name"),
                "target_ip_address": self.payload_settings.get("target_ip_address"),
                "username": self.payload_settings.get("target_username"),
                "password": self.payload_settings.get("target_password"),
            }
            self.payload_settings.update({"exfiltrate": False})

            if self.payload_settings["corrupt"]:
                return KillChainStageProgress.IN_PROGRESS

        elif self.payload_settings["corrupt"]:
            self.chosen_action = "c2-server-ransomware-launch", {"node_name": self.current_host}
            self.payload_settings.update({"corrupt": False})

        return KillChainStageProgress.FINISHED

    def _scan_handler(self) -> KillChainStageProgress:
        """Private method which handles the propagate kill chain stage.

        This method handles the agent action response

        Returns the current KillChainStageProgress of the scan.
        If this method returns .IN_PROGRESS then the method is called on the next timestep.

        If this method returns .FINISHED then the kill chain stage is progressed.
        Refer to the _propagate method for further information regarding execution flow.

        :rtype: KillChainStageProgress.
        """
        # Retrieving the previous scan action's results.
        previous_scan_response = self._scan_setup_handler()

        # If the previous scan was unsuccessful we need to repeat the previous scan.
        # So we can skip the scan action response handler
        if previous_scan_response.status == "success":
            # Setting scan_results as the previous scan action's .data attribute
            scan_results = previous_scan_response.data

            # Updating self.network_knowledge with the previous scan.
            self._scan_action_response_handler(scan_results)

        # Before continuing, checking for edge case errors.
        if self._scan_failure_handler():
            # self.chosen_action would be the previous scan at this point
            # Setting self.chosen action to do nothing in order to prevent TAP001 from performing
            # from performing another despite having failed the kill chain.
            self.chosen_action = "do-nothing", {}
            self.logger.info(f"Thus TAP001 {self.config.ref} has failed the {self.current_kill_chain_stage.name}")
            if self.config.agent_settings.repeat_kill_chain_stages == False:
                self.current_kill_chain_stage = self.selected_kill_chain.FAILED
            else:
                self.logger.info(f"TAP001 has opted to reattempt the {self.current_kill_chain_stage.name} stage!")
            # breaking out of _scan_handler early & resetting the PROPAGATE stage.
            return KillChainStageProgress.PENDING

        # Setting the Next Scan Type.
        next_scan_type = self._scan_logic_handler()
        self._scan_action_handler(next_scan_type)

        # Final Clause - Returns either IN_PROGRESS or FINISHED.
        return self._scan_progress_handler()

    def _scan_logic_handler(self) -> str:
        """TAP001's private method responsible for controlling execution flow within the _scan_handler() method.

        This method is decides the next scan action to be taken by the TAP Agent dependent on the self.network_knowledge
        attribute. The self.network_knowledge attribute is updated dynamically via _scan_action_response_handler()

        This method is carries out the following logic:

        1. If the target is found; Port scan the target host.

        This to confirm that a valid target is present on the target host
        before moving onto the next stage.

        2. If the current network has not yet been Recon Scanned; Recon Scan all live hosts.

        If the current network has live hosts yet no protocol/port information has been identified,
        then we need to perform a recon scan.

        3. If the current network has been Recon Scanned; Ping Scan the next network address.

        If the current network has no currently identified live_hosts, then we must ping scan
        the provided network address in order to locate some hosts to recon-scan.

        Additionally, if we have reached this clause without being caught by a previous statement then we can
        move onto the next network address.

        Otherwise, If you reach the final else clause then a logic failure
        has occurred somewhere before reaching this function.

        This logic is repeated until a valid target is found.

        rtype: str
        """
        # If the target is found, then we only need to Port Scan the network to reach an exit condition.
        # Intuitively doesn't make sense to perform another scan after the target has already been scanned,
        # However, In the real world, you would perform an more aggressive scan (Port in this case)
        # To identify other potential vulnerabilities on the target.
        if self.network_knowledge.get("target_found") == True:
            return "Port"

        # This assumes that NMAP's action response stays consistent.
        if self.last_scan_type == "Ping":
            # If we know that their are no suitable targets in the last_results
            # then we scan skip Recon and Return Ping instead.
            if self.network_knowledge.get("live_hosts") == []:
                self.logger.info(
                    "As we didn't find any suitable hosts from the last scan - we have no need to perform a recon_scan."
                )
                return "Ping"
            else:
                return "Recon"

        # Then the next network address needs to be scanned.
        elif self.last_scan_type == "Recon":
            return "Ping"

        # If we haven't caught a condition at this point then we're running into unexpected behaviour.
        # Returning anything other than a ping type catches an else statement in _scan_action_handler.
        else:
            self.current_kill_chain_stage = MobileMalwareKillChain.FAILED
            return "logic_handler_error"

    def _scan_progress_handler(self) -> KillChainStageProgress:
        """TAP001 Private method used for handling success & continue cases.

        The target must be found via the simulation and a
        valid database service must be installed and running on the target.
        Otherwise, the scan will continue.

        :rtype: KillChainStageProgress.
        """
        # Success Criteria: The Target is found and the target port is also found (Database Service at current)
        if self.network_knowledge["target_found"]:
            target_port = self.network_knowledge["target_port"]
            if target_port == PortStatus.OPEN:
                self.logger.info(f"TAP001 {self.config.ref} located the target and confirmed a valid database service!")
                self.chosen_action = "do-nothing", {}  # No need to perform another scan after this.
                return KillChainStageProgress.FINISHED
            else:
                self.logger.info(
                    f"TAP001 {self.config.ref} located the target but not yet confirmed a valid database service."
                )
                # No need to update scans_complete any further as we've located the target.
                return KillChainStageProgress.IN_PROGRESS
        else:
            self.logger.info(f"TAP001 {self.config.ref} has not yet located the target. Scan continuing!")
            # Updating the amount of scans completed.
            self.scans_complete += 1
            return KillChainStageProgress.IN_PROGRESS

    def _scan_failure_handler(self) -> bool:
        """TAP001 Private Method used for handling the _propagate failure edge cases.

        Returns a True if the scan entered into a failing edge case.
        Otherwise returns False if no errors were encountered.

        :rtype: bool.
        """
        # Simple boolean for keeping track if an edge case is encountered.
        error_found = False

        # Edge Case: If the scan action finds the target but the target doesn't have a database running.
        if self.network_knowledge.get("target_found"):
            target_port = self.network_knowledge["target_port"]
            if (
                target_port == PortStatus.CLOSED
            ):  # Only set to True if the target doesn't have a running database service.
                self.logger.info(
                    f"TAP001 {self.config.ref} was able to locate {self.target_ip} - "
                    f"However, {self.target_ip} does not have a database service running."
                )
                error_found = True

        # Edge Case: If the scan action has executed X times without finding the target.
        # This edge case should be last incase of the elusive double edge-case.
        # (Which would be caught first by this clause which would prevent valuable debugging logs)
        if self.scans_complete >= self.permitted_attempts:
            self.logger.info(
                f"{self.config.ref} was unable to find {self.target_ip}"
                f"within the permitted {self.permitted_attempts} scan attempts."
            )
            error_found = True

        # Returning the boolean.
        return error_found

    def _scan_setup_handler(self) -> RequestResponse:
        """TAP001 Private method responsible for setting up the scan_return_handler on each call.

        Uses the self.last_scan_timestep list to index the self.history inherited attribute.

        Returns the results of the previous scan as an RequestResponse class object.

        :rtype RequestResponse.
        """
        # Using the last_timestep variable as an Index for the last scan action.
        # (This only pops the last_scan_timestep not the self.history attribute itself.)
        previous_scan_action = self.history[self.last_scan_timestep.pop()]

        # Appending the current timestep to the last_scan_timestep.
        self.last_scan_timestep.append(self.current_timestep)

        # Testing for do-nothing,{}'s present in the previous_action.
        if previous_scan_action.action == "do-nothing":
            self.logger.error("do-nothing Caught whilst in scan_handler.")
            self.current_kill_chain_stage = MobileMalwareKillChain.FAILED

        # Abstract TAP handles these errors if the user set the repeat_kill_chain_stages option to false.
        if previous_scan_action.response.status != "success":
            self.logger.info(
                f"The previous scan wasn't successful: {previous_scan_action.response.data} "
                f"Re-attempting the previous scan!"
            )

        # Returning the request.response attribute in AgentActionHistory
        return previous_scan_action.response

    def _scan_action_response_handler(self, scan_results: Union[Dict, list]) -> None:
        """TAP001 Private method which handles any success criteria and sets the self.network_knowledge accordingly.

        This method is responsible for setting the self.network_knowledge attribute dependent on the
        outcome of the previous scans in order to keep track of the current progress of the scan action.

        It's important to note that in the context of the narrative, the malware does not actually know the
        ip address of the target_ip.

        The IP address of the target_ip should only ever be used to confirm that a valid-target is the target_ip
        This way, users are able to configure a network with multiple databases, yet select specific target one.

        :param scan_results: The .data dictionary from the previous scan actions RequestResponse '.data' attribute.
        :type scan_results: dict.
        """
        # This should only ever get called after the target is already found
        # Checks to see if the target has an active database_service running
        # (Thus vulnerable to attack)
        # At current, both there is no way to differentiate between database clients & database services.
        # Thus we have to assume that the given target is a database service.
        if self.network_knowledge.get("target_found"):
            # TODO: Sometimes scan results doesn't contain data for target ip, this is unexpected, hence we added {} as
            # default return to prevent crash. But we ought to figure out why this occurs.
            for protocol, ports in scan_results.get(self.network_knowledge.get("target_ip"), {}).items():
                if protocol == "tcp":
                    for port in ports:
                        if port == PORT_LOOKUP["POSTGRES_SERVER"]:
                            self.logger.info(f"Found a valid target on {self.target_ip}!")
                            self.network_knowledge["target_port"] = PortStatus.OPEN
                            return  # Exit out of the method, no further scans are required.

            # If we couldn't find a valid port, set the target_port to closed
            # Return early.
            self.network_knowledge["target_port"] = PortStatus.CLOSED
            return

        # If we're reached this then we know the target wasn't found within the previous scan_results.
        # Thus we can ignore the port/protocol results and convert scan_results into a list.

        # Covers both PORT and PING scans (Ping returns a List, Port returns a Dict)
        if isinstance(scan_results.get("live_hosts"), list):
            scan_results = scan_results.get("live_hosts")
        else:
            # Recon doesn't return "live_hosts" but a dict of hosts.
            scan_results_list = []
            for hosts in scan_results:
                scan_results_list.append(hosts)
            scan_results = scan_results_list

        # Edge Case: No Returned Results.
        if scan_results == []:
            self.logger.info(f"Didn't find any suitable hosts from the last {self.last_scan_type} scan ")
        else:  # Else - Search through the host_list.
            self.logger.info(f"Found {len(scan_results)} hosts in the previous scan: {scan_results}")
            for host_ip in scan_results:
                # Is the host the target?
                if host_ip == self.network_knowledge.get("target_ip"):
                    # If the previous scan found the target then we don't need to scan another network
                    # We only need to port_scan the previous network address again.
                    # (Handled by _scan_progress_handler)
                    self.logger.info(f"Found {self.target_ip} the in previous scan!")
                    self.network_knowledge.update(target_found=True)
                    # We can return early without updating the lists as PORT scan is hard coded to use the target_ip.
                    return
                else:
                    pass

        # Updating live_hosts with live_hosts list.
        self.network_knowledge.update(live_hosts=scan_results)

        # Updating the next_scan target (Either a list of hosts, or the next network address.)
        self._update_next_scan_target(scan_results)

        return

    # Perhaps could pass **kwargs and simplify the if ladder
    def _scan_action_handler(self, scan_type: str) -> None:
        """TAP001 Private method for handling the self._chosen_action attribute.

        The primary responsibility of this method is to set the self.chosen_action
        to one of the following different scan agent actions dependent on the
        given argument:

        Ping:   node-nmap-ping-scan
        Port:   node-nmap-port-scan
        Recon:  node-network-service-recon

        :param scan_type: The .data dictionary from the previous Scan Actions RequestResponse '.data' attribute.
        :type scan_type: str.
        """
        if scan_type == "Ping":
            self.chosen_action = "node-nmap-ping-scan", {
                "source_node": self.current_host,
                "target_ip_address": self.network_knowledge.get("next_scan_target"),
                "show": False,
            }
        elif scan_type == "Port":
            # As we only need to port scan the target, we can use the given target_ip.
            self.network_knowledge["next_scan_target"] = self.network_knowledge.get("target_ip")

            self.chosen_action = "node-nmap-port-scan", {
                "source_node": self.current_host,
                "target_ip_address": self.network_knowledge.get("target_ip"),
                "show": False,
            }
        elif scan_type == "Recon":
            self.chosen_action = "node-network-service-recon", {
                "source_node": self.current_host,
                "target_ip_address": self.network_knowledge.get("next_scan_target"),
                # Currently both database clients & servers run on POSTGRES_SERVER.
                "target_port": PORT_LOOKUP["POSTGRES_SERVER"],  # 5432
                "target_protocol": PROTOCOL_LOOKUP["TCP"],
                "show": False,
            }
        else:
            self.logger.error(
                f"{self.config.ref}'s _scan_action_handler method encountered a unknown scan_type: {scan_type}"
            )
            self.current_kill_chain_stage = MobileMalwareKillChain.FAILED
            self.chosen_action = "do-nothing", {}

        # Updating the last_scan_type attribute.
        self.logger.info(f"TAP001 {self.config.ref} has opted for a {scan_type} scan!")
        self.last_scan_type = scan_type
        return

    def _update_next_scan_target(self, scan_target: Union[list, str]) -> None:
        """Updates network_knowledge.next_scan_type with the given argument dependent on the last_scan_type.

        If the last scan to be executed was a recon scan; then the next scan is updated
        to be the next user given network address. (We move onto another network)

        otherwise, the live_hosts of the previous scan is selected.

        :param scan_target: The network address (str) or list of hosts (list)
        to be used to update self.network_knowledge.next_scan_target
        :type scan_target: str or list
        """
        if self.last_scan_type == "Recon" or scan_target == []:  # Covers None Edge cases.
            # Edge Case: If the tap agent has ran out of networks to scan!
            try:
                # Tries to update the next_scan_target with the next network address
                self.networks_scanned += 1
                # Now we need to move onto the next network address.
                self.network_knowledge.update(
                    next_scan_target=self.config.agent_settings.kill_chain.PROPAGATE.network_addresses[
                        self.networks_scanned
                    ]
                )

            except IndexError:
                # Just In Case the last subnet has a valid target
                # (We won't be scanning another network, so the index error is irrelevant)
                if self.network_knowledge.get("target_found") == True:
                    pass
                # Repeats from the start if repeat scan is enabled.
                elif self.config.agent_settings.kill_chain.PROPAGATE.repeat_scan == True:
                    self.networks_scanned = 0
                    self.logger.info(f"TAP001 {self.config.ref} couldn't find the target!")
                    self.logger.info(f"TAP001 {self.config.ref} will continue to scan the network!")
                    random_network_address = random.randint(
                        0, len(self.config.agent_settings.kill_chain.PROPAGATE.network_addresses) - 1
                    )
                    self.network_knowledge.update(
                        next_scan_target=self.config.agent_settings.kill_chain.PROPAGATE.network_addresses[
                            random_network_address
                        ]
                    )

                else:
                    self.logger.info(
                        f"TAP001 {self.config.ref} ran out of networks to scan! Unable to find a valid target."
                    )

        elif self.last_scan_type == "Ping":
            # Now we need to recon scan the live_hosts so we set it as the next_scan_target.
            self.network_knowledge.update(next_scan_target=scan_target)

    def _show_scan(self, markdown: bool = False) -> None:
        """
        Prints a table of the current network knowledge of TAP001.

        :param markdown: Flag indicating if output should be in markdown format.
        """
        network_knowledge_headers = [
            "Target Found",
            "Target Port",
            "Target IP",
            # The scan will have already executed by the time.
            # This method is called.
            "Previous Scan Target",
            "Previous Scan Results",
        ]
        network_knowledge_table = PrettyTable(network_knowledge_headers)
        network_knowledge_table.title = f"TAP001 {self.config.ref}'s Current Network Knowledge"
        if markdown:
            network_knowledge_table.set_style(MARKDOWN)
        network_knowledge_table.add_row(
            [
                self.network_knowledge.get("target_found"),
                self.network_knowledge.get("target_port"),
                self.network_knowledge.get("target_ip"),
                self.network_knowledge.get("next_scan_target"),
                self.network_knowledge.get("live_hosts"),
            ]
        )
        print(network_knowledge_table)

        propagate_status_headers = [
            "Last Scan Timestep",
            "Last Scan Type",
            "Scans Complete",
            "Networks Scanned",
            "Permitted Scan Attempts",
        ]
        propagate_status_table = PrettyTable(propagate_status_headers)
        propagate_status_table.title = f"TAP001 {self.config.ref}'s Propagate Stage Status"
        if markdown:
            propagate_status_table.set_style(MARKDOWN)
        propagate_status_table.add_row(
            [
                self.last_scan_timestep,
                self.last_scan_type,
                self.scans_complete,
                self.networks_scanned,
                self.permitted_attempts,
            ]
        )
        print(propagate_status_table)

    def _select_target_ip(self) -> None:
        """
        Handles setting the target node behaviour of TAP type agents.

        If the user given tap_settings provides a target_ip list then the target node
        is set to a random node given in the target_ip list.
        Otherwise, the starting node is set to the 'default_target_node' option.
        """
        if not self.config.agent_settings.target_ips:
            self.target_ip = self.config.agent_settings.default_target_ip
        else:
            self.target_ip = random.choice(self.config.agent_settings.target_ips)

    def _propagate_reset(self) -> None:
        """Resets the propagate relevant attributes back to their original values.

        This method is called to prevent the TAP001 agent from restarting
        it's second kill chain execution with pre-existing network knowledge
        """
        self.last_scan_timestep.clear()
        "Clears the timesteps the last_scan timesteps."
        self.last_scan_type = None
        "Resets the type of scan that was performed most recently"
        self.scans_complete = 0
        "Resets the number of scans completed"
        self.networks_scanned = 0
        "Resets the number of subnets that have been scanned"

        self._network_knowledge_reset()

    def _network_knowledge_reset(self) -> None:
        """Resets self.network_knowledge back to their starting values.

        This method is called to prevent the TAP001 agent from instantly
        skipping past the Propagate Stage on it's second kill chain attempt.
        (The target would have already been found in it's first run execution.)
        """
        self.network_knowledge = {
            "target_found": False,  # Used for the propagate step
            "target_port": PortStatus.UNKNOWN,
            "target_ip": self.target_ip,
            "next_scan_target": self.config.agent_settings.kill_chain.PROPAGATE.network_addresses[0],  # Local Subnet
            "live_hosts": {},  # Previous scan action results.
        }
