.. _config:

The Config Files Explained
==========================

PrimAITE uses two configuration files for its operation:

* config_main.yaml - used to define the top-level settings of the PrimAITE environment, and the session that is to be run.
* config_[name].yaml - used to define the low-level settings of a session, including the network laydown, green / red agent information exchange requirements (IERSs), Access Control Rules, Action Space type, and the number of steps in each episode.

config_main.yaml:
*****************

The config_main.yaml file consists of the following attributes:

**Generic Config Values**

* **agentIdentifier** [enum]

   This identifies the agent to use for the session. Select from one of the following:

   * GENERIC - Where a user developed agent is to be used
   * STABLE_BASELINES3_PPO - Use a SB3 PPO agent
   * STABLE_BASELINES3_A2C - use a SB3 A2C agent

* **numEpisodes** [int]

   This defines the number of episodes that the agent will train or be evaluated over. Each episode consists of a number of steps (with step number defined in the config_[name].yaml file)

* **timeDelay** [int]

   The time delay (in milliseconds) to take between each step when running a GENERIC agent session

* **configFilename** [filename]

   The name of the config_[name].yaml file to use for this session

* **sessionType** [text]

   Type of session to be run (TRAINING or EVALUATION)

* **loadAgent** [bool]

   Determine whether to load an agent from file

* **agentLoadFile** [text]

   File path and file name of agent if you're loading one in

* **observationSpaceHighValue** [int]

   The high value to use for values in the observation space. This is set to 1000000000 by default, and should not need changing in most cases

**Reward-Based Config Values**

* **Generic [allOk]** [int]

   The score to give when the current situation (for a given component) is no different from that expected in the baseline (i.e. as though no blue or red agent actions had been undertaken)

* **Node Hardware State [offShouldBeOn]** [int]

   The score to give when the node should be on, but is off

* **Node Hardware State [offShouldBeResetting]** [int]

   The score to give when the node should be resetting, but is off

* **Node Hardware State [onShouldBeOff]** [int]

   The score to give when the node should be off, but is on

* **Node Hardware State [onShouldBeResetting]** [int]

   The score to give when the node should be resetting, but is on

* **Node Hardware State [resettingShouldBeOn]** [int]

   The score to give when the node should be on, but is resetting

* **Node Hardware State [resettingShouldBeOff]** [int]

   The score to give when the node should be off, but is resetting

* **Node Hardware State [resetting]** [int]

   The score to give when the node is resetting

* **Node Operating System or Service State [goodShouldBePatching]** [int]

   The score to give when the state should be patching, but is good

* **Node Operating System or Service State [goodShouldBeCompromised]** [int]

   The score to give when the state should be compromised, but is good

* **Node Operating System or Service State [goodShouldBeOverwhelmed]** [int]

   The score to give when the state should be overwhelmed, but is good

* **Node Operating System or Service State [patchingShouldBeGood]** [int]

   The score to give when the state should be good, but is patching

* **Node Operating System or Service State [patchingShouldBeCompromised]** [int]

   The score to give when the state should be compromised, but is patching

* **Node Operating System or Service State [patchingShouldBeOverwhelmed]** [int]

   The score to give when the state should be overwhelmed, but is patching

* **Node Operating System or Service State [patching]** [int]

   The score to give when the state is patching

* **Node Operating System or Service State [compromisedShouldBeGood]** [int]

   The score to give when the state should be good, but is compromised

* **Node Operating System or Service State [compromisedShouldBePatching]** [int]

   The score to give when the state should be patching, but is compromised

* **Node Operating System or Service State [compromisedShouldBeOverwhelmed]** [int]

   The score to give when the state should be overwhelmed, but is compromised

* **Node Operating System or Service State [compromised]** [int]

   The score to give when the state is compromised

* **Node Operating System or Service State [overwhelmedShouldBeGood]** [int]

   The score to give when the state should be good, but is overwhelmed

* **Node Operating System or Service State [overwhelmedShouldBePatching]** [int]

   The score to give when the state should be patching, but is overwhelmed

* **Node Operating System or Service State [overwhelmedShouldBeCompromised]** [int]

   The score to give when the state should be compromised, but is overwhelmed

* **Node Operating System or Service State [overwhelmed]** [int]

   The score to give when the state is overwhelmed

* **Node File System State [goodShouldBeRepairing]** [int]

    The score to give when the state should be repairing, but is good

* **Node File System State [goodShouldBeRestoring]** [int]

    The score to give when the state should be restoring, but is good

* **Node File System State [goodShouldBeCorrupt]** [int]

    The score to give when the state should be corrupt, but is good

* **Node File System State [goodShouldBeDestroyed]** [int]

    The score to give when the state should be destroyed, but is good

* **Node File System State [repairingShouldBeGood]** [int]

    The score to give when the state should be good, but is repairing

* **Node File System State [repairingShouldBeRestoring]** [int]

    The score to give when the state should be restoring, but is repairing

* **Node File System State [repairingShouldBeCorrupt]** [int]

    The score to give when the state should be corrupt, but is repairing

* **Node File System State [repairingShouldBeDestroyed]** [int]

    The score to give when the state should be destroyed, but is repairing

* **Node File System State [repairing]** [int]

    The score to give when the state is repairing

* **Node File System State [restoringShouldBeGood]** [int]

    The score to give when the state should be good, but is restoring

* **Node File System State [restoringShouldBeRepairing]** [int]

    The score to give when the state should be repairing, but is restoring

* **Node File System State [restoringShouldBeCorrupt]** [int]

    The score to give when the state should be corrupt, but is restoring

* **Node File System State [restoringShouldBeDestroyed]** [int]

    The score to give when the state should be destroyed, but is restoring

* **Node File System State [restoring]** [int]

    The score to give when the state is restoring

* **Node File System State [corruptShouldBeGood]** [int]

    The score to give when the state should be good, but is corrupt

* **Node File System State [corruptShouldBeRepairing]** [int]

    The score to give when the state should be repairing, but is corrupt

* **Node File System State [corruptShouldBeRestoring]** [int]

    The score to give when the state should be restoring, but is corrupt

* **Node File System State [corruptShouldBeDestroyed]** [int]

    The score to give when the state should be destroyed, but is corrupt

* **Node File System State [corrupt]** [int]

    The score to give when the state is corrupt

* **Node File System State [destroyedShouldBeGood]** [int]

    The score to give when the state should be good, but is destroyed

* **Node File System State [destroyedShouldBeRepairing]** [int]

    The score to give when the state should be repairing, but is destroyed

* **Node File System State [destroyedShouldBeRestoring]** [int]

    The score to give when the state should be restoring, but is destroyed

* **Node File System State [destroyedShouldBeCorrupt]** [int]

    The score to give when the state should be corrupt, but is destroyed

* **Node File System State [destroyed]** [int]

    The score to give when the state is destroyed

* **Node File System State [scanning]** [int]

    The score to give when the state is scanning

* **IER Status [redIerRunning]** [int]

   The score to give when a red agent IER is permitted to run

* **IER Status [greenIerBlocked]** [int]

   The score to give when a green agent IER is prevented from running

**Patching / Reset Durations**

* **osPatchingDuration** [int]

   The number of steps to take when patching an Operating System

* **nodeResetDuration** [int]

   The number of steps to take when resetting a node's hardware state

* **servicePatchingDuration** [int]

   The number of steps to take when patching a service

* **fileSystemRepairingLimit** [int]:

   The number of steps to take when repairing the file system

* **fileSystemRestoringLimit** [int]

   The number of steps to take when restoring the file system

* **fileSystemScanningLimit** [int]

   The number of steps to take when scanning the file system

config_[name].yaml:
*******************

The config_[name].yaml file consists of the following attributes:

* **itemType: ACTIONS** [enum]

   Determines whether a NODE or ACL action space format is adopted for the session

* **itemType: OBSERVATION_SPACE** [dict]

   Allows for user to configure observation space by combining one or more observation components. List of available
   components is is :py:mod:'primaite.environment.observations'.

   The observation space config item should have a ``components`` key which is a list of components. Each component
   config must have a ``name`` key, and can optionally have an ``options`` key. The ``options`` are passed to the
   component while it is being initialised.

   This example illustrates the correct format for the observation space config item

.. code-block::yaml

   - itemType: OBSERVATION_SPACE
     components:
     - name: LINK_TRAFFIC_LEVELS
       options:
         combine_service_traffic: false
         quantisation_levels: 8
     - name: NODE_STATUSES
     - name: LINK_TRAFFIC_LEVELS

* **itemType: STEPS** [int]

   Determines the number of steps to run in each episode of the session

* **itemType: PORTS** [int]

   Provides a list of ports modelled in this session

* **itemType: SERVICES** [freetext]

   Provides a list of services modelled in this session

* **itemType: NODE**

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

* **itemType: LINK**

   Defines a link included in the system laydown being simulated. It should consist of the following attributes:

     * **id** [int]: Unique ID for this YAML item
     * **name** [freetext]: Human-readable name of the component
     * **bandwidth** [int]: The bandwidth (in bits/s) of the link
     * **source** [int]: The ID of the source node
     * **destination** [int]: The ID of the destination node

* **itemType: GREEN_IER**

   Defines a green agent Information Exchange Requirement (IER). It should consist of:

     * **id** [int]: Unique ID for this YAML item
     * **startStep** [int]: The start step (in the episode) for this IER to begin
     * **endStep** [int]: The end step (in the episode) for this IER to finish
     * **load** [int]: The load (in bits/s) for this IER to apply to links
     * **protocol** [freetext]: The protocol to apply to the links. This must match a value in the services list
     * **port** [int]: The port that the protocol is running on. This must match a value in the ports list
     * **source** [int]: The ID of the source node
     * **destination** [int]: The ID of the destination node
     * **missionCriticality** [enum]: The mission criticality of this IER (with 5 being highest, 1 lowest)

* **itemType: RED_IER**

   Defines a red agent Information Exchange Requirement (IER). It should consist of:

     * **id** [int]: Unique ID for this YAML item
     * **startStep** [int]: The start step (in the episode) for this IER to begin
     * **endStep** [int]: The end step (in the episode) for this IER to finish
     * **load** [int]: The load (in bits/s) for this IER to apply to links
     * **protocol** [freetext]: The protocol to apply to the links. This must match a value in the services list
     * **port** [int]: The port that the protocol is running on. This must match a value in the ports list
     * **source** [int]: The ID of the source node
     * **destination** [int]: The ID of the destination node
     * **missionCriticality** [enum]: Not currently used. Default to 0

* **itemType: GREEN_POL**

    Defines a green agent pattern-of-life instruction. It should consist of:

      * **id** [int]: Unique ID for this YAML item
      * **startStep** [int]: The start step (in the episode) for this PoL to begin
      * **endStep** [int]: Not currently used. Default to same as start step
      * **nodeId** [int]: The ID of the node to apply the PoL to
      * **type** [enum]: The type of PoL to apply. Can be one of OPERATING, OS or SERVICE
      * **protocol** [freetext]: The protocol to be affected if SERVICE type is chosen. Must match a value in the services list
      * **state** [enuum]: The state to apply to the node (which represents the PoL change). Can be one of ON, OFF or RESETTING (for node state) or GOOD, PATCHING or COMPROMISED (for Software State) or GOOD, PATCHING, COMPROMISED or OVERWHELMED (for service state)

* **itemType: RED_POL**

    Defines a red agent pattern-of-life instruction. It should consist of:

      * **id** [int]: Unique ID for this YAML item
      * **startStep** [int]: The start step (in the episode) for this PoL to begin
      * **endStep** [int]: Not currently used. Default to same as start step
      * **targetNodeId** [int]: The ID of the node to apply the PoL to
      * **initiator** [enum]: What initiates the PoL. Can be DIRECT, IER or SERVICE
      * **type** [enum]: The type of PoL to apply. Can be one of OPERATING, OS or SERVICE
      * **protocol** [freetext]: The protocol to be affected if SERVICE type is chosen. Must match a value in the services list
      * **state** [enum]: The state to apply to the node (which represents the PoL change). Can be one of ON, OFF or RESETTING (for node state) or GOOD, PATCHING or COMPROMISED (for Software State) or GOOD, PATCHING, COMPROMISED or OVERWHELMED (for service state) or GOOD, CORRUPT, DESTROYED, REPAIRING or RESTORING (for file system state)
      * **sourceNodeId** [int] The ID of the source node containing the service to check (used for SERVICE initiator)
      * **sourceNodeService** [freetext]: The service on the source node to check (used for SERVICE initiator). Must match a value in the services list for this node
      * **sourceNodeServiceState** [enum]: The state of the source node service to check (used for SERVICE initiator). Can be one of GOOD, PATCHING, COMPROMISED or OVERWHELMED

* **itemType: ACL_RULE**

    Defines an initial Access Control List (ACL) rule. It should consist of:

      * **id** [int]: Unique ID for this YAML item
      * **permission** [enum]: Defines either an allow or deny rule. Value must be either DENY or ALLOW
      * **source** [IP address]: Defines the source IP address for the rule in xxx.xxx.xxx.xxx format
      * **destination** [IP address]: Defines the destination IP address for the rule in xxx.xxx.xxx.xxx format
      * **protocol** [freetext]: Defines the protocol for the rule. Must match a value in the services list
      * **port** [int]: Defines the port for the rule. Must match a value in the ports list
