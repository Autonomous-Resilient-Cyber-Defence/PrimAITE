.. _config:

The Config Files Explained
==========================

PrimAITE uses two configuration files for its operation:

* config_main.yaml - used to define the top-level settings of the PrimAITE environment, and the training session that is to be run.
* config_[name].yaml - used to define the low-level settings of a training session, including the network laydown, green / red agent information exchange requirements (IERSs), Access Control Rules, Action Space type, and the number of steps in each episode.

config_main.yaml:
*****************

The config_main.yaml file consists of the following attributes:

**Generic Config Values**

* **agentIdentifier** [enum]

   This identifies the agent to use for the training session. Select from one of the following:

   * GENERIC - Where a user developed agent is to be used
   * STABLE_BASELINES3_PPO - Use a SB3 PPO agent
   * STABLE_BASELINES3_A2C - use a SB3 A2C agent

* **numEpisodes** [int]

   This defines the number of episodes that the agent will train over. Each episode consists of a number of steps (with step number defined in the config_[name].yaml file)

* **timeDelay** [int]

   The time delay (in milliseconds) to take between each step when training a GENERIC agent

* **configFilename** [filename]

   The name of the config_[name].yaml file to use for this training session

* **observationSpaceHighValue** [int]

   The high value to use for values in the observation space. This is set to 1000000000 by default, and should not need changing in most cases

**Reward-Based Config Values**

* **Generic [allOk]** [int]

   The score to give when the current situation (for a given component) is no different from that expected in the baseline (i.e. as though no blue or red agent actions had been undertaken)

* **Node Operating State [offShouldBeOn]** [int]

   The score to give when the node should be on, but is off

* **Node Operating State [offShouldBeResetting]** [int]

   The score to give when the node should be resetting, but is off

* **Node Operating State [onShouldBeOff]** [int]
    
   The score to give when the node should be off, but is on

* **Node Operating State [onShouldBeResetting]** [int]
    
   The score to give when the node should be resetting, but is on

* **Node Operating State [resettingShouldBeOn]** [int]
    
   The score to give when the node should be on, but is resetting

* **Node Operating State [resettingShouldBeOff]** [int]
    
   The score to give when the node should be off, but is resetting

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

* **IER Status [redIerRunning]** [int]
    
   The score to give when a red agent IER is permitted to run

* **IER Status [greenIerBlocked]** [int]
    
   The score to give when a green agent IER is prevented from running

**Patching / Reset Durations**

* **osPatchingDuration** [int]

   The number of steps to take when patching an Operating System

* **nodeResetDuration** [int]
   
   The number of steps to take when resetting a node's operating state

* **servicePatchingDuration** [int]
   
   The number of steps to take when patching a service

config_[name].yaml:
*******************

The config_[name].yaml file consists of the following attributes:

* **itemType: ACTIONS** [enum]
   
   Determines whether a NODE or ACL action space format is adopted for the training session

* **itemType: STEPS** [int]
    
   Determines the number of steps to run in each episode of the training session

* **itemType: PORTS** [int]
   
   Provides a list of ports modelled in this training session

* **itemType: SERVICES** [freetext]
   
   Provides a list of services modelled in this training session

* **itemType: NODE**
    
   Defines a node included in the system laydown being simulated. It should consist of the following attributes:

     * **id** [int]: Unique ID for this YAML item
     * **name** [freetext]: Human-readable name of the component
     * **baseType** [enum]: Relates to the base type of the node. Can be SERVICE, ACTIVE or PASSIVE. PASSIVE nodes do not have an operating system or services. ACTIVE nodes have an operating system, but no services. SERVICE nodes have both an operating system and one or more services
     * **nodeType** [enum]: Relates to the component type. Can be one of CCTV, SWITCH, COMPUTER, LINK, MONITOR, PRINTER, LOP, RTU, ACTUATOR or SERVER
     * **priority** [enum]: Provides a priority for each node. Can be one of P1, P2, P3, P4 or P5 (which P1 being the highest)
     * **hardwareState** [enum]: The initial hardware state of the node. Can be one of ON, OFF or RESETTING
     * **ipAddress** [IP address]: The IP address of the component in format xxx.xxx.xxx.xxx
     * **softwareState** [enum]: The intial state of the node operating system. Can be GOOD, PATCHING or COMPROMISED
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
      * **node** [int]: The ID of the node to apply the PoL to
      * **type** [enum]: The type of PoL to apply. Can be one of OPERATING, OS or SERVICE
      * **protocol** [freetext]: The protocol to be affected if SERVICE type is chosen. Must match a value in the services list
      * **state** [enuum]: The state to apply to the node (which represents the PoL change). Can be one of ON, OFF or RESETTING (for node state) or GOOD, PATCHING or COMPROMISED (for operating system state) or GOOD, PATCHING, COMPROMISED or OVERWHELMED (for service state)

* **itemType: RED_POL**
     
    Defines a red agent pattern-of-life instruction. It should consist of:

      * **id** [int]: Unique ID for this YAML item
      * **startStep** [int]: The start step (in the episode) for this PoL to begin
      * **endStep** [int]: Not currently used. Default to same as start step
      * **node** [int]: The ID of the node to apply the PoL to
      * **type** [enum]: The type of PoL to apply. Can be one of OPERATING, OS or SERVICE
      * **protocol** [freetext]: The protocol to be affected if SERVICE type is chosen. Must match a value in the services list
      * **state** [enum]: The state to apply to the node (which represents the PoL change). Can be one of ON, OFF or RESETTING (for node state) or GOOD, PATCHING or COMPROMISED (for operating system state) or GOOD, PATCHING, COMPROMISED or OVERWHELMED (for service state)
      * **isEntryNode** [bool]: Defines whether the node affected is an entry node to the system

* **itemType: ACL_RULE**
     
    Defines an initial Access Control List (ACL) rule. It should consist of:

      * **id** [int]: Unique ID for this YAML item
      * **permission** [enum]: Defines either an allow or deny rule. Value must be either DENY or ALLOW
      * **source** [IP address]: Defines the source IP address for the rule in xxx.xxx.xxx.xxx format
      * **destination** [IP address]: Defines the destination IP address for the rule in xxx.xxx.xxx.xxx format
      * **protocol** [freetext]: Defines the protocol for the rule. Must match a value in the services list
      * **port** [int]: Defines the port for the rule. Must match a value in the ports list