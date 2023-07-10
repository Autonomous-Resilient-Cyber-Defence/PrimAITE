Custom Agents
=============


**Integrating a user defined blue agent**

PrimAITE has integration with Ray RLLib and StableBaselines3 agents. All agents interface with PrimAITE through an :py:class:`primaite.agents.agent.AgentSessionABC<Agent Session>` which provides Input/Output of agent savefiles, as well as capturing and plotting performance metrics during training. If you wish to integrate a custom blue agent, it is recommended to create a subclass of the :py:class:`primaite.agents.agent.AgentSessionABC` and implement the ``__init__()``, ``_setup()``,  ``_save_checkpoint()``, ``learn()``, ``evaluate()``, ``_get_latest_checkpoint``, ``load()``, ``save()``, and ``export()`` methods.

Below is a barebones example of a custom agent implementation:

.. code:: python

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
            #

        def save(self):
            ...
            # Call your agent's function that saves it to a file

        def export(self):
            ...
            # Call your agent's function that exports it to a transportable file format.


You will also need to modify :py:class:`primaite.primaite_session.PrimaiteSession<PrimaiteSession>` class to capture your new agent identifier.





The selection of which agent type to use is made via the training config file. In order to train a user generated agent,
the run_generic function should be selected, and should be modified (typically) to be:

.. code:: python

    agent = MyAgent(environment, num_steps)
    for episode in range(0, num_episodes):
        agent.learn()
    env.close()
    save_agent(agent)

Where:

* *MyAgent* is the user created agent
* *environment* is the :class:`~primaite.environment.primaite_env.Primaite` environment
* *num_episodes* is the number of episodes in the session, as defined in the training config file
* *num_steps* is the number of steps in an episode, as defined in the training config file
* the *.learn()* function should be defined in the user created agent
* the *env.close()* function is defined within PrimAITE
* the *save_agent()* assumes that a *save()* function has been defined in the user created agent. If not, this line can
  be ommitted (although it is encouraged, since it will allow the agent to be saved and ported)

The code below provides a suggested format for the learn() function within the user created agent.
It's important to include the *self.environment.reset()* call within the episode loop in order that the
environment is reset between episodes. Note that the example below should not be considered exhaustive.

.. code:: python

    def learn(self) :

    # pre-reqs

    # reset the environment
    self.environment.reset()
    done = False

    for step in range(max_steps):
        # calculate the action
        action = ...

        # execute the environment step
        new_state, reward, done, info = self.environment.step(action)

        # algorithm updates
        ...

        # update to our new state
        state = new_state

        # if done, finish episode
        if done == True:
            break
