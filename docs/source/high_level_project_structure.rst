Primaite Codebase Documentation
===============================

High-level structure
--------------------
The Primaite codebase consists of two main modules: the agent-training infrastructure and the simulation logic. These modules have been decoupled to allow for flexibility and modularity. The 'game' module acts as an interface between agents and the simulation.

Simulation
----------
The simulation module purely simulates a computer network. It has no concept of agents acting, but it can interact with agents by providing a 'state' dictionary (using the SimComponent describe_state() method) and by accepting requests (a list of strings).

Game layer
----------

The game layer is responsible for managing agents and getting them to interface with the simulator correctly. It consists of several components:

Observations
^^^^^^^^^^^^^^^^^^

The ObservationManager is responsible for generating observations from the simulator state dictionary. The data is formatted so it's compatible with Gymnasium.spaces. The ObservationManager is used by the AgentManager to generate observations for each agent.

Actions
^^^^^^^

The ActionManager is responsible for converting actions selected by agents (which comply with Gymnasium.spaces API) into simulation-friendly requests. The ActionManager is used by the AgentManager to take actions for each agent.

Rewards
^^^^^^^

The RewardManager is responsible for calculating rewards based on the state (similar to observations). The RewardManager is used by the AgentManager to calculate rewards for each agent.

Agents
^^^^^^

The AgentManager is responsible for managing agents and their interactions with the simulator. It uses the ObservationManager to generate observations for each agent, the ActionManager to take actions for each agent, and the RewardManager to calculate rewards for each agent.

PrimaiteSession
^^^^^^^^^^^^^^^

PrimaiteSession is the main entry point into Primaite and it allows the simultaneous coordination of a simulation and agents that interact with it. It also sends messages to ARCD GATE to perform reinforcement learning. PrimaiteSession uses the AgentManager to manage agents and their interactions with the simulator.

Code snippets
-------------
Here's an example of how to create a PrimaiteSession object:

.. code-block:: python

    from primaite import PrimaiteSession

    session = PrimaiteSession()

To start the simulation, use the start() method:

.. code-block:: python

    session.start()

To stop the simulation, use the stop() method:

.. code-block:: python

    session.stop()

To get the current state of the simulation, use the describe_state() method. This is also used as input for generating observations and rewards:

.. code-block:: python

    state = session.sim.describe_state()

To get the current observation of an agent, use the get_observation() method:

.. code-block:: python

    observation = session.get_observation(agent_id)

To get the current reward of an agent, use the get_reward() method:

.. code-block:: python

    reward = session.get_reward(agent_id)

To take an action for an agent, use the take_action() method:

.. code-block:: python

    action = agent.select_action(observation)
    session.take_action(agent_id, action)
