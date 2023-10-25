.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

.. _config:

The Config Files Explained
==========================

Note: This file describes the config files used in legacy PrimAITE v2.0. This file will be removed soon.

PrimAITE uses two configuration files for its operation:

* **The Training Config**

    Used to define the top-level settings of the PrimAITE environment, the reward values, and the session that is to be run.

* **The Lay Down Config**

    Used to define the low-level settings of a session, including the network laydown, green / red agent information exchange requirements (IERSs) and Access Control Rules.

Training Config:
*******************

The Training Config file consists of the following attributes:

**Generic Config Values**


* **agent_framework** [enum]

    This identifies the agent framework to be used to instantiate the agent algorithm. Select from one of the following:

    * NONE - Where a user developed agent is to be used
    * SB3 - Stable Baselines3
    * RLLIB - Ray RLlib.

* **agent_identifier**

    This identifies the agent to use for the session. Select from one of the following:

    * A2C - Advantage Actor Critic
    * PPO - Proximal Policy Optimization
    * HARDCODED - A custom built deterministic agent
    * RANDOM - A Stochastic random agent


* **random_red_agent** [bool]

    Determines if the session should be run with a random red agent

* **action_type** [enum]

    Determines whether a NODE, ACL, or ANY (combined NODE & ACL) action space format is adopted for the session


* **OBSERVATION_SPACE** [dict]

    Allows for user to configure observation space by combining one or more observation components. List of available
    components is in :py:mod:`primaite.environment.observations`.

    The observation space config item should have a ``components`` key which is a list of components. Each component
    config must have a ``name`` key, and can optionally have an ``options`` key. The ``options`` are passed to the
    component while it is being initialised.

    This example illustrates the correct format for the observation space config item

    .. code-block:: yaml

        observation_space:
        components:
          - name: NODE_LINK_TABLE
          - name: NODE_STATUSES
          - name: LINK_TRAFFIC_LEVELS
          - name: ACCESS_CONTROL_LIST
            options:
              combine_service_traffic : False
              quantisation_levels: 99


    Currently available components are:

      * :py:mod:`NODE_LINK_TABLE<primaite.environment.observations.NodeLinkTable>` this does not accept any additional options
      * :py:mod:`NODE_STATUSES<primaite.environment.observations.NodeStatuses>`, this does not accept any additional options
      * :py:mod:`ACCESS_CONTROL_LIST<primaite.environment.observations.AccessControlList>`, this does not accept additional options
      * :py:mod:`LINK_TRAFFIC_LEVELS<primaite.environment.observations.LinkTrafficLevels>`, this accepts the following options:

        * ``combine_service_traffic`` - whether to consider bandwidth use separately for each network protocol or combine them into a single bandwidth reading (boolean)
        * ``quantisation_levels`` - how many discrete bandwidth usage levels to use for encoding. This can be an integer equal to or greater than 3.

    The other configurable item is ``flatten`` which is false by default. When set to true, the observation space is flattened (turned into a 1-D vector). You should use this if your RL agent does not natively support observation space types like ``gym.Spaces.Tuple``.

* **num_train_episodes** [int]

    This defines the number of episodes that the agent will train for.


* **num_train_steps** [int]

    Determines the number of steps to run in each episode of the training session.


* **num_eval_episodes** [int]

    This defines the number of episodes that the agent will be evaluated over.


* **num_eval_steps** [int]

    Determines the number of steps to run in each episode of the evaluation session.


* **time_delay** [int]

    The time delay (in milliseconds) to take between each step when running a GENERIC agent session


* **session_type** [text]

    Type of session to be run (TRAINING, EVALUATION, or BOTH)

* **load_agent** [bool]

    Determine whether to load an agent from file

* **agent_load_file** [text]

    File path and file name of agent if you're loading one in

* **observation_space_high_value** [int]

    The high value to use for values in the observation space. This is set to 1000000000 by default, and should not need changing in most cases

* **implicit_acl_rule** [str]

    Determines which Explicit rule the ACL list has - two options are: DENY or ALLOW.

* **max_number_acl_rules** [int]

    Sets a limit on how many ACL rules there can be in the ACL list throughout the training session.

**Reward-Based Config Values**

Rewards are calculated based on the difference between the current state and reference state (the 'should be' state) of the environment.

* **Generic [all_ok]** [float]

    The score to give when the current situation (for a given component) is no different from that expected in the baseline (i.e. as though no blue or red agent actions had been undertaken)

* **Node Hardware State [off_should_be_on]** [float]

    The score to give when the node should be on, but is off

* **Node Hardware State [off_should_be_resetting]** [float]

    The score to give when the node should be resetting, but is off

* **Node Hardware State [on_should_be_off]** [float]

    The score to give when the node should be off, but is on

* **Node Hardware State [on_should_be_resetting]** [float]

    The score to give when the node should be resetting, but is on

* **Node Hardware State [resetting_should_be_on]** [float]

    The score to give when the node should be on, but is resetting

* **Node Hardware State [resetting_should_be_off]** [float]

    The score to give when the node should be off, but is resetting

* **Node Hardware State [resetting]** [float]

    The score to give when the node is resetting

* **Node Operating System or Service State [good_should_be_patching]** [float]

    The score to give when the state should be patching, but is good

* **Node Operating System or Service State [good_should_be_compromised]** [float]

    The score to give when the state should be compromised, but is good

* **Node Operating System or Service State [good_should_be_overwhelmed]** [float]

    The score to give when the state should be overwhelmed, but is good

* **Node Operating System or Service State [patching_should_be_good]** [float]

    The score to give when the state should be good, but is patching

* **Node Operating System or Service State [patching_should_be_compromised]** [float]

    The score to give when the state should be compromised, but is patching

* **Node Operating System or Service State [patching_should_be_overwhelmed]** [float]

    The score to give when the state should be overwhelmed, but is patching

* **Node Operating System or Service State [patching]** [float]

    The score to give when the state is patching

* **Node Operating System or Service State [compromised_should_be_good]** [float]

    The score to give when the state should be good, but is compromised

* **Node Operating System or Service State [compromised_should_be_patching]** [float]

    The score to give when the state should be patching, but is compromised

* **Node Operating System or Service State [compromised_should_be_overwhelmed]** [float]

    The score to give when the state should be overwhelmed, but is compromised

* **Node Operating System or Service State [compromised]** [float]

    The score to give when the state is compromised

* **Node Operating System or Service State [overwhelmed_should_be_good]** [float]

    The score to give when the state should be good, but is overwhelmed

* **Node Operating System or Service State [overwhelmed_should_be_patching]** [float]

    The score to give when the state should be patching, but is overwhelmed

* **Node Operating System or Service State [overwhelmed_should_be_compromised]** [float]

    The score to give when the state should be compromised, but is overwhelmed

* **Node Operating System or Service State [overwhelmed]** [float]

    The score to give when the state is overwhelmed

* **Node File System State [good_should_be_repairing]** [float]

    The score to give when the state should be repairing, but is good

* **Node File System State [good_should_be_restoring]** [float]

    The score to give when the state should be restoring, but is good

* **Node File System State [good_should_be_corrupt]** [float]

    The score to give when the state should be corrupt, but is good

* **Node File System State [good_should_be_destroyed]** [float]

    The score to give when the state should be destroyed, but is good

* **Node File System State [repairing_should_be_good]** [float]

    The score to give when the state should be good, but is repairing

* **Node File System State [repairing_should_be_restoring]** [float]

    The score to give when the state should be restoring, but is repairing

* **Node File System State [repairing_should_be_corrupt]** [float]

    The score to give when the state should be corrupt, but is repairing

* **Node File System State [repairing_should_be_destroyed]** [float]

    The score to give when the state should be destroyed, but is repairing

* **Node File System State [repairing]** [float]

    The score to give when the state is repairing

* **Node File System State [restoring_should_be_good]** [float]

    The score to give when the state should be good, but is restoring

* **Node File System State [restoring_should_be_repairing]** [float]

    The score to give when the state should be repairing, but is restoring

* **Node File System State [restoring_should_be_corrupt]** [float]

    The score to give when the state should be corrupt, but is restoring

* **Node File System State [restoring_should_be_destroyed]** [float]

    The score to give when the state should be destroyed, but is restoring

* **Node File System State [restoring]** [float]

    The score to give when the state is restoring

* **Node File System State [corrupt_should_be_good]** [float]

    The score to give when the state should be good, but is corrupt

* **Node File System State [corrupt_should_be_repairing]** [float]

    The score to give when the state should be repairing, but is corrupt

* **Node File System State [corrupt_should_be_restoring]** [float]

    The score to give when the state should be restoring, but is corrupt

* **Node File System State [corrupt_should_be_destroyed]** [float]

    The score to give when the state should be destroyed, but is corrupt

* **Node File System State [corrupt]** [float]

    The score to give when the state is corrupt

* **Node File System State [destroyed_should_be_good]** [float]

    The score to give when the state should be good, but is destroyed

* **Node File System State [destroyed_should_be_repairing]** [float]

    The score to give when the state should be repairing, but is destroyed

* **Node File System State [destroyed_should_be_restoring]** [float]

    The score to give when the state should be restoring, but is destroyed

* **Node File System State [destroyed_should_be_corrupt]** [float]

    The score to give when the state should be corrupt, but is destroyed

* **Node File System State [destroyed]** [float]

    The score to give when the state is destroyed

* **Node File System State [scanning]** [float]

    The score to give when the state is scanning

* **IER Status [red_ier_running]** [float]

    The score to give when a red agent IER is permitted to run

* **IER Status [green_ier_blocked]** [float]

    The score to give when a green agent IER is prevented from running

**Patching / Reset Durations**

* **os_patching_duration** [int]

    The number of steps to take when patching an Operating System

* **node_reset_duration** [int]

    The number of steps to take when resetting a node's hardware state

* **service_patching_duration** [int]

    The number of steps to take when patching a service

* **file_system_repairing_limit** [int]:

    The number of steps to take when repairing the file system

* **file_system_restoring_limit** [int]

    The number of steps to take when restoring the file system

* **file_system_scanning_limit** [int]

    The number of steps to take when scanning the file system

* **deterministic** [bool]

   Set to true if the agent evaluation should be deterministic. Default is ``False``

* **seed** [int]

   Seed used in the randomisation in agent training. Default is ``None``

The Lay Down Config
*******************

The lay down config file consists of the following attributes:


* **itemType: STEPS** [int]

* **item_type: PORTS** [int]

    Provides a list of ports modelled in this session

* **item_type: SERVICES** [freetext]

    Provides a list of services modelled in this session

* **item_type: NODE**

    Defines a node included in the system laydown being simulated. It should consist of the following attributes:

     * **id** [int]: Unique ID for this YAML item
     * **name** [freetext]: Human-readable name of the component
     * **node_class** [enum]: Relates to the base type of the node. Can be SERVICE, ACTIVE or PASSIVE. PASSIVE nodes do not have an operating system or services. ACTIVE nodes have an operating system, but no services. SERVICE nodes have both an operating system and one or more services
     * **node_type** [enum]: Relates to the component type. Can be one of CCTV, SWITCH, COMPUTER, LINK, MONITOR, PRINTER, LOP, RTU, ACTUATOR or SERVER
     * **priority** [enum]: Provides a priority for each node. Can be one of P1, P2, P3, P4 or P5 (which P1 being the highest)
     * **hardware_state** [enum]: The initial hardware state of the node. Can be one of ON, OFF or RESETTING
     * **ip_address** [IP address]: The IP address of the component in format xxx.xxx.xxx.xxx
     * **software_state** [enum]: The intial state of the node operating system. Can be GOOD, PATCHING or COMPROMISED
     * **file_system_state** [enum]: The initial state of the node file system. Can be GOOD, CORRUPT, DESTROYED, REPAIRING or RESTORING
     * **services**: For each service associated with the node:

        * **name** [freetext]: Free-text name of the service, but must match one of the services defined for the system in the services list
        * **port** [int]: Integer value of the port related to this service, but must match one of the ports defined for the system in the ports list
        * **state** [enum]: The initial state of the service. Can be one of GOOD, PATCHING, COMPROMISED or OVERWHELMED

* **item_type: LINK**

    Defines a link included in the system laydown being simulated. It should consist of the following attributes:

     * **id** [int]: Unique ID for this YAML item
     * **name** [freetext]: Human-readable name of the component
     * **bandwidth** [int]: The bandwidth (in bits/s) of the link
     * **source** [int]: The ID of the source node
     * **destination** [int]: The ID of the destination node

* **item_type: GREEN_IER**

    Defines a green agent Information Exchange Requirement (IER). It should consist of:

     * **id** [int]: Unique ID for this YAML item
     * **start_step** [int]: The start step (in the episode) for this IER to begin
     * **end_step** [int]: The end step (in the episode) for this IER to finish
     * **load** [int]: The load (in bits/s) for this IER to apply to links
     * **protocol** [freetext]: The protocol to apply to the links. This must match a value in the services list
     * **port** [int]: The port that the protocol is running on. This must match a value in the ports list
     * **source** [int]: The ID of the source node
     * **destination** [int]: The ID of the destination node
     * **mission_criticality** [enum]: The mission criticality of this IER (with 5 being highest, 1 lowest)

* **item_type: RED_IER**

    Defines a red agent Information Exchange Requirement (IER). It should consist of:

     * **id** [int]: Unique ID for this YAML item
     * **start_step** [int]: The start step (in the episode) for this IER to begin
     * **end_step** [int]: The end step (in the episode) for this IER to finish
     * **load** [int]: The load (in bits/s) for this IER to apply to links
     * **protocol** [freetext]: The protocol to apply to the links. This must match a value in the services list
     * **port** [int]: The port that the protocol is running on. This must match a value in the ports list
     * **source** [int]: The ID of the source node
     * **destination** [int]: The ID of the destination node
     * **mission_criticality** [enum]: Not currently used. Default to 0

* **item_type: GREEN_POL**

    Defines a green agent pattern-of-life instruction. It should consist of:

      * **id** [int]: Unique ID for this YAML item
      * **start_step** [int]: The start step (in the episode) for this PoL to begin
      * **end_step** [int]: Not currently used. Default to same as start step
      * **nodeId** [int]: The ID of the node to apply the PoL to
      * **type** [enum]: The type of PoL to apply. Can be one of OPERATING, OS or SERVICE
      * **protocol** [freetext]: The protocol to be affected if SERVICE type is chosen. Must match a value in the services list
      * **state** [enuum]: The state to apply to the node (which represents the PoL change). Can be one of ON, OFF or RESETTING (for node state) or GOOD, PATCHING or COMPROMISED (for Software State) or GOOD, PATCHING, COMPROMISED or OVERWHELMED (for service state)

* **item_type: RED_POL**

    Defines a red agent pattern-of-life instruction. It should consist of:

      * **id** [int]: Unique ID for this YAML item
      * **start_step** [int]: The start step (in the episode) for this PoL to begin
      * **end_step** [int]: Not currently used. Default to same as start step
      * **targetNodeId** [int]: The ID of the node to apply the PoL to
      * **initiator** [enum]: What initiates the PoL. Can be DIRECT, IER or SERVICE
      * **type** [enum]: The type of PoL to apply. Can be one of OPERATING, OS or SERVICE
      * **protocol** [freetext]: The protocol to be affected if SERVICE type is chosen. Must match a value in the services list
      * **state** [enum]: The state to apply to the node (which represents the PoL change). Can be one of ON, OFF or RESETTING (for node state) or GOOD, PATCHING or COMPROMISED (for Software State) or GOOD, PATCHING, COMPROMISED or OVERWHELMED (for service state) or GOOD, CORRUPT, DESTROYED, REPAIRING or RESTORING (for file system state)
      * **sourceNodeId** [int] The ID of the source node containing the service to check (used for SERVICE initiator)
      * **sourceNodeService** [freetext]: The service on the source node to check (used for SERVICE initiator). Must match a value in the services list for this node
      * **sourceNodeServiceState** [enum]: The state of the source node service to check (used for SERVICE initiator). Can be one of GOOD, PATCHING, COMPROMISED or OVERWHELMED

* **item_type: ACL_RULE**

    Defines an initial Access Control List (ACL) rule. It should consist of:

      * **id** [int]: Unique ID for this YAML item
      * **permission** [enum]: Defines either an allow or deny rule. Value must be either DENY or ALLOW
      * **source** [IP address]: Defines the source IP address for the rule in xxx.xxx.xxx.xxx format
      * **destination** [IP address]: Defines the destination IP address for the rule in xxx.xxx.xxx.xxx format
      * **protocol** [freetext]: Defines the protocol for the rule. Must match a value in the services list
      * **port** [int]: Defines the port for the rule. Must match a value in the ports list
      * **position** [int]: Defines where to place the ACL rule in the list. Lower index or (higher up in the list) means they are checked first. Index starts at 0 (Python indexes).
