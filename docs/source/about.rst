.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _about:

About PrimAITE
==============

The ARCD Primary-level AI Training Environment (**PrimAITE**) provides an effective simulation capability for training and evaluating AI in a cyber-defensive role. It incorporates the functionality required of a primary-level ARCD environment:

- The ability to model a relevant system context;
- Modelling an adversarial agent that the defensive agent can be trained and evaluated against;
- The ability to model key characteristics of a system by representing hosts, servers, network devices, IP addresses, ports, operating systems, folders / files, applications, services and links;
- Modelling background (green) pattern-of-life;
- Operates at machine-speed to enable fast training cycles via Reinforcement Learning (RL).

Features
^^^^^^^^

PrimAITE incorporates the following features:

- Architected with a separate Simulation layer and Game layer. This separation of concerns defines a clear path towards transfer learning with environments of differing fidelity;
- Ability to reconfigure an RL reward function based on (a) the ability to counter the modelled adversarial cyber-attack, and (b) the ability to ensure success for green agents;
- Access Control List (ACL) functions for network devices (routers and firewalls), following standard ACL rule format (e.g., DENY / ALLOW, source / destination IP addresses, protocol and port);
- Application of traffic to the links of the system laydown adheres to the ACL rulesets and routing tables contained within each network device;
- Provides RL environments adherent to the Farama Foundation Gymnasium (Previously OpenAI Gym) API, allowing integration with any compliant RL Agent frameworks;
- Provides RL environments adherent to Ray RLlib environment specifications for single-agent and multi-agent scenarios;
- Assessed for compatibility with Stable-Baselines3 (SB3), Ray RLlib, and bespoke agents;
- Persona-based adversarial (Red) agent behaviour; several out-the-box personas are provided, and more can be developed to suit the needs of the task. Stochastic variations in Red agent behaviour are also included as required;
- A robust system logging tool, automatically enabled at the node level and featuring various log levels and terminal output options, enables PrimAITE users to conduct in-depth network simulations;
- A PCAP service is seamlessly integrated within the simulation, automatically capturing and logging frames for both
  inbound and outbound traffic at the network interface level. This automatic functionality, combined with the ability
  to separate traffic directions, significantly enhances network analysis and troubleshooting capabilities;
- Agent action logs provide a description of every action taken by each agent during the episode. This includes timestep, action, parameters, request and response, for all Blue agent activity, which is aligned with the Track 2 Common Action / Observation Space (CAOS) format. Action logs also details of all scripted / stochastic red / green agent actions;
- Environment ground truth is provided at every timestep, providing a full description of the environment’s true state;
- Alignment with CAOS provides the ability to transfer agents between CAOS compliant environments.

Architecture
^^^^^^^^^^^^

PrimAITE is a Python application and will operate on multiple Operating Systems (Windows, Linux and macOS);
a comprehensive installation and user guide is provided with each release to support its usage.

Configuration of PrimAITE is achieved via included YAML files which support full control over the network / system laydown being modelled, background pattern of life, adversarial (red agent) behaviour, and step and episode count.
A Simulation Controller layer manages the overall running of the simulation, keeping track of all low-level objects.

It is agnostic to the number of agents, their action / observation spaces, and the RL library being used.

It presents a public API providing a method for describing the current state of the simulation, a method that accepts action requests and provides responses, and a method that triggers a timestep advancement.
The Game Layer converts the simulation into a playable game for the agent(s).

It translates between simulation state and Gymnasium.Spaces to pass action / observation data between the agent(s) and the simulation. It is responsible for calculating rewards, managing Multi-Agent RL (MARL) action turns, and via a single agent interface can interact with Blue, Red and Green agents.

Agents can either generate their own scripted behaviour or accept input behaviour from an RL agent.

Finally, a Gymnasium / Ray RLlib Environment Layer forwards requests to the Game Layer as the agent sends them. This layer also manages most of the I/O, such as reading in the configuration files and saving agent logs.

.. image:: ../../_static/primAITE_architecture.png
    :width: 500
    :align: center


Training & Evaluation Capability
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PrimAITE provides a training and evaluation capability to AI agents in the context of cyber-attack, via its Gymnasium / Ray RLlib compliant interface.

Scenarios can be constructed to reflect network / system laydowns consisting of any configuration of nodes (e.g. PCs, servers etc.) and the networking equipment and links between them.

All nodes can be configured to contain applications, services, folders and files (and their status).

Traffic flows between services and applications as directed by an ‘execution definition’ with the traffic flow on the network governed by the network equipment (switches, routers and firewalls) and the ACL rules and routing tables they employ.

Highlights of PrimAITE’s training and evaluation capability are:

- The scenario is not bound to a representation of any platform, system, or technology;
- Fully configurable (network / system laydown, green pattern-of-life, red personas, reward function, ACL rules for each device, number of episodes / steps, action / observation space) and repeatable to suit the requirements of AI agents;
- Can integrate with any Gymnasium / Ray RLlib compliant AI agent.


PrimAITE provides a number of use cases (network and red/green action configurations) by default which the user is able to extend and modify as required.

What is PrimAITE built with
---------------------------

* `Gymnasium <https://gymnasium.farama.org/>`_ is used as the basis for AI blue agent interaction with the PrimAITE environment
* `Networkx <https://github.com/networkx/networkx>`_ is used as the underlying data structure used for the PrimAITE environment
* `Stable Baselines 3 <https://github.com/DLR-RM/stable-baselines3>`_ is used as a default source of RL algorithms (although PrimAITE is not limited to SB3 agents)
* `Ray RLlib <https://github.com/ray-project/ray>`_ is used as an additional source of RL algorithms
* `Typer <https://github.com/tiangolo/typer>`_ is used for building CLIs (Command Line Interface applications)
* `Jupyterlab <https://github.com/jupyterlab/jupyterlab>`_ is used as an extensible environment for interactive and reproducible computing, based on the Jupyter Notebook Architecture
* `Platformdirs <https://github.com/platformdirs/platformdirs>`_ is used for finding the right location to store user data and configuration but varies per platform
* `Plotly <https://github.com/plotly/plotly.py>`_ is used for building high level charts


Getting Started with PrimAITE
-----------------------------

Head over to the :ref:`getting-started` page to install and setup PrimAITE!

..
  Architecture - Nodes and Links
  ******************************
  **Nodes**
  An inheritance model has been adopted in order to model nodes. All nodes have the following base attributes (Class: Node):
  * ID
  * Name
  * Type (e.g. computer, switch, RTU - enumeration)
  * Priority (P1, P2, P3, P4 or P5 - enumeration)
  * Hardware State (ON, OFF, RESETTING, SHUTTING_DOWN, BOOTING - enumeration)
  Active Nodes also have the following attributes (Class: Active Node):
  * IP Address
  * Software State (GOOD, FIXING, COMPROMISED - enumeration)
  * File System State (GOOD, CORRUPT, DESTROYED, REPAIRING, RESTORING - enumeration)
  Service Nodes also have the following attributes (Class: Service Node):
  * List of Services (where service is composed of service name and port). There is no theoretical limit on the number of services that can be modelled. Services and protocols are currently intrinsically linked (i.e. a service is an application on a node transmitting traffic of this protocol type)
  * Service state (GOOD, FIXING, COMPROMISED, OVERWHELMED - enumeration)
  Passive Nodes are currently not used (but may be employed for non IP-based components such as machinery actuators in future releases).
  **Links**
  Links are modelled both as network edges (networkx) and as Python classes, in order to extend their functionality. Links include the following attributes:
  * ID
  * Name
  * Bandwidth (bits/s)
  * Source node ID
  * Destination node ID
  * Protocol list (containing the loading of protocols currently running on the link)
  When the simulation runs, IERs are applied to the links in order to model traffic loading, individually assigned to each protocol. This allows green (background) and red agent behaviour to be modelled, and defensive agents to identify suspicious traffic patterns at a protocol / traffic loading level of fidelity.
  Information Exchange Requirements (IERs)
  ****************************************
  PrimAITE adopts the concept of Information Exchange Requirements (IERs) to model both green agent (background) and red agent (adversary) behaviour. IERs are used to initiate modelling of traffic loading on the network, and have the following attributes:
  * ID
  * Start step (i.e. which step in the training episode should the IER start)
  * End step (i.e. which step in the training episode should the IER end)
  * Source node ID
  * Destination node ID
  * Load (bits/s)
  * Protocol
  * Port
  * Running status (i.e. on / off)
  The application of green agent IERs between a source and destination follows a number of rules. Specifically:
  1. Does the current simulation time step fall between IER start and end step
  2. Is the source node operational (both physically and at an O/S level), and is the service (protocol / port) associated with the IER (a) present on this node, and (b) in an operational state (i.e. not FIXING)
  3. Is the destination node operational (both physically and at an O/S level), and is the service (protocol / port) associated with the IER (a) present on this node, and (b) in an operational state (i.e. not FIXING)
  4. Are there any Access Control List rules in place that prevent the application of this IER
  5. Are all switches in the (OSPF) path between source and destination operational (both physically and at an O/S level)
  For red agent IERs, the application of IERs between a source and destination follows a number of subtly different rules. Specifically:
  1. Does the current simulation time step fall between IER start and end step
  2. Is the source node operational, and is the service (protocol / port) associated with the IER (a) present on that node and (b) already in a compromised state
  3. Is the destination node operational, and is the service (protocol / port) associated with the IER present on that node
  4. Are there any Access Control List rules in place that prevent the application of this IER
  5. Are all switches in the (OSPF) path between source and destination operational (both physically and at an O/S level)
  Assuming the rules pass, the IER is applied to all relevant links (based on use of OSPF) between source and destination.
  Node Pattern-of-Life
  ********************
  Every node can be impacted (i.e. have a status change applied to it) by either green agent pattern-of-life or red agent pattern-of-life. This is distinct from IERs, and allows for attacks (and defence) to be modelled purely within the confines of a node.
  The status changes that can be made to a node are as follows:
  * All Nodes:
    * Hardware State:
        * ON
        * OFF
        * RESETTING - when a status of resetting is entered, the node will automatically exit this state after a number of steps (as defined by the nodeResetDuration configuration item) after which it returns to an ON state
        * BOOTING
        * SHUTTING_DOWN
  * Active Nodes and Service Nodes:
    * Software State:
        * GOOD
        * FIXING - when a status of FIXING is entered, the node will automatically exit this state after a number of steps (as defined by the osFIXINGDuration configuration item) after which it returns to a GOOD state
        * COMPROMISED
    * File System State:
        * GOOD
        * CORRUPT (can be resolved by repair or restore)
        * DESTROYED (can be resolved by restore only)
        * REPAIRING - when a status of repairing is entered, the node will automatically exit this state after a number of steps (as defined by the fileSystemRepairingLimit configuration item) after which it returns to a GOOD state
        * RESTORING - when a status of repairing is entered, the node will automatically exit this state after a number of steps (as defined by the fileSystemRestoringLimit configuration item) after which it returns to a GOOD state
  * Service Nodes only:
    * Service State (for any associated service):
        * GOOD
        * FIXING - when a status of FIXING is entered, the service will automatically exit this state after a number of steps (as defined by the serviceFIXINGDuration configuration item) after which it returns to a GOOD state
        * COMPROMISED
        * OVERWHELMED
  Red agent pattern-of-life has an additional feature not found in the green pattern-of-life. This is the ability to influence the state of the attributes of a node via a number of different conditions:
    * DIRECT:
    The pattern-of-life described by the configuration file item will be applied regardless of any other conditions in the network. This is particularly useful for direct red agent entry into the network.
    * IER:
    The pattern-of-life described by the configuration file item will be applied to the service on the node, only if there is an IER of the same protocol / service type incoming at the specified timestep.
    * SERVICE:
    The pattern-of-life described by the configuration file item will be applied to the node based on the state of a service. The service can either be on the same node, or a different node within the network.
  Access Control List modelling
  *****************************
  An Access Control List (ACL) is modelled to provide the means to manage traffic flows in the system. This will allow defensive agents the means to turn on / off rules, or potentially create new rules, to counter an attack.
  The ACL follows a standard network firewall format. For example:
  .. list-table:: ACL example
    :widths: 25 25 25 25 25
    :header-rows: 1
    * - Permission
      - Source IP
      - Dest IP
      - Protocol
      - Port
    * - DENY
      - 192.168.1.2
      - 192.168.1.3
      - HTTPS
      - 443
    * - ALLOW
      - 192.168.1.4
      - ANY
      - SMTP
      - 25
    * - DENY
      - ANY
      - 192.168.1.5
      - ANY
      - ANY
  All ACL rules are considered when applying an IER. Logic follows the order of rules, so a DENY or ALLOW for the same parameters will override an earlier entry.
  Observation Spaces
  ******************
  The observation space provides the blue agent with information about the current status of nodes and links.
  PrimAITE builds on top of Gymnasium Spaces to create an observation space that is easily configurable for users. It's made up of components which are managed by the :py:class:`primaite.environment.observations.ObservationsHandler`. Each training scenario can define its own observation space, and the user can choose which information to inlude, and how it should be formatted.
  NodeLinkTable component
  -----------------------
  For example, the :py:class:`primaite.environment.observations.NodeLinkTable` component represents the status of nodes and links as a ``gym.spaces.Box`` with an example format shown below:
  An example observation space is provided below:
  .. list-table:: Observation Space example
    :widths: 25 25 25 25 25 25 25
    :header-rows: 1
    * -
      - ID
      - Hardware State
      - Software State
      - File System State
      - Service / Protocol A
      - Service / Protocol B
    * - Node A
      - 1
      - 1
      - 1
      - 1
      - 1
      - 1
    * - Node B
      - 2
      - 1
      - 3
      - 1
      - 1
      - 1
    * - Node C
      - 3
      - 2
      - 1
      - 1
      - 3
      - 2
    * - Link 1
      - 5
      - 0
      - 0
      - 0
      - 0
      - 10000
    * - Link 2
      - 6
      - 0
      - 0
      - 0
      - 0
      - 10000
    * - Link 3
      - 7
      - 0
      - 0
      - 0
      - 5000
      - 0
  For the nodes, the following values are represented:
  .. code-block::
    [
      ID
      Hardware State            (1=ON,   2=OFF,  3=RESETTING,  4=SHUTTING_DOWN, 5=BOOTING)
      Operating System State    (0=none, 1=GOOD, 2=PATCHING,   3=COMPROMISED)
      File System State         (0=none, 1=GOOD, 2=CORRUPT,    3=DESTROYED,  4=REPAIRING, 5=RESTORING)
      Service1/Protocol1 state  (0=none, 1=GOOD, 2=FIXING,   3=COMPROMISED)
      Service2/Protocol2 state  (0=none, 1=GOOD, 2=FIXING,   3=COMPROMISED)
    ]
  (Note that each service available in the network is provided as a column, although not all nodes may utilise all services)
  For the links, the following statuses are represented:
  .. code-block::
    [
      ID
      Hardware State            (0=not applicable)
      Operating System State    (0=not applicable)
      File System State         (0=not applicable)
      Service1/Protocol1 state  (Traffic load from this protocol on this link)
      Service2/Protocol2 state  (Traffic load from this protocol on this link)
    ]
  NodeStatus component
  ----------------------
  This is a MultiDiscrete observation space that can be though of as a one-dimensional vector of discrete states.
  The example above would have the following structure:
  .. code-block::
    [
      node1_info
      node2_info
      node3_info
    ]
  Each ``node_info`` contains the following:
  .. code-block::
    [
      hardware_state    (0=none, 1=ON,   2=OFF,      3=RESETTING, 4=SHUTTING_DOWN, 5=BOOTING)
      software_state    (0=none, 1=GOOD, 2=PATCHING, 3=COMPROMISED)
      file_system_state (0=none, 1=GOOD, 2=CORRUPT,  3=DESTROYED, 4=REPAIRING, 5=RESTORING)
      service1_state    (0=none, 1=GOOD, 2=FIXING, 3=COMPROMISED)
      service2_state    (0=none, 1=GOOD, 2=FIXING, 3=COMPROMISED)
    ]
  In a network with three nodes and two services, the full observation space would have 15 elements. It can be written with ``gym`` notation to indicate the number of discrete options for each of the elements of the observation space. For example:
  .. code-block::
    gym.spaces.MultiDiscrete([4,5,6,4,4,4,5,6,4,4,4,5,6,4,4])
  .. note::
    NodeStatus observation component provides information only about nodes. Links are not considered.
  LinkTrafficLevels
  -----------------
  This component is a MultiDiscrete space showing the traffic flow levels on the links in the network, after applying a threshold to convert it from a continuous to a discrete value.
  There are two configurable parameters:
  * ``quantisation_levels`` determines how many discrete bins to use for converting the continuous traffic value to discrete (default is 5).
  * ``combine_service_traffic`` determines whether to separately output traffic use for each network protocol or whether to combine them into an overall value for the link. (default is ``True``)
  For example, with default parameters and a network with three links, the structure of this component would be:
  .. code-block::
    [
      link1_status
      link2_status
      link3_status
    ]
  Each ``link_status`` is a number from 0-4 representing the network load in relation to bandwidth.
  .. code-block::
    0 = No traffic (0%)
    1 = low traffic (1%-33%)
    2 = medium traffic (33%-66%)
    3 = high traffic (66%-99%)
    4 = max traffic/ overwhelmed (100%)
  Using ``gym`` notation, the shape of the obs space is: ``gym.spaces.MultiDiscrete([5,5,5])``.
  Action Spaces
  **************
  The action space available to the blue agent comes in two types:
  1. Node-based
  2. Access Control List
  3. Any (Agent can take both node-based and ACL-based actions)
  The choice of action space used during a training session is determined in the config_[name].yaml file.
  **Node-Based**
  The agent is able to influence the status of nodes by switching them off, resetting, or FIXING operating systems and services. In this instance, the action space is a Gymnasium spaces.Discrete type, as follows:
  * Dictionary item {... ,1: [x1, x2, x3,x4] ...}
    The placeholders inside the list under the key '1' mean the following:
      * [0, num nodes] - Node ID (0 = nothing, node ID)
      * [0, 4] - What property it's acting on (0 = nothing, 1 = state, 2 = SoftwareState, 3 = service state, 4 = file system state)
      * [0, 3] - Action on property (0 = nothing, 1 = on / scan, 2 = off / repair, 3 = reset / patch / restore)
      * [0, num services] - Resolves to service ID (0 = nothing, resolves to service)
  **Access Control List**
  The blue agent is able to influence the configuration of the Access Control List rule set (which implements a system-wide firewall). In this instance, the action space is an Gymnasium spaces.Discrete type, as follows:
    * Dictionary item {... ,1: [x1, x2, x3, x4, x5, x6] ...}
    The placeholders inside the list under the key '1' mean the following:
      * [0, 2] - Action (0 = do nothing, 1 = create rule, 2 = delete rule)
      * [0, 1] - Permission (0 = DENY, 1 = ALLOW)
      * [0, num nodes] - Source IP (0 = any, then 1 -> x resolving to IP addresses)
      * [0, num nodes] - Dest IP (0 = any, then 1 -> x resolving to IP addresses)
      * [0, num services] - Protocol (0 = any, then 1 -> x resolving to protocol)
      * [0, num ports] - Port (0 = any, then 1 -> x resolving to port)
  **ANY**
  The agent is able to carry out both **Node-Based** and **Access Control List** operations.
  This means the dictionary will contain key-value pairs in the format of BOTH Node-Based and Access Control List as seen above.
  Rewards
  *******
  A reward value is presented back to the blue agent on the conclusion of every step. The reward value is calculated via two methods which combine to give the total value:
  1. Node and service status
  2. IER status
  **Node and service status**
  On every step, the status of each node is compared against both a reference environment (simulating the situation if the red and blue agents had not impacted the environment)
  and the before and after state of the environment. If the comparison against the reference environment shows no difference, then the score provided is "AllOK". If there is a
  difference with respect to the reference environment, the before and after states are compared, and a score determined. See :ref:`config` for details of reward values.
  **IER status**
  On every step, the full IER set is examined to determine whether green and red agent IERs are being permitted to run. Any red agent IERs running incur a penalty; any green agent
  IERs not permitted to run also incur a penalty. See :ref:`config` for details of reward values.
  Future Enhancements
  *******************
  The PrimAITE project has an ambition to include the following enhancements in future releases:
  * Integration with a suitable standardised framework to allow multi-agent integration
  * Integration with external threat emulation tools, either using off-line data, or integrating at runtime
