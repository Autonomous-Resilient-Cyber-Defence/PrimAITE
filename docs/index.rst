.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Welcome to PrimAITE's documentation
====================================

What is PrimAITE?
-----------------

Overview
^^^^^^^^

The ARCD Primary-level AI Training Environment (**PrimAITE**) provides an effective simulation capability for the purposes of training and evaluating AI in a cyber-defensive role. It incorporates the functionality required of a primary-level ARCD environment, which includes:

- The ability to model a relevant platform / system context;
- Modelling an adversarial agent that the defensive agent can be trained and evaluated against;
- The ability to model key characteristics of a platform / system by representing connections, IP addresses, ports, operating systems, services and traffic loading on links;
- Modelling background pattern-of-life;
- Operates at machine-speed to enable fast training cycles.

Features
^^^^^^^^

PrimAITE incorporates the following features:

- Highly configurable (via YAML files) to provide the means to model a variety of platform / system laydowns and adversarial attack scenarios;
- A Reinforcement Learning (RL) reward function based on (a) the ability to counter the modelled adversarial cyber-attack, and (b) the ability to ensure success;
- Provision of logging to support AI performance / effectiveness assessment;
- Uses the concept of Information Exchange Requirements (IERs) to model background pattern of life and adversarial behaviour;
- An Access Control List (ACL) function, mimicking the behaviour of a network firewall, is applied across the model, following standard ACL rule format (e.g. DENY/ALLOW, source IP address, destination IP address, protocol and port);
- Application of traffic to the links of the platform / system laydown adheres to the ACL ruleset;
- Presents both a Gymnasium and Ray RLLib interface to the environment, allowing integration with any compliant defensive agents;
- Allows for the saving and loading of trained defensive agents;
- Stochastic adversarial agent behaviour;
- Full capture of discrete logs relating to agent training or evaluation (system state, agent actions taken, instantaneous and average reward for every step of every episode);
- Distinct control over running a training and / or evaluation session;
- NetworkX provides laydown visualisation capability.

Architecture
^^^^^^^^^^^^

PrimAITE is a Python application and is therefore Operating System agnostic. The Gymnasium and Ray RLLib frameworks are employed to provide an interface and source for AI agents. Configuration of PrimAITE is achieved via included YAML files which support full control over the platform / system laydown being modelled, background pattern of life, adversarial (red agent) behaviour, and step and episode count. NetworkX based nodes and links host Python classes to present attributes and methods, and hence a more representative platform / system can be modelled within the simulation.



Training & Evaluation Capability
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PrimAITE provides a training and evaluation capability to AI agents in the context of cyber-attack, via its Gymnasium and RLLib compliant interface. Scenarios can be constructed to reflect platform / system laydowns consisting of any configuration of nodes (e.g. PCs, servers, switches etc.) and network links between them. All nodes can be configured to model services (and their status) and the traffic loading between them over the network links. Traffic loading is broken down into a per service granularity, relating directly to a protocol (e.g. Service A would be configured as a TCP service, and TCP traffic then flows between instances of Service A under the direction of a tailored IER). Highlights of PrimAITE’s training and evaluation capability are:

- The scenario is not bound to a representation of any platform, system, or technology;
- Fully configurable (network / system laydown, IERs, node pattern-of-life, ACL, number of episodes, steps per episode) and repeatable to suit the requirements of AI agents;
- Can integrate with any Gymnasium or RLLib compliant AI agent.

Use of PrimAITE default scenarios within ARCD is supported by a “Use Case Profile” tailored to the scenario.

AI Assessment Capability
^^^^^^^^^^^^^^^^^^^^^^^^

PrimAITE includes the capability to support in-depth assessment of cyber defence AI by outputting logs of the environment state and AI behaviour throughout both training and evaluation sessions. These logs include the following data:

- Timestamp;
- Episode and step number;
- Agent identifier;
- Observation space;
- Action taken (by defensive AI);
- Reward value.

Logs are available in CSV format and provide coverage of the above data for every step of every episode.




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

.. toctree::
   :maxdepth: 8
   :caption: About PrimAITE:
   :hidden:

   source/about
   source/dependencies
   source/glossary

.. toctree::
   :caption: Usage:
   :hidden:

   source/getting_started
   source/primaite_session
   source/example_notebooks
   source/simulation
   source/game_layer
   source/config
   source/environment
   source/customising_scenarios

.. toctree::
   :caption: Developer information:
   :hidden:

   source/state_system
   source/request_system
   PrimAITE API <source/_autosummary/primaite>
   PrimAITE Tests <source/_autosummary/tests>


.. toctree::
   :caption: Project Links:
   :hidden:

   Code <https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE>
   Issues <https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/issues>
   Pull Requests <https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/pulls>
   Discussions <https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/discussions>
