.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK


``agents``
==========
Agents can be scripted (deterministic and stochastic), or controlled by a reinforcement learning algorithm. Not to be confused with an RL agent, the term agent here is used to refer to an entity that sends requests to the simulated network. In this part of the config, each agent's action space, observation space, and reward function can be defined. All three are defined in a modular way.

``agents`` hierarchy
--------------------

.. code-block:: yaml

    agents:
    - ref: red_agent_example
        ...
    - ref: blue_agent_example
        ...
    - ref: green_agent_example
    team: GREEN
    type: probabilistic-agent

    agent_settings:
      start_step: 5
      frequency: 4
      variance: 3
      flatten_obs: False

``ref``
-------
The reference to be used for the given agent.

``team``
--------
Specifies if the agent is malicious (``RED``), benign (``GREEN``), or defensive (``BLUE``). Currently this value is not used for anything other than for human readability in the configuration file.

``type``
--------
Specifies which class should be used for the agent. ``proxy-agent`` is used for agents that receive instructions from an RL algorithm. Scripted agents like ``red-database-corrupting-agent`` and ``probabilistic-agent`` generate their own behaviour.

Available agent types:

- ``probabilistic-agent``
- ``proxy-agent``
- ``red-database-corrupting-agent``

``observation_space``
---------------------
Defines the observation space of the agent.

``type``
^^^^^^^^

selects which python class from the :py:mod:`primaite.game.agent.observation` module is used for the overall observation structure.

``options``
^^^^^^^^^^^

Allows configuration of the chosen observation type. These are optional.

    * ``num_services_per_node``, ``num_folders_per_node``, ``num_files_per_folder``, ``num_nics_per_node`` all define the shape of the observation space. The size and shape of the obs space must remain constant, but the number of files, folders, acl rules, and other components can change within an episode. Therefore padding is performed and these options set the size of the obs space.
    * ``nodes``: list of nodes that will be present in this agent's observation space. The ``node_ref`` relates to the human-readable unique reference defined later in the ``simulation`` part of the config. Each node can also be configured with services, and files that should be monitored.
    * ``links``: list of links that will be present in this agent's observation space. The ``link_ref`` relates to the human-readable unique reference defined later in the ``simulation`` part of the config.
    * ``acl``: configure how the agent reads the access control list on the router in the simulation. ``router_node_ref`` is for selecting which router's acl table should be used. ``ip_list`` sets the encoding of ip addresses as integers within the observation space.

For more information see :py:mod:`primaite.game.agent.observations`

``action_space``
----------------

The action space is configured to be made up of individual action types. Once configured, the agent can select an action type and some optional action parameters at every step. For example: The ``NODE_SERVICE_SCAN`` action takes the parameters ``node_id`` and ``service_id``.


``action_map``
^^^^^^^^^^^^^^

Restricts the possible combinations of action type / action parameter values to reduce the overall size of the action space. By default, every possible combination of actions and parameters will be assigned an integer for the agent's ``MultiDiscrete`` action space. Instead, the ``action_map`` allows you to list the actions corresponding to each integer in the ``MultiDiscrete`` space.

This is Optional.

``options``
^^^^^^^^^^^

Options that apply to all action components. These are optional.

    * ``nodes``: list the nodes that the agent can act on, the order of this list defines the mapping between nodes and ``node_id`` integers.
    * ``max_folders_per_node``, ``max_files_per_folder``, ``max_services_per_node``, ``max_nics_per_node``, ``max_acl_rules`` all are used to define the size of the action space.

For more information see :py:mod:`primaite.game.agent.actions`

``reward_function``
-------------------

Similar to action space, this is defined as a list of components from the :py:mod:`primaite.game.agent.rewards` module.

``reward_components``
^^^^^^^^^^^^^^^^^^^^^
TODO: update description
A list of reward types from :py:mod:`primaite.game.agent.rewards.RewardFunction.rew_class_identifiers`

e.g.

.. code-block:: yaml

    reward_components:
        - type: dummy
        - type: database-file-integrity


``agent_settings``
------------------

Settings passed to the agent during initialisation. Determines how the agent will behave during training.

e.g.

.. code-block:: yaml

    agent_settings:
        start_settings:
            start_step: 25
            frequency: 20
            variance: 5

``start_step``
^^^^^^^^^^^^^^

Optional. Default value is ``5``.

The timestep where the agent begins performing actions.

``frequency``
^^^^^^^^^^^^^

Optional. Default value is ``5``.

The number of timesteps the agent will wait before performing another action.

``variance``
^^^^^^^^^^^^

Optional. Default value is ``0``.

The amount of timesteps that the frequency can randomly change.

``flatten_obs``
---------------

If ``True``, gymnasium flattening will be performed on the observation space before sending to the agent. Set this to ``True`` if your agent does not support nested observation spaces.

``Agent History``
-----------------

Agents will record their action log for each step. This is a summary of what the agent did, along with response information from requests within the simulation.
A summary of the actions taken by the agent can be viewed using the `show_history()` function. By default, this will display all actions taken apart from ``DONOTHING``.
