.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Glossary
=============

.. glossary::
    :sorted:

    Network
        The network in primaite is a logical representation of a computer network containing :term:`Nodes<Node>` and :term:`Links<Link>`.

    Node
        A Node represents a network endpoint. For example a computer, server, switch, or an actuator.

    Link
        A Link represents the connection between two Nodes. For example, a physical wire between a computer and a switch or a wireless connection.

    Protocol
        Protocols are used by links to separate different types of network traffic. Common examples would be HTTP, TCP, and UDP.

    Service
        A service represents a piece of software that is installed on a node, such as a web server or a database.

    Access Control List
        PrimAITE blocks or allows certain traffic on the network by simulating firewall rules, which are defined in the Access Control List.

    Agent
        An agent is a representation of a user of the network. Typically this would be a user that is using one of the computer nodes, though it could be an autonomous agent.

    Green agent
        Simulates typical benign activity on the network, such as real users using computers and servers.

    Red Agent
        An agent that is aiming to attack the network in some way, for example by executing a Denial-Of-Service attack or stealing data.

    Blue Agent
        A defensive agent that protects the network from Red Agent attacks to minimise disruption to green agents and protect data.

    Information Exchange Requirement (IER)
        Simulates network traffic by sending data from one network node to another via links for a specified amount of time. IERs can be part of green agent behaviour or red agent behaviour. PrimAITE can be configured to apply a penalty for green agents' IERs being blocked and a reward for red agents' IERs being blocked.

    Pattern-of-Life (PoL)
        PoLs allow agents to change the current hardware, OS, file system, or service statuses of nodes during the course of an episode. For example, a green agent may restart a server node to represent scheduled maintainance. A red agent's Pattern-of-Life can be used to attack nodes by changing their states to CORRUPTED or COMPROMISED.

    Reward
        The reward is a single number used by the blue agent to understand whether it's performing well or poorly. RL agents change their behaviour in an attempt to increase the expected reward each episode. The reward is generated based on the current states of the environment / :term:`reference environment` and is impacted positively by things like green IERS running successfully and negatively by things like nodes being compromised.

    Observation
        An observation is a representation of the current state of the environment that is given to the learning agent so it can decide on which action to perform. If the environment is 'fully observable', the observation contains information about every possible aspect of the environment. More commonly, the environment is 'partially observable' which means the learning agent has to make decisions without knowing every detail of the current environment state.

    Action
        The learning agent decides on an action to take on every step in the simulation. The action has the chance to positively or negatively impact the environment state. Over time, the agent aims to learn which actions to take when to maximise the expected reward.

    Training
        During training, an RL agent is placed in the simulated network and it learns which actions to take in which scenarios to obtain maximum reward.

    Evaluation
        During evaluation, an RL agent acts on the simulated network but it is not allowed to update it's behaviour. Evaluation is used to assess how successful agents are at defending the network.

    Step
        The agents can only act in the environment at discrete intervals. The time step is the basic unit of time in the simulation. At each step, the RL agent has an opportunity to observe the state of the environment and decide an action. Steps are also used for updating states for time-dependent activities such as rebooting a node.

    Episode
        When an episode starts, the network simulation is reset to an initial state. The agents take actions on each step of the episode until it reaches a terminal state, which usually happens after a predetermined number of steps. After the terminal state is reached, a new episode starts and the RL agent has another opportunity to protect the network.

    Reference environment
        While the network simulation is unfolding, a parallel simulation takes place which is identical to the main one except that blue and red agent actions are not applied. This reference environment essentially shows what would be happening to the network if there had been no cyberattack or defense. The reference environment is used to calculate rewards.

    Transaction
        PrimAITE records the decisions of the learning agent by saving its observation, action, and reward at every time step. During each session, this data is saved to disk to allow for full inspection.

    Laydown
        The laydown is a file which defines the training scenario. It contains the network topology, firewall rules, services, protocols, and details about green and red agent behaviours.

    Gymnasium
        PrimAITE uses the Gymnasium reinforcement learning framework API to create a training environment and interface with RL agents. Gymnasium defines a common way of creating observations, actions, and rewards.

    User app home
        PrimAITE supports upgrading software version while retaining user data. The user data directory is where configs, notebooks, and results are stored, this location is `~/primaite<version>` on linux/darwin and `C:\Users\<username>\primaite\<version>` on Windows.
