# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Made environment reset completely recreate the game object.
- Changed the red agent in the data manipulation scenario to randomly choose client 1 or client 2 to start its attack.
- Changed the data manipulation scenario to include a second green agent on client 1.
- Refactored actions and observations to be configurable via object name, instead of UUID.
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
- Added support for SQL INSERT command.
- Added ability to log each agent's action choices each step to a JSON file.



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
- NTP Services: `NTPClient` and `NTPServer`
- **RouterNIC Class**: Introduced a new class `RouterNIC`, extending the standard `NIC` functionality. This class is specifically designed for router operations, optimizing the processing and routing of network traffic.
  - **Custom Layer-3 Processing**: The `RouterNIC` class includes custom handling for network frames, bypassing standard Node NIC's Layer 3 broadcast/unicast checks. This allows for more efficient routing behavior in network scenarios where router-specific frame processing is required.
  - **Enhanced Frame Reception**: The `receive_frame` method in `RouterNIC` is tailored to handle frames based on Layer 2 (Ethernet) checks, focusing on MAC address-based routing and broadcast frame acceptance.
- **Subnet-Wide Broadcasting for Services and Applications**: Implemented the ability for services and applications to conduct broadcasts across an entire IPv4 subnet within the network simulation framework.
- Introduced the `NetworkInterface` abstract class to provide a common interface for all network interfaces. Subclasses are divided into two main categories: `WiredNetworkInterface` and `WirelessNetworkInterface`, each serving as an abstract base class (ABC) for more specific interface types. Under `WiredNetworkInterface`, the subclasses `NIC` and `SwitchPort` were added. For wireless interfaces, `WirelessNIC` and `WirelessAccessPoint` are the subclasses under `WirelessNetworkInterface`.
- Added `Layer3Interface` as an abstract base class for networking functionalities at layer 3, including IP addressing and routing capabilities. This class is inherited by `NIC`, `WirelessNIC`, and `WirelessAccessPoint` to provide them with layer 3 capabilities, facilitating their role in both wired and wireless networking contexts with IP-based communication.
- Created the `ARP` and `ICMP` service classes to handle Address Resolution Protocol operations and Internet Control Message Protocol messages, respectively, with `RouterARP` and `RouterICMP` for router-specific implementations.
- Created `HostNode` as a subclass of `Node`, extending its functionality with host-specific services and applications. This class is designed to represent end-user devices like computers or servers that can initiate and respond to network communications.
- Introduced a new `IPV4Address` type in the Pydantic model for enhanced validation and auto-conversion of IPv4 addresses from strings using an `ipv4_validator`.
- Comprehensive documentation for the Node and its network interfaces, detailing the operational workflow from frame reception to application-level processing.
- Detailed descriptions of the Session Manager and Software Manager functionalities, including their roles in managing sessions, software services, and applications within the simulation.
- Documentation for the Packet Capture (PCAP) service and SysLog functionality, highlighting their importance in logging network frames and system events, respectively.
- Expanded documentation on network devices such as Routers, Switches, Computers, and Switch Nodes, explaining their specific processing logic and protocol support.
- **Firewall Node**: Introduced the `Firewall` class extending the functionality of the existing `Router` class. The `Firewall` class incorporates advanced features to scrutinize, direct, and filter traffic between various network zones, guided by predefined security rules and policies. Key functionalities include:
    - Access Control Lists (ACLs) for traffic filtering based on IP addresses, protocols, and port numbers.
    - Network zone segmentation for managing traffic across external, internal, and DMZ (De-Militarized Zone) networks.
    - Interface configuration to establish connectivity and define network parameters for external, internal, and DMZ interfaces.
    - Protocol and service management to oversee traffic and enforce security policies.
    - Dynamic traffic processing and filtering to ensure network security and integrity.
- `AirSpace` class to simulate wireless communications, managing wireless interfaces and facilitating the transmission of frames within specified frequencies.
- `AirSpaceFrequency` enum for defining standard wireless frequencies, including 2.4 GHz and 5 GHz bands, to support realistic wireless network simulations.
- `WirelessRouter` class, extending the `Router` class, to incorporate wireless networking capabilities alongside traditional wired connections. This class allows the configuration of wireless access points with specific IP settings and operating frequencies.
- Documentation Updates:
    - Examples include how to set up PrimAITE session via config
    - Examples include how to create nodes and install software via config
    - Examples include how to set up PrimAITE session via Python
    - Examples include how to create nodes and install software via Python
    - Added missing ``DoSBot`` documentation page
    - Added diagrams where needed to make understanding some things easier
    - Templated parts of the documentation to prevent unnecessary repetition and for easier maintaining of documentation
    - Separated documentation pages of some items i.e. client and server software were on the same pages - which may make things confusing
    - Configuration section at the bottom of the software pages specifying the configuration options available (and which ones are optional)
- Ability to add ``Firewall`` node via config
- Ability to add ``Router`` routes via config
- Ability to add ``Router``/``Firewall`` ``ACLRule`` via config
- NMNE capturing capabilities to `NetworkInterface` class for detecting and logging Malicious Network Events.
- New `nmne_config` settings in the simulation configuration to enable NMNE capturing and specify keywords such as "DELETE".

### Changed
- Integrated the RouteTable into the Routers frame processing.
- Frames are now dropped when their TTL reaches 0
- **NIC Functionality Update**: Updated the Network Interface Card (`NIC`) functionality to support Layer 3 (L3) broadcasts.
  - **Layer 3 Broadcast Handling**: Enhanced the existing `NIC` classes to correctly process and handle Layer 3 broadcasts. This update allows devices using standard NICs to effectively participate in network activities that involve L3 broadcasting.
  - **Improved Frame Reception Logic**: The `receive_frame` method of the `NIC` class has been updated to include additional checks and handling for L3 broadcasts, ensuring proper frame processing in a wider range of network scenarios.
- Standardised the way network interfaces are accessed across all `Node` subclasses (`HostNode`, `Router`, `Switch`) by maintaining a comprehensive `network_interface` attribute. This attribute captures all network interfaces by their port number, streamlining the management and interaction with network interfaces across different types of nodes.
- Refactored all tests to utilise new `Node` subclasses (`Computer`, `Server`, `Router`, `Switch`) instead of creating generic `Node` instances and manually adding network interfaces. This change aligns test setups more closely with the intended use cases and hierarchies within the network simulation framework.
- Updated all tests to employ the `Network()` class for managing nodes and their connections, ensuring a consistent and structured approach to setting up network topologies in testing scenarios.
- **ACLRule Wildcard Masking**: Updated the `ACLRule` class to support IP ranges using wildcard masking. This enhancement allows for more flexible and granular control over traffic filtering, enabling the specification of broader or more specific IP address ranges in ACL rules.
- Updated `NetworkInterface` documentation to reflect the new NMNE capturing features and how to use them.
- Integration of NMNE capturing functionality within the `NicObservation` class.
- Changed blue action set to enable applying node scan, reset, start, and shutdown to every host in data manipulation scenario

### Removed
- Removed legacy simulation modules: `acl`, `common`, `environment`, `links`, `nodes`, `pol`
- Removed legacy training modules
- Removed tests for legacy code

### Fixed
- Addressed network transmission issues that previously allowed ARP requests to be incorrectly routed and repeated across different subnets. This fix ensures ARP requests are correctly managed and confined to their appropriate network segments.
- Resolved problems in `Node` and its subclasses where the default gateway configuration was not properly utilized for communications across different subnets. This correction ensures that nodes effectively use their configured default gateways for outbound communications to other network segments, thereby enhancing the network's routing functionality and reliability.
- Network Interface Port name/num being set properly for sys log and PCAP output.

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
