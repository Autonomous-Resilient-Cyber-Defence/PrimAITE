.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

Welcome to PrimAITE's documentation
====================================

What is PrimAITE?
-----------------

Overview
^^^^^^^^

The ARCD Primary-level AI Training Environment (**PrimAITE**) provides an effective simulation capability for training and evaluating AI in a cyber-defensive role. It incorporates the functionality required of a primary-level  ARCD environment:

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

PrimAITE is a Python application and will operate on multiple Operating Systems (Windows, Linux and Mac);
a comprehensive installation and user guide is provided with each release to support its usage.

Configuration of PrimAITE is achieved via included YAML files which support full control over the network / system laydown being modelled, background pattern of life, adversarial (red agent) behaviour, and step and episode count.
A Simulation Controller layer manages the overall running of the simulation, keeping track of all low-level objects.

It is agnostic to the number of agents, their action / observation spaces, and the RL library being used.

It presents a public API providing a method for describing the current state of the simulation, a method that accepts action requests and provides responses, and a method that triggers a timestep advancement.
The Game Layer converts the simulation into a playable game for the agent(s).

it translates between simulation state and Gymnasium.Spaces to pass action / observation data between the agent(s) and the simulation. It is responsible for calculating rewards, managing Multi-Agent RL (MARL) action turns, and via a single agent interface can interact with Blue, Red and Green agents.

Agents can either generate their own scripted behaviour or accept input behaviour from an RL agent.

Finally, a Gymnasium / Ray RLlib Environment Layer forwards requests to the Game Layer as the agent sends them. This layer also manages most of the I/O, such as reading in the configuration files and saving agent logs.

.. image:: ../../_static/primAITE_architecture.png
    :width: 500
    :align: center


Training & Evaluation Capability
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PrimAITE provides a training and evaluation capability to AI agents in the context of cyber-attack, via its Gymnasium / Ray RLlib compliant interface.

Scenarios can be constructed to reflect network / system laydowns consisting of any configuration of nodes (e.g., PCs, servers etc.) and the networking equipment and links between them.

All nodes can be configured to contain applications, services, folders and files (and their status).

Traffic flows between services and applications as directed by an ‘execution definition,’ with the traffic flow on the network governed by the network equipment (switches, routers and firewalls) and the ACL rules and routing tables they employ.

Highlights of PrimAITE’s training and evaluation capability are:

- The scenario is not bound to a representation of any platform, system, or technology;
- Fully configurable (network / system laydown, green pattern-of-life, red personas, reward function, ACL rules for each device, number of episodes / steps, action / observation space) and repeatable to suit the requirements of AI agents;
- Can integrate with any Gymnasium / Ray RLlib compliant AI agent .


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
   source/simulation
   source/game_layer
   source/config
   source/environment
   source/customising_scenarios
   source/varying_config_files

.. toctree::
   :caption: Notebooks:
   :hidden:

   source/example_notebooks
   source/notebooks/executed_notebooks

.. toctree::
   :caption: Developer information:
   :hidden:

   source/developer_tools
   source/state_system
   source/request_system
   PrimAITE API <source/_autosummary/primaite>
   PrimAITE Tests <source/_autosummary/tests>
