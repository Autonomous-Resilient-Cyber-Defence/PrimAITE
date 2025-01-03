.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

Welcome to PrimAITE's documentation
====================================

What is PrimAITE?
-----------------

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
   source/game_layer
   source/simulation
   source/config
   source/rewards
   source/customising_scenarios
   source/varying_config_files
   source/environment
   source/action_masking
   source/node_sets

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


Overview
^^^^^^^^

The ARCD Primary-level AI Training Environment (**PrimAITE**) provides an effective simulation capability for training and evaluating AI in a cyber-defensive role. It incorporates the functionality required of a primary-level  ARCD environment:

- The ability to model a relevant system context;
- Modelling an adversarial agent that the defensive agent can be trained and evaluated against;
- The ability to model key characteristics of a system by representing hosts, servers, network devices, IP addresses, ports, operating systems, folders / files, applications, services and links;
- Modelling background (green) pattern-of-life;
- Operates at machine-speed to enable fast training cycles via Reinforcement Learning (RL).

PrimAITE has been designed as an extensible environment and toolkit to support the development, test, training and evaluation of AI-based cyber defensive agents. Whilst PrimAITE ships with a number of example modelled scenarios (a.k.a. Use Cases), it has not been developed to mandate the solving of a single cyber challenge, and instead provides a highly flexible environment application that can be extended and reconfigured by the user to suit their specific cyber defence training and evaluation needs. PrimAITE provides default networks, red agent and green agent behaviour, reward functions, and action / observation space configuration, all of which can be utilised out of the box, but which ultimately can (and in some instances should) be built upon and / or reconfigured to meet the needs of different defensive agent developers. The PrimAITE user guide provides comprehensive instruction on all PrimAITE features, functionality and components, and can be consulted in order to help guide users in any reconfiguration or enhancements they wish to undertake; a library of example Jupyter notebooks are also provided to support such work.

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
- Agent action logs provide a description of every action taken by each agent during the episode. This includes timestep, action, parameters, request and response, for all Blue agent activity, which is aligned with the Track 2 Common Action / Observation Space (CAOS) format. Action logs also detail all scripted / stochastic red / green agent actions;
- Environment ground truth is provided at every timestep, providing a full description of the environment’s true state;
- Alignment with CAOS provides the ability to transfer agents between CAOS compliant environments.
