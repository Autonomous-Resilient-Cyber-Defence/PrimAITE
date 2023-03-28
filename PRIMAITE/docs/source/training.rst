.. _training:

Running a PrimAITE Training Session
===================================

A PrimAITE training session will usually be associated with a "Training Use Case Profile". This document will present:

* The Use Case name, default number of steps in a training episode and default number of episodes in a training session. The number of steps and episodes can be modified in the configuration files
* The system laydown being modelled
* The objectives of the mission (steady-state), the red agent and the blue agent (in a defensive role)
* The green agent pattern-of-life profile
* The red agent attack profile
* The observation space definition
* The action space definition
* Agent integration guidance
* Initial Access Control List settings (if applicable)
* The reward function definition

**Integrating a user defined blue agent**

Integrating a blue agent with PrimAITE requires some modification of the code within the main.py file. The main.py file consists of a number of functions, each of which will invoke training for a particular agent. These are:

* Generic (run_generic)
* Stable Baselines 3 PPO (run_stable_baselines3_ppo)
* Stable Baselines 3 A2C (run_stable_baselines3_a2c)

The selection of which agent type to use is made via the config_main.yaml file. In order to train a user generated agent, 
the run_generic function should be selected, and should be modified (typically) to be:

.. code:: python

    agent = MyAgent(environment, max_steps)​
    for episode in range(0, num_episodes):​
        agent.learn()      ​
    env.close()​
    save_agent(agent)

Where:

* *MyAgent* is the user created agent
* *environment* is the PrimAITE environment
* *max_steps* is the number of steps in an episode, as defined in the config_[name].yaml file
* *num_episodes* is the number of episodes in the training session, as defined in the config_main.yaml file
* the *.learn()* function should be defined in the user created agent
* the *env.close()* function is defined within PrimAITE
* the *save_agent()* assumes that a *save()* function has been defined in the user created agent. If not, this line can be ommitted (although it is encouraged, since it will allow the agent to be saved and ported)

The code below provides a suggested format for the learn() function within the user created agent.
It's important to include the *self.environment.reset()* call within the episode loop in order that the 
environment is reset between episodes. Note that the example below should not be considered exhaustive.

.. code:: python

    def learn(self) :​

    # pre-reqs​​

    # reset the environment​
    self.environment.reset()​
    done = False​
    
    for step in range(max_steps):​
        # calculate the action​
        action = ...

        ​# execute the environment step​
        new_state, reward, done, info = self.environment.step(action)​

        # algorithm updates​
        ...

        # update to our new state​
        state = new_state​

        # if done, finish episode​
        if done == True:​
            break

**Running the training session**
 
In order to execute a training session, carry out the following steps:

1. Navigate to "[Install directory]\\PRIMAITE\\PRIMAITE\\” 
2. Start a console window (type “CMD” in path window, or start a console window first and navigate to “[Install Directory]\\PRIMAITE\\PRIMAITE\\”) 
3. Type “python main.py” 
4. Training will start with an output indicating the current episode, and average reward value for the episode 

 
