Custom Agents
=============


**Integrating a user defined blue agent**

Integrating a blue agent with PrimAITE requires some modification of the code within the main.py file. The main.py file
consists of a number of functions, each of which will invoke training for a particular agent. These are:

* Generic (run_generic)
* Stable Baselines 3 PPO (:func:`~primaite.main.run_stable_baselines3_ppo)
* Stable Baselines 3 A2C (:func:`~primaite.main.run_stable_baselines3_a2c)

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
