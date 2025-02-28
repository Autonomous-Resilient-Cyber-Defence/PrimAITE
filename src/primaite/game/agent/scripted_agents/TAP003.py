# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from enum import IntEnum
from typing import Dict, List, Literal, Optional, Tuple, Type

from gymnasium.core import ObsType
from pydantic import Field

from primaite.game.agent.actions.acl import RouterACLAddRuleAction
from primaite.game.agent.scripted_agents.abstract_tap import (
    AbstractTAP,
    KillChainOptions,
    KillChainStageOptions,
    KillChainStageProgress,
)


class InsiderKillChainOptions(KillChainOptions):
    """Model validation for TAP003's Kill Chain."""

    class _PlanningOptions(KillChainStageOptions):
        """Valid options for the `PLANNING` InsiderKillChain stage."""

        starting_network_knowledge: Dict  # TODO: more specific schema here?

    class _AccessOptions(KillChainStageOptions):
        """Valid options for the `ACCESS` InsiderKillChain stage."""

        pass

    class _ManipulationOptions(KillChainStageOptions):
        """Valid options for the `MANIPULATION` InsiderKillChain stage."""

        account_changes: List[Dict] = []  # TODO: More specific schema here?

    class _ExploitOptions(KillChainStageOptions):
        """Valid options for the `EXPLOIT` InsiderKillChain stage."""

        malicious_acls: List[RouterACLAddRuleAction.ConfigSchema] = []

    PLANNING: _PlanningOptions = Field(default_factory=lambda: InsiderKillChainOptions._PlanningOptions())
    ACCESS: _AccessOptions = Field(default_factory=lambda: InsiderKillChainOptions._AccessOptions())
    MANIPULATION: _ManipulationOptions = Field(default_factory=lambda: InsiderKillChainOptions._ManipulationOptions())
    EXPLOIT: _ExploitOptions = Field(default_factory=lambda: InsiderKillChainOptions._ExploitOptions())


class InsiderKillChain(IntEnum):
    """
    Enumeration representing different attack stages of the vulnerability and backdoor creation kill chain.

    This kill chain is designed around the TAP003 - Malicious Insider Corporal Pearson.
    Each stage represents a specific phase in the kill chain.
    Please refer to the TAP003 notebook for the current version's implementation of this kill chain.
    """

    RECONNAISSANCE = 1
    "Represents TAP003 identifying sensitive systems, data and access control mechanisms"
    PLANNING = 2
    "Represents TAP003 devising a plan to exploit their elevated privileges."
    ACCESS = 3
    "Represents TAP003's using legitimate credentials to access the access control settings."
    MANIPULATION = 4
    "Represents TAP003 altering ACLs, User & Group Attributes & other control mechanisms to grant unauthorised access"
    EXPLOIT = 5
    "Represents TAP003 exploiting their insider knowledge and privilege to implement changes for sabotage."
    EMBED = 6
    "Represents TAP003's additional changes to ensure continued access"
    CONCEAL = 7
    "Represents TAP003's efforts in hiding their traces of malicious activities"
    EXTRACT = 8
    "Represents TAP003 removing sensitive data from the organisation, either for personal gain or to inflict harm."
    ERASE = 9
    "Represents TAP003 covering their tracks by removing any tools, reverting temporary changes and logging out"

    # These Enums must be included in all kill chains.
    # Due to limitations in Python and Enums, it is not possible to inherit these Enums from an base class.

    NOT_STARTED = 100
    "Indicates that the Kill Chain has not started."
    SUCCEEDED = 200
    "Indicates that the kill chain has succeeded."
    FAILED = 300
    "Indicates that the attack has failed."

    def initial_stage(self) -> "InsiderKillChain":
        """Returns the first stage in the kill chain. Used by Abstract TAP for TAP Agent Setup."""
        return self.RECONNAISSANCE


class TAP003(AbstractTAP, discriminator="tap-003"):
    """
    TAP003 | Malicious Insider Corporal Pearson.

    Currently implements one kill chain: Backdoor & Vulnerability Creation.
    This Threat Actor Profile (TAP) aims to introduce subtle cyber attack.
    For example, the Backdoor & Vulnerability creation kill chain
    creates DENY firewall rules which do not trigger NMNE.
    Please see the TAP003-Kill-Chain-E2E.ipynb for more information.
    """

    class AgentSettingsSchema(AbstractTAP.AgentSettingsSchema):
        """Agent Settings Schema that enforces TAP003's `kill_chain` config to use the InsiderKillChainOptions."""

        kill_chain: InsiderKillChainOptions  # = Field(default_factory=lambda: MobileMalwareKillChainOptions())

    class ConfigSchema(AbstractTAP.ConfigSchema):
        """Config Schema for the TAP001 agent."""

        type: Literal["tap-003"] = "tap-003"
        agent_settings: "TAP003.AgentSettingsSchema" = Field(default_factory=lambda: TAP003.AgentSettingsSchema())

    config: ConfigSchema
    selected_kill_chain: Type[InsiderKillChain] = InsiderKillChain
    _current_acl: int = 0
    network_knowledge: Dict = {}  # TODO: more specific typing

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._change_password_target_host: str = ""
        """If we have just sent a change password request over SSH, this variable keeps track of the hostname."""
        self._ssh_target_host: str = ""
        """If we have just send a SSH_LOGIN request, keeps track of the hostname to which we are attempting to SSH."""
        self._next_account_change: Optional[Dict] = None
        self._num_acls = len(self.config.agent_settings.kill_chain.EXPLOIT.malicious_acls)

        self.network_knowledge: dict = {"credentials": {}, "current_session": {}}
        """Keep track of current network state based on responses after sending actions. Populated during PLANNING."""
        self.setup_agent()

    def _progress_kill_chain(self) -> None:
        """Private Method used to progress the kill chain to the next stage."""
        if self.next_kill_chain_stage == self.selected_kill_chain.EXPLOIT:  # Covering final stage edge case.
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
        1. Loads the inherited attribute 'selected_kill_chain' with the InsiderKillChain
        2. Selects the starting node from the given user tap settings
        3. Selects the target node from the given user tap settings
        4. Sets the next execution timestep to the given user tap settings - start step
        5. Sets TAP's current host as the selected starting node.
        """
        # TAP Boilerplate Setup
        self._setup_agent_kill_chain(InsiderKillChain)

        # TAP003 Specific Setup
        self._select_start_node()
        self._set_next_execution_timestep(self.config.agent_settings.start_step)
        self.current_host = self.starting_node

    def get_action(self, obs: ObsType, timestep: int) -> Tuple[str, Dict]:
        """Follows the TAP003 Backdoor Vulnerability Kill Chain.

        Calls the next TAP003 Action Stage. Uses private methods to schedule kill chain stages.
        See TAP003-Kill-Chain-E2E.ipynb for further information on the TAP003 agent.

        :param obs: Current observation for this agent.
        :type obs: ObsType
        :param timestep: The current simulation timestep, used for scheduling actions
        :type timestep: int
        :return: Action formatted in CAOS format
        :rtype: Tuple[str, Dict]
        """
        self._handle_login_response()
        self._handle_change_password_response()
        if timestep < self.next_execution_timestep or self.actions_concluded:
            return "do-nothing", {}  # bypasses self.chosen_action

        # self.current_timestep is currently the previous execution timestep
        # So it can be used to index action history.
        if not self._tap_return_handler(self.current_timestep):
            # If the application is already installed, don't keep retrying - this is an acceptable fail
            if self.current_kill_chain_stage == InsiderKillChain.PLANNING:
                last_action = self.history[self.current_timestep].action
                fail_reason = self.history[self.current_timestep].response.data["reason"]
                if last_action == "node-application-install" and fail_reason == "already installed":
                    pass
            else:
                self.update_current_timestep(new_timestep=timestep)
                self._set_next_execution_timestep(timestep + self.config.agent_settings.frequency)
                self._tap_outcome_handler(InsiderKillChain)
                return self.chosen_action

        self.update_current_timestep(new_timestep=timestep)
        self._set_next_execution_timestep(timestep + self.config.agent_settings.frequency)
        self._tap_outcome_handler(InsiderKillChain)  # Handles successes and failures

        # The kill chain is called in reverse order
        # The kill chain sequence must be called in reverse order to ensure proper execution.

        self._exploit()
        self._manipulation()
        self._access()
        self._planning()
        self._reconnaissance()
        self._tap_start(InsiderKillChain)

        return self.chosen_action

    def _handle_login_response(self) -> None:
        """If the last request was an SSH login attempt, update the current session in network knowledge."""
        if not self.history:
            return
        last_hist_item = self.history[-1]
        if not last_hist_item.action == "node-session-remote-login" or last_hist_item.response.status != "success":
            return

        self.network_knowledge["current_session"] = {
            "hostname": self._ssh_target_host,
            "ip_address": last_hist_item.response.data["ip_address"],
            "username": last_hist_item.response.data["username"],
        }
        self.logger.debug(
            f"Updating network knowledge. Logged in as {last_hist_item.response.data['username']} on "
            f"{self._ssh_target_host}"
        )

    def _handle_change_password_response(self) -> None:
        if not self.history:
            return
        last_hist_item = self.history[-1]

        # when sending remote change password command, this must get populated
        if not self._change_password_target_host:
            return

        if (
            last_hist_item.action == "node-send-remote-command"
            and last_hist_item.parameters["command"][2] == "change_password"
            and last_hist_item.response.status == "success"
        ):
            # changing password logs us out, so our current session needs to be cleared
            self.network_knowledge["current_session"] = {}

            # update internal knowledge with the new password
            ip = last_hist_item.parameters["remote_ip"]
            username = last_hist_item.parameters["command"][3]
            password = last_hist_item.parameters["command"][5]
            hostname = self._change_password_target_host
            self.network_knowledge["credentials"][hostname] = {
                "ip_address": ip,
                "username": username,
                "password": password,
            }
            self.logger.debug(f"Updating network knowledge. Changed {username}'s password to {password} on {hostname}.")
            self._change_password_target_host = ""
        # local password change
        elif last_hist_item.action == "node-account-change-password" and last_hist_item.response.status == "success":
            self.network_knowledge["current_session"] = {}
            username = last_hist_item.request[6]
            password = last_hist_item.request[8]
            hostname = last_hist_item.request[2]
            self.network_knowledge["credentials"][hostname] = {"username": username, "password": password}
            self.logger.debug(f"Updating network knowledge. Changed {username}'s password to {password} on {hostname}.")
            self._change_password_target_host = ""

    def _reconnaissance(self) -> None:
        """Insider Kill Chain | Reconnaissance Stage.

        First stage in the Insider kill chain.

        Sets the self.chosen attribute to the "do-nothing" CAOS action
        and then calls the self._progress_kill_chain() method.
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.RECONNAISSANCE:
            self.chosen_action = "do-nothing", {}
            self._progress_kill_chain()

    def _planning(self) -> None:
        """Insider Kill Chain | Planning Stage.

        Second stage in the Insider kill chain.
        Performs a trial using the given user PLANNING stage probability.

        If the trial is successful then the agent populates its knowledge base with information from the config.

        Otherwise, the stage is not progressed. Additionally, the agent's kill chain is set
        to failure if the repeat_kill_chain_stages parameter is set to FALSE.
        """
        if not self.current_kill_chain_stage == self.selected_kill_chain.PLANNING:
            return

        if not self._agent_trial_handler(self.config.agent_settings.kill_chain.PLANNING.probability):
            if self.config.agent_settings.repeat_kill_chain_stages == False:
                self.current_kill_chain_stage = self.selected_kill_chain.FAILED
            self.chosen_action = "do-nothing", {}

        else:
            self.network_knowledge[
                "credentials"
            ] = self.config.agent_settings.kill_chain.PLANNING.starting_network_knowledge["credentials"]
            self.current_host = self.starting_node
            self.logger.info("Resolving starting knowledge.")
            self._progress_kill_chain()
        if self.current_stage_progress == KillChainStageProgress.PENDING:
            self.logger.info(f"TAP003 reached the {self.current_kill_chain_stage.name}")

    def _access(self) -> None:
        """Insider Kill Chain | Planning Stage.

        Third stage in the Insider kill chain.
        Performs a trial using the given user ACCESS stage probability.

        This currently does nothing.
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.ACCESS:
            if self._agent_trial_handler(self.config.agent_settings.kill_chain.ACCESS.probability):
                self._progress_kill_chain()
                self.chosen_action = "do-nothing", {}
            else:
                if self.config.agent_settings.repeat_kill_chain_stages == False:
                    self.current_kill_chain_stage = self.selected_kill_chain.FAILED
                self.chosen_action = "do-nothing", {}

    def _manipulation(self) -> None:
        """Insider Kill Chain | Manipulation Stage.

        Fourth stage in the Insider kill chain.
        Performs a trial using the given user MANIPULATION stage probability.

        If the trial is successful, the agent will change passwords for accounts that will later be used to execute
        malicious commands

        Otherwise if the stage is not progressed. Additionally, the agent's kill chain is set
        to failure if the repeat_kill_chain_stages parameter is set to FALSE.
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.MANIPULATION:
            if self._agent_trial_handler(self.config.agent_settings.kill_chain.MANIPULATION.probability):
                if self.current_stage_progress == KillChainStageProgress.PENDING:
                    self.logger.info(f"TAP003 reached the {self.current_kill_chain_stage.name}.")
                    self.current_stage_progress = KillChainStageProgress.IN_PROGRESS
                self.current_host = self.starting_node
                account_changes = self.config.agent_settings.kill_chain.MANIPULATION.account_changes
                if len(account_changes) > 0 or self._next_account_change:
                    if not self._next_account_change:
                        self._next_account_change = account_changes.pop(0)
                    if self._next_account_change["host"] == self.current_host:
                        # do a local password change
                        self.chosen_action = "node-account-change-password", {
                            "node_name": self.current_host,
                            "username": self._next_account_change["username"],
                            "current_password": self.network_knowledge["credentials"][self.current_host]["password"],
                            "new_password": self._next_account_change["new_password"],
                        }
                        self.logger.info("Changing local password.")
                        self._next_account_change = account_changes.pop(0)
                        self._change_password_target_host = self.current_host
                    else:
                        # make sure we are logged in via ssh to remote node
                        hostname = self._next_account_change["host"]
                        if self.network_knowledge.get("current_session", {}).get("hostname") != hostname:
                            self._ssh_target_host = hostname
                            self.chosen_action = "node-session-remote-login", {
                                "node_name": self.starting_node,
                                "username": self.network_knowledge["credentials"][hostname]["username"],
                                "password": self.network_knowledge["credentials"][hostname]["password"],
                                "remote_ip": self.network_knowledge["credentials"][hostname]["ip_address"],
                            }
                            self.logger.info(f"Logging into {hostname} in order to change password.")
                        # once we know we are logged in, send a command to change password
                        else:
                            self.chosen_action = "node-send-remote-command", {
                                "node_name": self.starting_node,
                                "remote_ip": self.network_knowledge["credentials"][hostname]["ip_address"],
                                "command": [
                                    "service",
                                    "user-manager",
                                    "change_password",
                                    self._next_account_change["username"],
                                    self.network_knowledge["credentials"][hostname]["password"],
                                    self._next_account_change["new_password"],
                                ],
                            }
                            self.logger.info(f"Changing password on remote node {hostname}")
                            try:
                                self._next_account_change = account_changes.pop(0)
                            except IndexError:
                                self.logger.info("No further account changes required.")
                                self._next_account_change = None
                            self._change_password_target_host = hostname
                if not self._next_account_change:
                    self.logger.info("Manipulation complete. Progressing to exploit...")
                    self._progress_kill_chain()
            else:
                if self.config.agent_settings.repeat_kill_chain_stages == False:
                    self.current_kill_chain_stage = self.selected_kill_chain.FAILED
                self.chosen_action = "do-nothing", {}

    def _exploit(self) -> None:
        """Insider Kill Chain | Exploit Stage.

        Fifth stage in the Insider kill chain.
        Performs a trial using the given user EXPLOIT stage probability.

        If the trial is successful then self.chosen_action attribute is set to the
        "node-send-remote-command" CAOS action with the "ROUTER_ACL_ADDRULE" as it's chosen command.

        The impact of the ROUTER_ACL_ADDRULE is dependant on user given parameters. At current
        the default impact of this stage is to block green agent traffic. An example of TAP003's
        manipulation stage in action can be found in the TAP003 notebook.

        Otherwise if the stage is not progressed. Additionally, the agent's kill chain is set
        to failure if the repeat_kill_chain_stages parameter is set to FALSE.
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.EXPLOIT:
            if self.current_kill_chain_stage == KillChainStageProgress.PENDING:
                # Perform the probability of success once upon entering the stage.
                if not self._agent_trial_handler(self.config.agent_settings.kill_chain.EXPLOIT.probability):
                    if self.config.agent_settings.repeat_kill_chain_stages == False:
                        self.current_kill_chain_stage = self.selected_kill_chain.FAILED
                    self.chosen_action = "do-nothing", {}
                    return
                self.current_kill_chain_stage = KillChainStageProgress.IN_PROGRESS

            self.config.agent_settings.kill_chain.EXPLOIT.malicious_acls = (
                self.config.agent_settings.kill_chain.EXPLOIT.malicious_acls
            )
            self._num_acls = len(self.config.agent_settings.kill_chain.EXPLOIT.malicious_acls)
            malicious_acl = self.config.agent_settings.kill_chain.EXPLOIT.malicious_acls[self._current_acl]
            hostname = malicious_acl.target_router

            if self.network_knowledge.get("current_session", {}).get("hostname") != hostname:
                self._ssh_target_host = hostname
                self.chosen_action = "node-session-remote-login", {
                    "node_name": self.starting_node,
                    "username": self.network_knowledge["credentials"][hostname]["username"],
                    "password": self.network_knowledge["credentials"][hostname]["password"],
                    "remote_ip": self.network_knowledge["credentials"][hostname]["ip_address"],
                }
                self.logger.info(f"Logging into {hostname} in order to add ACL rules.")
            # once we know we are logged in, send a command to change password
            else:
                self.chosen_action = "node-send-remote-command", {
                    "node_name": self.starting_node,
                    "remote_ip": self.network_knowledge["credentials"][hostname]["ip_address"],
                    "command": [
                        "acl",
                        "add_rule",
                        malicious_acl.permission,
                        malicious_acl.protocol_name,
                        str(malicious_acl.src_ip),
                        str(malicious_acl.src_wildcard),
                        malicious_acl.src_port,
                        str(malicious_acl.dst_ip),
                        str(malicious_acl.dst_wildcard),
                        malicious_acl.dst_port,
                        malicious_acl.position,
                    ],
                }
                self.logger.info(f"Adding ACL rule to {hostname}")
                self._current_acl = self._current_acl + 1

            if self._current_acl == self._num_acls:
                self._current_acl = 0
                self.logger.info("Finished adding ACL rules.")
                self._progress_kill_chain()
