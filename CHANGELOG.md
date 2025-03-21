# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] = 2025-03-XX

### Added
-   Log observation space data by episode and step.
-   Added ability to set the observation threshold for NMNE, file access and application executions.
-   Added `show_history` method to Agents, allowing you to view actions taken by an agent per step. By default, `do-nothing` actions are omitted.
-   New ``node-send-local-command`` action implemented which grants agents the ability to execute commands locally. (Previously limited to remote only)
-   Added ability to set the observation threshold for NMNE, file access and application executions
-   UC7 Scenario model changes including Threat Actor Profile, TAP001 and TAP003 agents plus config files and example notebooks.
-   New how-to guides describing how to use the new extension system to customise actions, environments and rewards.
-   Added version and plugin fields to YAML configs to ensure compatibility with future versions.
-   Network Node Adder class provides a framework for adding nodes to a network in a standardised way.

### Changed
-   ACLs are no longer applied to layer-2 traffic.
-   Random number seed values are recorded in simulation/seed.log if the seed is set in the config file
    or `generate_seed_value` is set to `true`.
-   ARP .show() method will now include the port number associated with each entry.
-   The behaviour that services, applications, files and folders require scanning before their observations are updated is now optional.
-   Updated the `Terminal` class to provide response information when sending remote command execution.
-   Agents now follow a common configuration format, simplifying the configuration of agents and their extensibilty.
-   Actions within PrimAITE are now extensible, allowing for plugin support.
-   Added a config schema to `ObservationManager`, `ActionManager`, and `RewardFunction`.
-   Streamlined the way agents are created from config
-   Agent config no longer requires a dummy action space if the action space is empty, the same applies for observation space and reward function
-   Actions now support a config schema, to allow yaml data validation and default parameter values
-   Action parameters are no longer defined through IDs, instead meaningful data is provided directly in the action map
-   Test and example YAMLs have been updated to match the new agent and action schemas, such as:
    -   Removed empty action spaces, observation spaces, or reward spaces for agent which didn't use them
    -   Relabelled action parameters to match the new action config schemas, and updated the values to no longer rely on indices
    -   Removed action space options which were previously used for assigning meaning to action space IDs
-   Updated tests that don't use YAMLs to still use the new action and agent schemas
-   Nodes now use a config schema and are extensible, allowing for plugin support.
-   Node tests have been updated to use the new node config schemas when not using YAML files.
-   Documentation has been updated to include details of extensibility with PrimAITE.
-   Software is created in the GOOD health state instead of UNUSED.
-   Standardised naming convention for YAML config files using kebab-case.
    This naming convention is used for configuring software, observations, actions and node types.
    NB: A migration guide will be available with this release.

### Fixed
-   DNS client no longer fails to check its cache if a DNS server address is missing.
-   DNS client now correctly inherits the node's DNS address configuration setting.
-   ACL observations now include the ACL at index 0.
-   SoftwareManager.show() correctly displays all the software associated with a port whether the software is listening or not.


## [3.3.0] - 2024-09-04
### Added
-   Random Number Generator Seeding by specifying a random number seed in the config file.
-   Implemented Terminal service class, providing a generic terminal simulation.
-   Added `User`, `UserManager` and `UserSessionManager` to enable the creation of user accounts and login on Nodes.
-   Added actions to establish SSH connections, send commands remotely and terminate SSH connections.
-   Added actions to change users' passwords.
-   Added a `listen_on_ports` set in the `IOSoftware` class to enable software listening on ports in addition to the
    main port they're assigned.
-   Added two new red applications: ``C2Beacon`` and ``C2Server`` which aim to simulate malicious network infrastructure.
    Refer to the ``Command and Control Application Suite E2E Demonstration`` notebook for more information.
-   Added reward calculation details to AgentHistoryItem.
-   Added a new Privilege-Escalation-and Data-Loss-Example.ipynb notebook with a realistic cyber scenario focusing on
    internal privilege escalation and data loss through the manipulation of SSH access and Access Control Lists (ACLs).
-   Added a new extensible `NetworkNodeAdder` class for convenient addition of sets of nodes based on a simplified config.

### Changed
-   File and folder observations can now be configured to always show the true health status, or require scanning like before.
-   It's now possible to disable stickiness on reward components, meaning their value returns to 0 during timesteps where agent don't issue the corresponding action. Affects `GreenAdminDatabaseUnreachablePenalty`, `WebpageUnavailablePenalty`, `WebServer404Penalty`
-   Node observations can now be configured to show the number of active local and remote logins.
-   Ports and IP Protocols no longer use enums. They are defined in dictionary lookups and are handled by custom validation to enable extensibility with plugins.
-   Changed AirSpaceFrequency to a data transfer object with a registry to allow extensibility
-   Changed the Office LAN creation convenience function to follow the new `NetworkNodeAdder` pattern. Office LANs can now also be defined in YAML config.

### Fixed
-   Folder observations showing the true health state without scanning (the old behaviour can be reenabled via config)
-   Updated `SoftwareManager` `install` and `uninstall` to handle all functionality that was being done at the `install`
    and `uninstall` methods in the `Node` class.
-   Updated the `receive_payload_from_session_manager` method in `SoftwareManager` so that it now sends a copy of the
    payload to any software listening on the destination port of the `Frame`.
-   Made the `show` method of `Network` show all node types, including ones registered at runtime

### Removed
-   Removed the `install` and `uninstall` methods in the `Node` class.


## [3.2.0] - 2024-07-18

### Added
-   Action penalty is a reward component that applies a negative reward for doing any action other than DONOTHING
-   Application configuration actions for RansomwareScript, DatabaseClient, and DoSBot applications
-   Ability to configure how long it takes to apply the service fix action
-   Terminal service using SSH
-   Airspaces now track the amount of data being transmitted, viewable using the `show_bandwidth_load` method
-   Tests to verify that airspace bandwidth is applied correctly and can be configured via YAML
-   Agent logging for agents' internal decision logic
-   Action masking in all PrimAITE environments
### Changed
-   Application registry was moved to the `Application` class and now updates automatically when Application is subclassed
-   Databases can no longer respond to request while performing a backup
-   Application install no longer accepts an `ip_address` parameter
-   Application install action can now be used on all applications
-   Actions have additional logic for checking validity
-   Frame `size` attribute now includes both core size and payload size in bytes
-   The `speed` attribute of `NetworkInterface` has been changed from `int` to `float`
-   Tidied up CHANGELOG
-   Enhanced `AirSpace` logic to block transmissions that would exceed the available capacity.
-   Updated `_can_transmit` function in `Link` to account for current load and total bandwidth capacity, ensuring transmissions do not exceed limits.

### Fixed
-   Links and airspaces can no longer transmit data if this would exceed their bandwidth


## [3.1.0] - 2024-06-25

### Added
-   Observations for traffic amounts on host network interfaces
-   NMAP application network discovery, including ping scan and port scan
-   NMAP actions
-   Automated adding copyright notices to source files
-   More file types
-   `show` method to files
-   `model_dump` methods to network enums to enable better logging

### Changed
-   Updated file system actions to stop failures when creating duplicate files
-   Improved parsing of ACL add rule actions to make some parameters optional

### Fixed
-   Fixed database client uninstall failing due to persistent connections
-   Fixed packet storm when pinging broadcast addresses


## [3.0.0] - 2024-06-10

### Added
-   New simulation module
-   Multi agent reinforcement learning support
-   File system class to manage files and folders
-   Software for nodes that can have its own behaviour
-   Software classes to model FTP, Postgres databases, web traffic, NTP
-   Much more detailed network simulation including packets, links, and network interfaces
-   More node types: host, computer, server, router, switch, wireless router, and firewalls
-   Network Hardware - NIC, SwitchPort, Node, and Link. Nodes have fundamental services like ARP, ICMP, and PCAP running them by default.
-   Malicious network event detection
-   New `game` module for managing agents
-   ACL rule wildcard masking
-   Network broadcasting
-   Wireless transmission
-   More detailed documentation
-   Example jupyter notebooks to demonstrate new functionality
-   More reward components
-   Packet capture logs
-   Node system logs
-   Per-step full simulation state log
-   Attack randomisation with respect to timing and attack source
-   Ability to set log level via CLI
-   Ability to vary the YAML configuration per-episode
-   Developer CLI tools for enhanced debugging (with `primaite dev-mode enable`)
-   `show` function to many simulation objects to inspect their current state

### Changed
-   Decoupled the environment from the simulation by adding the `game` interface layer
-   Made agents share a common base class
-   Added more actions
-   Made all agents use CAOS actions, including red and green agents
-   Reworked YAML configuration file schema
-   Reworked the reward system to be component-based
-   Changed agent logs to create a JSON output instead of CSV with more detailed action information
-   Made observation space flattening optional
-   Made all logging optional
-   Agent actions now provide responses with a success code

### Removed
-   Legacy simulation modules
-   Legacy training modules
-   Tests for legacy code
-   Hardcoded IERs and PoL, traffic generation is now handled by agents and software
-   Inbuilt agent training scripts


## [2.0.0] - 2023-07-26

### Added
-   Command Line Interface (CLI) for easy access and streamlined usage of PrimAITE.
-   Application Directories to enable PrimAITE as a Python package with predefined directories for storage.
-   Support for Ray Rllib, allowing training of PPO and A2C agents using Stable Baselines3 and Ray RLlib.
-   Random Red Agent to train the blue agent against, with options for randomised Red Agent `POL` and `IER`.
-   Repeatability of sessions through seed settings, and deterministic or stochastic evaluation options.
-   Session loading to revisit previously run sessions for SB3 Agents.
-   Agent Session Classes (`AgentSessionABC` and `HardCodedAgentSessionABC`) to standardise agent training with a common interface.
-   Standardised Session Output in a structured format in the user's app sessions directory, providing four types of outputs: Session Metadata, Results, Diagrams, Trained agents.
-   Configurable Observation Space managed by the `ObservationHandler` class for a more flexible observation space setup.
-   Benchmarking of PrimAITE performance, showcasing session and step durations for reference.
-   Documentation overhaul, including automatic API and test documentation with recursive Sphinx auto-summary, using the Furo theme for responsive light/dark theme, and enhanced navigation with `sphinx-code-tabs` and `sphinx-copybutton`.

### Changed
-   Action Space updated to discrete spaces, introducing a new `ANY` action space option for combined `NODE` and `ACL` actions.
-   Improved `Node` attribute naming convention for consistency, now adhering to `Pascal Case`.
-   Package Structure has been refactored for better build, distribution, and installation, with all source code now in the `src/` directory, and the `PRIMAITE` Python package renamed to `primaite` to adhere to PEP-8 Package & Module Names.
-   Docs and Tests now sit outside the `src/` directory.
-   Non-python files (example config files, Jupyter notebooks, etc.) now sit inside a `*/_package_data/` directory in their respective sub-packages.
-   All dependencies are now defined in the `pyproject.toml` file.
-   Introduced individual configuration for the number of episodes and time steps for training and evaluation sessions, with separate config values for each.
-   Decoupled the lay down config file from the training config, allowing more flexibility in configuration management.
-   Updated `Transactions` to only report pre-action observation, improving the CSV header and providing more human-readable descriptions for columns relating to observations.
-   Changes to `AccessControlList`, where the `acl` dictionary is now a list to accommodate changes to ACL action space and positioning of `ACLRules` inside the list to signal their level of priority.


### Fixed
-   Various bug fixes, including Green IERs separation, correct clearing of links in the reference environment, and proper reward calculation.
-   Logic to check if a node is OFF before executing actions on the node by the blue agent, preventing erroneous state changes.
-   Improved functionality of Resetting a Node, adding "SHUTTING DOWN" and "BOOTING" operating states for more reliable reset commands.
-   Corrected the order of actions in the `Primaite` env to ensure the blue agent uses the current state for decision-making.


## [1.1.1] - 2023-06-27

### Fixed
-   Fixed bug whereby 'reference' environment links reach bandwidth capacity and are never cleared due to green & red IERs being applied to them. This bug had a knock-on effect that meant IERs were being blocked based on the full capacity of links on the reference environment which was not correct; they should only be based on the link capacity of the 'live' environment. This fix has been addressed by:
    -   Implementing a reference copy of all green IERs (`self.green_iers_reference`).
    -   Clearing the traffic on reference IERs at the same time as the live IERs.
    -   Passing the `green_iers_reference` to the `apply_iers` function at the reference stage.
    -   Passing the `green_iers_reference` as an additional argument to `calculate_reward_function`.
    -   Updating the green IERs section of the `calculate_reward_function` to now take into account both the green reference IERs and live IERs. The `green_ier_blocked` reward is only applied if the IER is blocked in the live environment but is running in the reference environment.
    -   Re-ordering the actions taken as part of the step function to ensure the blue action happens first before other changes.
    -   Removing the unnecessary "Reapply PoL and IERs" action from the step function.
    -   Moving the deep-copy of nodes and links to below the "Implement blue action" stage of the step function.


## [1.1.0] - 2023-03-13

### Added
-   The user can now initiate either a TRAINING session or an EVALUATION (test) session with the Stable Baselines 3 (SB3) agents via the config_main.yaml file. During evaluation/testing, the agent policy will be fixed (no longer learning) and subjected to the SB3 `evaluate_policy()` function.
-   The user can choose whether a saved agent is loaded into the session (with reference to a URL) via the `config_main.yaml` file. They specify a Boolean true/false indicating whether a saved agent should be loaded, and specify the URL and file name.
-   Active and Service nodes now possess a new "File System State" attribute. This attribute is permitted to have the states GOOD, CORRUPT, DESTROYED, REPAIRING, and RESTORING. This new feature affects the following components:
    -   Blue agent observation space;
    -   Blue agent action space;
    -   Reward function;
    -   Node pattern-of-life.
-   The Red Agent node pattern-of-life has been enhanced so that node PoL is triggered by an 'initiator'. The initiator is either DIRECT (state change is applied to the node without any conditions), IER (state change is applied to the node based on IER entry condition), or SERVICE (state change is applied to the node based on a service state condition on the same node or a different node within the network).
-   New default config named "config_5_DATA_MANIPULATION.yaml" and associated Training Use Case Profile.
-   NodeStateInstruction has been split into `NodeStateInstructionGreen` and `NodeStateInstructionRed` to reflect the changes within the red agent pattern-of-life capability.
-   The reward function has been enhanced so that node attribute states of resetting, patching, repairing, and restarting contribute to the overall reward value.
-   The User Guide has been updated to reflect all the above changes.

### Changed
-   "config_1_DDOS_BASIC.yaml" modified to make it more simplistic to aid evaluation testing.
-   "config_2_DDOS_BASIC.yaml" updated to reflect the addition of the File System State and the Red Agent node pattern-of-life enhancement.
-   "config_3_DOS_VERY_BASIC.yaml" updated to reflect the addition of the File System State and the Red Agent node pattern-of-life enhancement.
-   "config_UNIT_TEST.yaml" is a copy of the new "config_5_DATA_MANIPULATION.yaml" file.
-   Updates to Transactions.

### Fixed
-   Fixed "config_2_DDOS_BASIC.yaml" by adding another ACL rule to allow traffic to flow from Node 9 to Node 3. Previously, there was no rule, so one of the green IERs could not flow by default.
