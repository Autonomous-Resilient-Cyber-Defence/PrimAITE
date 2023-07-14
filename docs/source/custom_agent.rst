Custom Agents
=============


Integrating a user defined blue agent
*************************************

.. note::

    If you are planning to implement custom RL agents into PrimAITE, you must use the project as a repository. If you install PrimAITE as a python package from wheel, custom agents are not supported.

PrimAITE has integration with Ray RLLib and StableBaselines3 agents. All agents interface with PrimAITE through an :py:class:`primaite.agents.agent.AgentSessionABC<Agent Session>` which provides Input/Output of agent savefiles, as well as capturing and plotting performance metrics during training and evaluation. If you wish to integrate a custom blue agent, it is recommended to create a subclass of the :py:class:`primaite.agents.agent.AgentSessionABC` and implement the ``__init__()``, ``_setup()``,  ``_save_checkpoint()``, ``learn()``, ``evaluate()``, ``_get_latest_checkpoint``, ``load()``, and ``save()`` methods.

Below is a barebones example of a custom agent implementation:

.. code:: python

    # src/primaite/agents/my_custom_agent.py

    from primaite.agents.agent import AgentSessionABC
    from primaite.common.enums import AgentFramework, AgentIdentifier

    class CustomAgent(AgentSessionABC):
        def __init__(self, training_config_path, lay_down_config_path):
            super().__init__(training_config_path, lay_down_config_path)
            assert self._training_config.agent_framework == AgentFramework.CUSTOM
            assert self._training_config.agent_identifier == AgentIdentifier.MY_AGENT
            self._setup()

        def _setup(self):
            super()._setup()
            self._env = Primaite(
                training_config_path=self._training_config_path,
                lay_down_config_path=self._lay_down_config_path,
                session_path=self.session_path,
                timestamp_str=self.timestamp_str,
        )
            self._agent = ... # your code to setup agent

        def _save_checkpoint(self):
            checkpoint_num = self._training_config.checkpoint_every_n_episodes
            episode_count = self._env.episode_count
            save_checkpoint = False
            if checkpoint_num:
                save_checkpoint = episode_count % checkpoint_num == 0
            # saves checkpoint if the episode count is not 0 and save_checkpoint flag was set to true
            if episode_count and save_checkpoint:
                ...
                # your code to save checkpoint goes here.
                # The path should start with self.checkpoints_path and include the episode number.

        def learn(self):
            ...
            # call your agent's learning function here.

            super().learn() # this will finalise learning and output session metadata
            self.save()

        def evaluate(self):
            ...
            # call your agent's evaluation function here.

            self._env.close()
            super().evaluate()

        def _get_latest_checkpoint(self):
            ...
            # Load an agent from file.

        @classmethod
        def load(cls, path):
            ...
            # Create a CustomAgent object which loads model weights from file.

        def save(self):
            ...
            # Call your agent's function that saves it to a file


You will also need to modify :py:class:`primaite.primaite_session.PrimaiteSession<PrimaiteSession>` and :py:mod:`primaite.common.enums` to capture your new agent identifiers.

.. code-block:: python
    :emphasize-lines: 17, 18

    # src/primaite/common/enums.py

    class AgentIdentifier(Enum):
        """The Red Agent algo/class."""
        A2C = 1
        "Advantage Actor Critic"
        PPO = 2
        "Proximal Policy Optimization"
        HARDCODED = 3
        "The Hardcoded agents"
        DO_NOTHING = 4
        "The DoNothing agents"
        RANDOM = 5
        "The RandomAgent"
        DUMMY = 6
        "The DummyAgent"
        CUSTOM_AGENT = 7
        "Your custom agent"

.. code-block:: python
    :emphasize-lines: 3, 11, 12

    # src/primaite_session.py

    from primaite.agents.my_custom_agent import CustomAgent

    # ...

        def setup(self):
        """Performs the session setup."""
        if self._training_config.agent_framework == AgentFramework.CUSTOM:
            _LOGGER.debug(f"PrimaiteSession Setup: Agent Framework = {AgentFramework.CUSTOM}")
            if self._training_config.agent_identifier == AgentIdentifier.CUSTOM_AGENT:
                self._agent_session = CustomAgent(self._training_config_path, self._lay_down_config_path)
            if self._training_config.agent_identifier == AgentIdentifier.HARDCODED:
                _LOGGER.debug(f"PrimaiteSession Setup: Agent Identifier =" f" {AgentIdentifier.HARDCODED}")
                if self._training_config.action_type == ActionType.NODE:
                    # Deterministic Hardcoded Agent with Node Action Space
                    self._agent_session = HardCodedNodeAgent(self._training_config_path, self._lay_down_config_path)

Finally, specify your agent in your training config.

.. code-block:: yaml

    # ~/primaite/config/path/to/your/config_main.yaml

    # Training Config File

    agent_framework: CUSTOM
    agent_identifier: CUSTOM_AGENT
    random_red_agent: False
    # ...

Now you can :ref:`run a primaite session<run a primaite session>` with your custom agent by passing in the custom ``config_main``.
