# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Fixed a bug where ACL rules were not resetting on episode reset.
- Fixed a bug where blue agent's ACL actions were being applied against the wrong IP addresses
- Fixed a bug where deleted files and folders did not reset correctly on episode reset.
- Fixed a bug where service health status was using the actual health state instead of the visible health state
- Fixed a bug where the database file health status was using the incorrect value for negative rewards
- Fixed a bug preventing file actions from reaching their intended file
- Made database patch correctly take 2 timesteps instead of being immediate
- Made database patch only possible when the software is compromised or good, it's no longer possible when the software is OFF or RESETTING
- Temporarily disable the blue agent file delete action due to crashes. This issue is resolved in another branch that will be merged into dev soon.
- Fix a bug where ACLs were not showing up correctly in the observation space.
- Added a notebook which explains Data manipulation scenario, demonstrates the attack, and shows off blue agent's action space, observation space, and reward function.
- Made packet capture and system logging optional (off by default). To turn on, change the io_settings.save_pcap_logs and io_settings.save_sys_logs settings in the config.
- Made observation space flattening optional (on by default). To turn off for an agent, change the agent_settings.flatten_obs setting in the config.
- Fixed an issue where the data manipulation attack was triggered at episode start.
- Fixed a bug where FTP STOR stored an additional copy on the client machine's filesystem
- Fixed a bug where the red agent acted to early
- Fixed the order of service health state
- Fixed an issue where starting a node didn't start the services on it



### Added
- Network Hardware - Added base hardware module with NIC, SwitchPort, Node, and Link. Nodes have
fundamental services like ARP, ICMP, and PCAP running them by default.
- Network Transmission - Modelled OSI Model layers 1 through to 5 with various classes for creating network frames and
transmitting them from a Service/Application, down through the layers, over the wire, and back up through the layers to
a Service/Application another machine.
- Introduced `Router` and `Switch` classes to manage networking routes more effectively.
  - Added `ACLRule` and `RouteTableEntry` classes as part of the `Router`.
- New `.show()` methods in all network component classes to inspect the state in either plain text or markdown formats.
- Added `Computer` and `Server` class to better differentiate types of network nodes.
- Integrated a new Use Case 2 network into the system.
- New unit tests to verify routing between different subnets using `.ping()`.
- system - Added the core structure of Application, Services, and Components. Also added a SoftwareManager and
SessionManager.
- Permission System - each action can define criteria that will be used to permit or deny agent actions.
- File System - ability to emulate a node's file system during a simulation
- Example notebooks - There is currently 1 jupyter notebook which walks through using PrimAITE
  1. Creating a simulation - this notebook explains how to build up a simulation using the Python package. (WIP)
- Database:
  - `DatabaseClient` and `DatabaseService` created to allow emulation of database actions
  - Ability for `DatabaseService` to backup its data to another server via FTP and restore data from backup
- Red Agent Services:
  - Data Manipulator Bot - A red agent service which sends a payload to a target machine. (By default this payload is a SQL query that breaks a database). The attack runs in stages with a random, configurable probability of succeeding.
  - `DataManipulationAgent` runs the Data Manipulator Bot according to a configured start step, frequency and variance.
- DNS Services: `DNSClient` and `DNSServer`
- FTP Services: `FTPClient` and `FTPServer`
- HTTP Services: `WebBrowser` to simulate a web client and `WebServer`
- Fixed an issue where the services were still able to run even though the node the service is installed on is turned off

### Removed
- Removed legacy simulation modules: `acl`, `common`, `environment`, `links`, `nodes`, `pol`
- Removed legacy training modules
- Removed tests for legacy code


## [2.0.0] - 2023-07-26

### Added
- Command Line Interface (CLI) for easy access and streamlined usage of PrimAITE.
- Application Directories to enable PrimAITE as a Python package with predefined directories for storage.
- Support for Ray Rllib, allowing training of PPO and A2C agents using Stable Baselines3 and Ray RLlib.
- Random Red Agent to train the blue agent against, with options for randomised Red Agent `POL` and `IER`.
- Repeatability of sessions through seed settings, and deterministic or stochastic evaluation options.
- Session loading to revisit previously run sessions for SB3 Agents.
- Agent Session Classes (`AgentSessionABC` and `HardCodedAgentSessionABC`) to standardise agent training with a common interface.
- Standardised Session Output in a structured format in the user's app sessions directory, providing four types of outputs:
  1. Session Metadata
  2. Results
  3. Diagrams
  4. Saved agents (training checkpoints and a final trained agent).
- Configurable Observation Space managed by the `ObservationHandler` class for a more flexible observation space setup.
- Benchmarking of PrimAITE performance, showcasing session and step durations for reference.
- Documentation overhaul, including automatic API and test documentation with recursive Sphinx auto-summary, using the Furo theme for responsive light/dark theme, and enhanced navigation with `sphinx-code-tabs` and `sphinx-copybutton`.

### Changed
- Action Space updated to discrete spaces, introducing a new `ANY` action space option for combined `NODE` and `ACL` actions.
- Improved `Node` attribute naming convention for consistency, now adhering to `Pascal Case`.
- Package Structure has been refactored for better build, distribution, and installation, with all source code now in the `src/` directory, and the `PRIMAITE` Python package renamed to `primaite` to adhere to PEP-8 Package & Module Names.
- Docs and Tests now sit outside the `src/` directory.
- Non-python files (example config files, Jupyter notebooks, etc.) now sit inside a `*/_package_data/` directory in their respective sub-packages.
- All dependencies are now defined in the `pyproject.toml` file.
- Introduced individual configuration for the number of episodes and time steps for training and evaluation sessions, with separate config values for each.
- Decoupled the lay down config file from the training config, allowing more flexibility in configuration management.
- Updated `Transactions` to only report pre-action observation, improving the CSV header and providing more human-readable descriptions for columns relating to observations.
- Changes to `AccessControlList`, where the `acl` dictionary is now a list to accommodate changes to ACL action space and positioning of `ACLRules` inside the list to signal their level of priority.


### Fixed
- Various bug fixes, including Green IERs separation, correct clearing of links in the reference environment, and proper reward calculation.
- Logic to check if a node is OFF before executing actions on the node by the blue agent, preventing erroneous state changes.
- Improved functionality of Resetting a Node, adding "SHUTTING DOWN" and "BOOTING" operating states for more reliable reset commands.
- Corrected the order of actions in the `Primaite` env to ensure the blue agent uses the current state for decision-making.

## [1.1.1] - 2023-06-27

### Bug Fixes
* Fixed bug whereby 'reference' environment links reach bandwidth capacity and are never cleared due to green & red IERs being applied to them. This bug had a knock-on effect that meant IERs were being blocked based on the full capacity of links on the reference environment which was not correct; they should only be based on the link capacity of the 'live' environment. This fix has been addressed by:
  * Implementing a reference copy of all green IERs (`self.green_iers_reference`).
  * Clearing the traffic on reference IERs at the same time as the live IERs.
  * Passing the `green_iers_reference` to the `apply_iers` function at the reference stage.
  * Passing the `green_iers_reference` as an additional argument to `calculate_reward_function`.
  * Updating the green IERs section of the `calculate_reward_function` to now take into account both the green reference IERs and live IERs. The `green_ier_blocked` reward is only applied if the IER is blocked in the live environment but is running in the reference environment.
  * Re-ordering the actions taken as part of the step function to ensure the blue action happens first before other changes.
  * Removing the unnecessary "Reapply PoL and IERs" action from the step function.
  * Moving the deep-copy of nodes and links to below the "Implement blue action" stage of the step function.

## [1.1.0] - 2023-03-13

### Added
* The user can now initiate either a TRAINING session or an EVALUATION (test) session with the Stable Baselines 3 (SB3) agents via the config_main.yaml file. During evaluation/testing, the agent policy will be fixed (no longer learning) and subjected to the SB3 `evaluate_policy()` function.
* The user can choose whether a saved agent is loaded into the session (with reference to a URL) via the `config_main.yaml` file. They specify a Boolean true/false indicating whether a saved agent should be loaded, and specify the URL and file name.
* Active and Service nodes now possess a new "File System State" attribute. This attribute is permitted to have the states GOOD, CORRUPT, DESTROYED, REPAIRING, and RESTORING. This new feature affects the following components:
  * Blue agent observation space;
  * Blue agent action space;
  * Reward function;
  * Node pattern-of-life.
* The Red Agent node pattern-of-life has been enhanced so that node PoL is triggered by an 'initiator'. The initiator is either DIRECT (state change is applied to the node without any conditions), IER (state change is applied to the node based on IER entry condition), or SERVICE (state change is applied to the node based on a service state condition on the same node or a different node within the network).
* New default config named "config_5_DATA_MANIPULATION.yaml" and associated Training Use Case Profile.
* NodeStateInstruction has been split into `NodeStateInstructionGreen` and `NodeStateInstructionRed` to reflect the changes within the red agent pattern-of-life capability.
* The reward function has been enhanced so that node attribute states of resetting, patching, repairing, and restarting contribute to the overall reward value.
* The User Guide has been updated to reflect all the above changes.

### Changed
* "config_1_DDOS_BASIC.yaml" modified to make it more simplistic to aid evaluation testing.
* "config_2_DDOS_BASIC.yaml" updated to reflect the addition of the File System State and the Red Agent node pattern-of-life enhancement.
* "config_3_DOS_VERY_BASIC.yaml" updated to reflect the addition of the File System State and the Red Agent node pattern-of-life enhancement.
* "config_UNIT_TEST.yaml" is a copy of the new "config_5_DATA_MANIPULATION.yaml" file.
* Updates to Transactions.

### Fixed
* Fixed "config_2_DDOS_BASIC.yaml" by adding another ACL rule to allow traffic to flow from Node 9 to Node 3. Previously, there was no rule, so one of the green IERs could not flow by default.



[unreleased]: https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/releases/tag/v2.0.0
