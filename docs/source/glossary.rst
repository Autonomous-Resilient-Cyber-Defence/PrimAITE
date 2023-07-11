Glossary
=============

.. glossary::

    Network
        The network in primaite is a logical representation of a computer network containing :term:`Node<Nodes>` and :term:`Link<Links>`.

    Node
        A Node represents a network endpoint. For example a computer, server, switch, or an actuator.

    Link
        A Link represents the connection between two Nodes. For example, a physical wire between a computer and a switch or a wireless connection.

    Agent
        An agent is a representation of a user of the network. Typically this would be a user that is using one of the computer nodes, though it could be an autonomous agent.

    Red Agent
        An agent that is aiming to attack the network in some way, for example by executing a Denial-Of-Service attack or stealing data.

    Blue Agent
        A defensive agent that protects the network from Red Agent attacks to minimise disruption to green agents and protect data.

    Green agent
        Simulates typical benign activity on the network, such as real users using computers and servers.

    Information Exchange Request (IER)
        ...

    Pattern-of-Life (PoL)
        ...

    Protocol
        ...

    Service
        ...

    Gym
        ...

    Reward
        ...

    Access Control List
        ...

    Observation
        ...

    Action
        ...

    StableBaselines3
        ...

    Ray RLLib
        ...

    Episode
        ...

    Step
        ...

    Reference environment
        ...

    Transaction
        ...

    Laydown
        ...

    User data directory
        PrimAITE supports upgrading software version while retaining user data. The user data directory is where configs, notebooks, and results are stored, this location is `~/primaite` on linux/darwin and `C:\Users\<username>\primaite` on Windows.
