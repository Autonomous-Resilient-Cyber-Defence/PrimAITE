PrimAITE Game layer
*******************

The Primaite codebase consists of two main modules:

* ``simulator``: The simulation logic including the network topology, the network state, and behaviour of various hardware and software classes.
* ``game``: The agent-training infrastructure which helps reinforcement learning agents interface with the simulation. This includes the observation, action, and rewards, for RL agents, but also scripted deterministic agents. The game layer orchestrates all the interactions between modules.

 The simulator and game layer communicate using the PrimAITE State API and the PrimAITE Request API.

..
    TODO: write up these APIs and link them here.


Game layer
----------

The game layer is responsible for managing agents and getting them to interface with the simulator correctly. It consists of several components:

PrimAITE Session
^^^^^^^^^^^^^^^

``PrimaiteSession`` is the main entry point into Primaite and it allows the simultaneous coordination of a simulation and agents that interact with it. ``PrimaiteSession`` keeps track of multiple agents of different types.

Agents
^^^^^^

All agents inherit from the :py:class:`primaite.game.agent.interface.AbstractAgent` class, which mandates that they have an ObservationManager, ActionManager, and RewardManager. The agent behaviour depends on the type of agent, but there are two main types:

* RL agents action during each step is decided by an appropriate RL algorithm. The agent within PrimAITE just acts to format and forward actions decided by an RL policy.
* Deterministic agents perform all of their decision making within the PrimAITE game layer. They typically have a scripted policy which always performs the same action or a rule-based policy which performs actions based on the current state of the simulation. They can have a stochastic element, and their seed will be settable.

..
    TODO: add seed to stochastic scripted agents

Observations
^^^^^^^^^^^^^^^^^^

An agent's observations are managed by the ``ObservationManager`` class. It generates observations based on the current simulation state dictionary. It also provides the observation space during initial setup. The data is formatted so it's compatible with ``Gymnasium.spaces``. Observation spaces are composed of one or more components which are defined by the ``AbstractObservation`` base class.

Actions
^^^^^^^

An agent's actions are managed by the ``ActionManager``. It converts actions selected by agents (which are typically integers chosen from a ``gymnasium.spaces.Discrete`` space) into simulation-friendly requests. It also provides the action space during initial setup. Action spaces are composed of one or more components which are defined by the ``AbstractAction`` base class.

Rewards
^^^^^^^

An agent's reward function is managed by the ``RewardManager``. It calculates rewards based on the simulation state (in a way similar to observations). Rewards can be defined as a weighted sum of small reward components. For example, an agents reward can be based on the uptime of a database service plus the loss rate of packets between clients and a web server. The reward components are defined by the AbstractReward base class.
