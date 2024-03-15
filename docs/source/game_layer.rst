PrimAITE Game layer
*******************

The Primaite codebase consists of two main modules:

* ``simulator``: The simulation logic including the network topology, the network state, and behaviour of various hardware and software classes.
* ``game``: The agent-training infrastructure which helps reinforcement learning agents interface with the simulation. This includes the observation, action, and rewards, for RL agents, but also scripted deterministic agents. The game layer orchestrates all the interactions between modules.

The simulator and game layer communicate using the PrimAITE State API and the PrimAITE Request API.

The game layer is responsible for managing agents and getting them to interface with the simulator correctly. It consists of several components:

PrimAITE Session
================

.. admonition:: Deprecated
   :class: deprecated

   PrimAITE Session is being deprecated in favour of Jupyter Notebooks. The `session` command will be removed in future releases, but example notebooks will be provided to demonstrate the same functionality.

``PrimaiteSession`` is the main entry point into Primaite and it allows the simultaneous coordination of a simulation and agents that interact with it. ``PrimaiteSession`` keeps track of multiple agents of different types.

Agents
======

All agents inherit from the :py:class:`primaite.game.agent.interface.AbstractAgent` class, which mandates that they have an ObservationManager, ActionManager, and RewardManager. The agent behaviour depends on the type of agent, but there are two main types:

* RL agents action during each step is decided by an appropriate RL algorithm. The agent within PrimAITE just acts to format and forward actions decided by an RL policy.
* Deterministic agents perform all of their decision making within the PrimAITE game layer. They typically have a scripted policy which always performs the same action or a rule-based policy which performs actions based on the current state of the simulation. They can have a stochastic element, and their seed is settable.


Observations
============

An agent's observations are managed by the ``ObservationManager`` class. It generates observations based on the current simulation state dictionary. It also provides the observation space during initial setup. The data is formatted so it's compatible with ``Gymnasium.spaces``. Observation spaces are composed of one or more components which are defined by the ``AbstractObservation`` base class.

Actions
=======

An agent's actions are managed by the ``ActionManager``. It converts actions selected by agents (which are typically integers chosen from a ``gymnasium.spaces.Discrete`` space) into simulation-friendly requests. It also provides the action space during initial setup. Action spaces are composed of one or more components which are defined by the ``AbstractAction`` base class.

Rewards
=======

An agent's reward function is managed by the ``RewardManager``. It calculates rewards based on the simulation state (in a way similar to observations). Rewards can be defined as a weighted sum of small reward components. For example, an agents reward can be based on the uptime of a database service plus the loss rate of packets between clients and a web server.

Reward Components
-----------------

Currently implemented are reward components tailored to the data manipulation scenario. View the full API and description of how they work here: :py:module:`primaite.game.agent.reward`.

Reward Sharing
--------------

An agent's reward can be based on rewards of other agents. This is particularly useful for modelling a situation where the blue agent's job is to protect the ability of green agents to perform their pattern-of-life. This can be configured in the YAML file this way:

```yaml
green_agent_1: # this agent sometimes tries to access the webpage, and sometimes the database
    # actions, observations, and agent settings go here
    reward_function:
      reward_components:

        # When the webpage loads, the reward goes up by 0.25 when it fails to load, it goes down to -0.25
        - type: WEBPAGE_UNAVAILABLE_PENALTY
          weight: 0.25
          options:
            node_hostname: client_2

        # When the database is reachable, the reward goes up by 0.05, when it is unreachable it goes down to -0.05
        - type: GREEN_ADMIN_DATABASE_UNREACHABLE_PENALTY
          weight: 0.05
          options:
            node_hostname: client_2

blue_agent:
    # actions, observations, and agent settings go here
    reward_function:
      reward_components:

        # When the database file is in a good state, blue's reward is 0.4, when it's in a corrupted state the reward is -0.4
        - type: DATABASE_FILE_INTEGRITY
          weight: 0.40
          options:
            node_hostname: database_server
            folder_name: database
            file_name: database.db

        # The green's reward is added onto the blue's reward.
        - type: SHARED_REWARD
          weight: 1.0
          options:
            agent_name: client_2_green_user

```

When defining agent reward sharing, users must be careful to avoid circular references, as that would lead to an infinite calculation loop. PrimAITE will prevent circular dependencies and provide a helpful error message if they are detected in the yaml.
