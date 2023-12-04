Primaite v3 config
******************

PrimAITE uses a single configuration file to define everything needed to train and evaluate an RL policy in a custom cybersecurity scenario. This includes the configuration of the network, the scripted or trained agents that interact with the network, as well as settings that define how to perform training in Stable Baselines 3 or Ray RLLib.
The entire config is used by the ``PrimaiteSession`` object for users who wish to let PrimAITE handle the agent definition and training. If you wish to define custom agents and control the training loop yourself, you can use the config with the ``PrimaiteGame``, and ``PrimaiteGymEnv`` objects instead. That way, only the network configuration and agent setup parts of the config are used, and the training section is ignored.

Configurable items
==================

``training_config``
-------------------
This section allows selecting which training framework and algorithm to use, and set some training hyperparameters.

``io_settings``
---------------
This section configures how the ``PrimaiteSession`` saves data.

``game``
--------
This section defines high-level settings that apply across the game, currently it's used to help shape the action and observation spaces by restricting which ports and internet protocols should be considered. Here, users can also set the maximum number of steps in an episode.

``agents``
----------
Agents can be scripted (deterministic and stochastic), or controlled by a reinforcement learning algorithm. Not to be confused with an RL agent, the term agent here is used to refer to an entity that sends requests to the simulated network. In this part of the config, each agent's action space, observation space, and reward function can be defined. All three are defined in a modular way.

**type**: Specifies which class should be used for the agent. ``ProxyAgent`` is used for agents that receive instructions from an RL algorithm. Scripted agents like ``RedDatabaseCorruptingAgent`` and ``GreenWebBrowsingAgent`` generate their own behaviour.

**team:**: Specifies if the agent is malicious (RED), benign (GREEN), or defensive (BLUE). Currently this value is not used for anything.

**observation space:**
    * ``type``: selects which python class from the ``primaite.game.agent.observation`` module is used for the overall observation structure.
    * ``options``: allows configuring the chosen observation type. The ``UC2BlueObservation`` should be used for RL Agents.
        * ``num_services_per_node``, ``num_folders_per_node``, ``num_files_per_folder``, ``num_nics_per_node`` all define the shape of the observation space. The size and shape of the obs space must remain constant, but the number of files, folders, ACL rules, and other components can change within an episode. Therefore padding is performed and these options set the size of the obs space.
        * ``nodes``: list of nodes that will be present in this agent's observation space. The ``node_ref`` relates to the human-readable unique reference defined later in the ``simulation`` part of the config. Each node can also be configured with services, and files that should be monitored.
        * ``links``: list of links that will be present in this agent's observation space. The ``link_ref`` relates to the human-readable unique reference defined later in the ``simulation`` part of the config.
        * ``acl``: configure how the agent reads the access control list on the router in the simulation. ``router_node_ref`` is for selecting which router's ACL table should be used. ``ip_address_order`` sets the encoding of ip addresses as integers within the observation space.

**action space:**
The action space is configured to be made up of individual action types. Once configured, the agent can select an action type and some optional action parameters at every step. For example: The ``NODE_SERVICE_SCAN`` action takes the parameters ``node_id`` and ``service_id``.

Description of configurable items:
    * ``action_list``: a list of action modules. The options are listed in the ``primaite.game.agent.actions`` module.
    * ``action_map``: (optional). Restricts the possible combinations of action type / action parameter values to reduce the overall size of the action space. By default, every possible combination of actions and parameters will be assigned an integer for the agent's ``MultiDiscrete`` action space. Instead, the action_map allows you to list the actions corresponding to each integer in the ``MultiDiscrete`` space.
    * ``options``: Options that apply too all action components.
        * ``nodes``: list the nodes that the agent can act on, the order of this list defines the mapping between nodes and ``node_id`` integers.
        * ``max_folders_per_node``, ``max_files_per_folder``, ``max_services_per_node``, ``max_nics_per_node``, ``max_acl_rules`` all are used to define the size of the action space.

**reward function:**
Similar to action space, this is defined as a list of components.

Description of configurable items:
    * ``reward_components`` a list of reward components from the ``primaite.game.agent.reward`` module.
        * ``weight``: relative importance of this reward component. The total reward for a step is a weighted sum of all reward components.
        * ``options``: list of options passed to the reward component during initialisation, the exact options required depend on the reward component.

**agent_settings**:
Settings passed to the agent during initialisation. These depend on the agent class.

``simulation``
--------------
In this section the network layout is defined. This part of the config follows a hierarchical structure. Almost every component defines a ``ref`` field which acts as a human-readable unique identifier, used by other parts of the config, such as agents.

At the top level of the network are ``nodes`` and ``links``.

**nodes:**
    * ``type``: one of ``router``, ``switch``, ``computer``, or ``server``, this affects what other sub-options should be defined.
    * ``hostname`` - a non-unique name used for logging and outputs.
    * ``num_ports`` (optional, routers and switches only): number of network interfaces present on the device.
    * ``ports`` (optional, routers and switches only): configuration for each network interface, including IP address and subnet mask.
    * ``acl`` (Router only): Define the ACL rules at each index of the ACL on the router. the possible options are: ``action`` (PERMIT or DENY), ``src_port``, ``dst_port``, ``protocol``, ``src_ip``, ``dst_ip``. Any options left blank default to none which usually means that it will apply across all options. For example leaving ``src_ip`` blank will apply the rule to all IP addresses.
    * ``services`` (computers and servers only): a list of services to install on the node. They must define a ``ref``, ``type``, and ``options`` that depend on which ``type`` was selected.
    * ``applications`` (computer and servers only): Similar to services. A list of application to install on the node.
    * ``nics`` (computers and servers only): If the node has multiple networking devices, the second, third, fourth, etc... must be defined here with an ``ip_address`` and ``subnet_mask``.

**links:**
    * ``ref``: unique identifier for this link
    * ``endpoint_a_ref``: Reference to the node at the first end of the link
    * ``endpoint_a_port``: The ethernet port or switch port index of the second node
    * ``endpoint_b_ref``: Reference to the node at the second end of the link
    * ``endpoint_b_port``: The ethernet port or switch port index on the second node
