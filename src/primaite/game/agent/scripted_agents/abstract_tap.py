# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

import random
from abc import abstractmethod
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, ConfigDict, Field

from primaite.game.agent.interface import AbstractScriptedAgent
from primaite.game.science import simulate_trial


# This class is required for abstract tap. The IntEnums in this class are repeated in other kill chains.
class BaseKillChain(IntEnum):
    """A generic kill chain for abstract tap initialisation.

    The IntEnums in this class are repeated in other kill chains
    As IntEnums cannot be directly extended by a inheritance.
    """

    NOT_STARTED = 100
    "Indicates that the Kill Chain has not started."
    SUCCEEDED = 200
    "Indicates that the kill chain has succeeded."
    FAILED = 300
    "Indicates that the attack has failed."

    # The original approach is to extend the base class during runtime via class methods.
    # However, this approach drastically impacted the readability and complexity of the code
    # So the decision was made to ignore the DRY Principle for kill chains.

    @abstractmethod
    def initial_stage(self) -> "BaseKillChain":
        """Returns the first stage in the kill chain. Used for Abstract TAP Setup."""
        return self.NOT_STARTED


class KillChainStageProgress(Enum):
    """Generic Progress Enums. Used by TAP Agents to keep track of kill chain stages that required multiple actions."""

    PENDING = 0
    """Indicates that the current kill chain stage is yet to start."""
    IN_PROGRESS = 1
    """Indicates that the current kill chain stage is not yet completed."""
    FINISHED = 2
    """Indicates that the current kill chain stage stage has been completed."""


class KillChainOptions(BaseModel):
    """Base Class for Kill Chain Options. Inherited by all TAP Type Agents."""

    model_config = ConfigDict(extra="forbid")


class KillChainStageOptions(BaseModel):
    """Shared options for generic Kill Chain Stages."""

    model_config = ConfigDict(extra="forbid")
    probability: float = 1


class AbstractTAP(AbstractScriptedAgent):
    """Abstract class for Threat Actor Persona (TAP) Type Agents must inherit from.

    This abstract base class provides TAP agents an interface which provides
    TAP type agents the necessary methods to execute kill chain(s) with
    configurable parameters.

    TAP Actions are returned to the Request Manager as a Tuple
    in CAOS format via the get_action method in line with other agents.

    Abstract TAP Class intends to provide each TAP the following:

    1. Kill Chain Progression

    Kill Chains are IntEnums which define the different stages within a kill chain.
    These stages are intended to be used across multiple ARCD environments.

    2. Abstract Methods For Kill Chain Control Flow

    Abstract methods _progress_kill_chain & _setup_kill_chain
    are intended to provide TAP type agent additional control
    over execution flow in comparison to AbstractScriptedAgent.

    Usually these methods handle kill chain progression & success criteria.

    For more information about Abstract TAPs please refer
    to the methods & attributes documentation directly.

    Additionally, Refer to a specific TAP for a more specific example.
    """

    class AgentSettingsSchema(AbstractScriptedAgent.AgentSettingsSchema):
        """Agent Settings Schema. Default settings applied for all threat actor profiles."""

        start_step: int = 5
        frequency: int = 5
        variance: int = 0
        repeat_kill_chain: bool = False
        repeat_kill_chain_stages: bool = True
        starting_nodes: Optional[List[str]] = []
        default_starting_node: str
        kill_chain: KillChainOptions

    class ConfigSchema(AbstractScriptedAgent.ConfigSchema):
        """Configuration schema applicable to all TAP agents."""

        agent_settings: "AbstractTAP.AgentSettingsSchema" = Field(
            default_factory=lambda: AbstractTAP.AgentSettingsSchema()
        )

    config: ConfigSchema = Field(default_factory=lambda: AbstractTAP.ConfigSchema())

    selected_kill_chain: Type[BaseKillChain]
    """A combination of TAP's base & default kill chain. Loaded dynamically during agent setup."""
    next_execution_timestep: int = 0
    """The next timestep in which the agent will attempt to progress the kill chain."""
    starting_node: str = ""
    """The name (string) of TAP agent's starting node. This attribute is initialised via _self_select_starting_node."""

    actions_concluded: bool = False
    """Boolean value which indicates if a TAP Agent has completed it's attack for the episode."""

    next_kill_chain_stage: BaseKillChain = BaseKillChain.NOT_STARTED
    """The IntEnum of the next kill chain stage to be executed.

       This attribute is initialised via _tap_start.
       Afterwards, this attribute is loaded dynamically via _progress_kill_chain.
    """
    current_kill_chain_stage: BaseKillChain = BaseKillChain.NOT_STARTED
    """The TAP agent's current kill chain.

        This attribute is used as a state to indicate the current progress in a kill chain.
    """
    current_stage_progress: KillChainStageProgress = KillChainStageProgress.PENDING
    """The TAP agent's current progress in a stage within a kill chain.

        This attribute is used as a state to indicate the current progress in a individual kill chain stage.

        Some TAP's require multiple actions to take place before moving onto the next stage in a kill chain.
        This attribute is used to keep track of the current progress within an individual stage.
    """
    chosen_action: Tuple[str, Dict] = "do-nothing", {}
    """The next agent's chosen action. Returned in CAOS format at the end of each timestep."""

    current_host: str = ""
    """The name (str) of a TAP agent's currently selected host.

       This attribute is set dynamically during tap execution via _set_current_host.
       """
    current_timestep: int = 0
    """The current timestep (int) of the game.

        This attribute is set to the "timestep" argument passed to get_action.
        Mainly used to by kill chain stages for complex execution flow that is dependant on the simulation.

        Specifically, this attribute is used for indexing previous actions in the self.history inherited attribute.

        For more information please refer to AbstractAgent's "self.history" attribute
        And for action responses see 'request.py' and the .data attribute.

        Lastly, a demonstration of the above capability can be found in the PROPAGATE step in the tap001-e2e notebook.
        """

    def update_current_timestep(self, new_timestep: int):
        """Updates the current time_step attribute to the given timestep argument."""
        self.current_timestep = new_timestep

    @abstractmethod
    def _progress_kill_chain(self):
        """Private Abstract method which defines the default kill chain progression.

        This abstract method intend to allow TAPs to control the logic flow of their kill chain.
        In a majority of cases this method handles the success criteria and incrementing the current kill chain intenum.

        This method is abstract so TAPs can configure this behaviour for tap specific implementations.
        """
        pass

    def _select_start_node(self) -> None:
        """
        Handles setting the starting node behaviour of TAP type agents.

        If the user given tap_settings provides a starting_node list then the starting node
        is set to a random node given in the starting_node list.
        Otherwise, the starting node is set to the 'default_starting_node' option.
        """
        # Catches empty starting nodes.
        if not self.config.agent_settings.starting_nodes:
            self.starting_node = self.config.agent_settings.default_starting_node
        else:
            self.starting_node = random.choice(self.config.agent_settings.starting_nodes)

    def _setup_agent_kill_chain(self, given_kill_chain: BaseKillChain) -> None:
        """Sets the 'next_kill_chain_stage' TAP attribute via the public kill chain method 'initial_stage'."""
        self.selected_kill_chain = given_kill_chain
        self.next_kill_chain_stage = self.selected_kill_chain.initial_stage(given_kill_chain)

    def _set_next_execution_timestep(self, timestep: int) -> None:
        """Set the next execution timestep with a configured random variance.

        :param timestep: The timestep to add variance to.
        """
        random_timestep_increment = random.randint(
            -self.config.agent_settings.variance, self.config.agent_settings.variance
        )
        self.next_execution_timestep = timestep + random_timestep_increment

    def _agent_trial_handler(self, agent_probability_of_success: int) -> bool:
        """Acts as a wrapper around simulate trial - Sets kill chain stage to failed if the relevant setting is set.

        :param agent_probability_of_success: The probability of the action success to be passed to simulate_trial.
        :type agent_probability_of_success: int.
        :rtype: Bool.
        """
        if simulate_trial(agent_probability_of_success):
            return True
        else:
            self.logger.info(
                f"failed to reach kill chain stage {self.next_kill_chain_stage.name} due to probability of failure."
            )
            if self.config.agent_settings.repeat_kill_chain_stages == False:
                self.logger.info(f"Thus {self.config.ref} has failed the kill chain")
                self.current_kill_chain_stage = self.selected_kill_chain.FAILED
                return False
            else:
                self.logger.info(f"Retrying from stage {self.current_kill_chain_stage.name}.")
            return False

    def _tap_outcome_handler(self, selected_kill_chain_class: BaseKillChain) -> None:
        """
        Default TAP behaviour for base kill chain stages.

        Upon Success and failure:
        TAPs will either repeat or re-attack dependant on the user given settings.

        :param tap_kill_chain: The TAP agent's currently selected kill chain.
        :type tap_kill_chain: BaseKillChain
        """
        if (
            self.current_kill_chain_stage == self.selected_kill_chain.SUCCEEDED
            or self.current_kill_chain_stage == self.selected_kill_chain.FAILED
        ):
            if self.actions_concluded == True:  # Prevents Further logging via a guard clause boolean
                self.chosen_action = "do-nothing", {}
                return
            if self.current_kill_chain_stage == self.selected_kill_chain.SUCCEEDED:
                self.logger.info(f"{self.config.ref} has successfully carried out the kill chain.")
            if self.current_kill_chain_stage == self.selected_kill_chain.FAILED:
                self.logger.info(f"{self.config.ref} has failed the Kill Chain.")
            if self.config.agent_settings.repeat_kill_chain == True:
                self.logger.info(f"{self.config.ref} has opted to re-attack!")
                self.current_kill_chain_stage = BaseKillChain.NOT_STARTED
                self.next_kill_chain_stage = selected_kill_chain_class.initial_stage(selected_kill_chain_class)
            else:
                self.logger.info(f"{self.config.ref} has opted to forgo any further attacks.")
                self.actions_concluded = True  # Guard Clause Bool
            self.chosen_action = "do-nothing", {}

    def _tap_return_handler(self, timestep: int) -> bool:
        # Intelligence | Use the request_response system to enable different behaviour
        """
        Handles the request_manager's response query. Sets Kill Chain to false if failed.

        If the previous action failed due to the simulation state,
        the kill chain is considered to have failed.

        Returns True if the previous action was successful.
        Returns False if the previous action was any other state.
        (Including Pending and Failure)

        :param timestep: The current primAITE game layer timestep.
        :type timestep: int
        :rtype bool
        """
        if self.history[timestep].response.status != "success":
            self.logger.info(
                f"{self.config.ref} has failed to successfully carry out {self.current_kill_chain_stage.name}"
            )
            self.logger.info(f"due to the simulation state: {self.history[timestep].response.data}")
            if self.config.agent_settings.repeat_kill_chain_stages == False:
                self.logger.info(
                    f"Thus {self.config.ref} has failed this kill chain attempt on {self.current_kill_chain_stage.name}"
                )
                self.current_kill_chain_stage = self.selected_kill_chain.FAILED
            else:
                self.logger.info(f"Retrying from stage {self.current_kill_chain_stage.name}!")
            return False
        return True

    def _tap_start(self, tap_kill_chain: Type[BaseKillChain]) -> None:
        """
        Sets the TAP Agent's beginning current/next kill chain stages.

        :param IntEnum tap_kill_chain: A currently selected kill chain.
        """
        if self.current_kill_chain_stage == self.selected_kill_chain.NOT_STARTED:
            self.current_kill_chain_stage = tap_kill_chain.initial_stage(tap_kill_chain)
            self.next_kill_chain_stage = self.selected_kill_chain(self.current_kill_chain_stage + 1)
            self.logger.info(f"{self.config.ref} has begun it's attack!")
            self.chosen_action = "do-nothing", {}
