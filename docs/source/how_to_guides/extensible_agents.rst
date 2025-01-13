.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _about:

Extensible Agents
*****************

Agents defined within PrimAITE have been updated to allow for easier creation of new bespoke agents.


Developing Agents for PrimAITE
==============================

Agents within PrimAITE, follow the shown inheritance structure below.

The inheritance structure of agents within PrimAITE are shown below. When developing custom agents for use with PrimAITE, please see the relevant documentation for each agent type to determine which is most relevant for your implementation.

All agent types within PrimAITE are listed under the ``_registry`` attribute of the parent class, ``AbstractAgent``.

# TODO: Turn this into an inheritance diagram

AbstractAgent
	|
	| - AbstractScriptedAgent
	|		|
	|	    | - AbstractTAPAgent
	|		|		|
	|		|		| - DataManipulationAgent
	|		|
	|		|
	|		| - RandomAgent
	|		|
	|		| - PeriodicAgent
	|		|
	|		| - RandomAgent
	|
	| - ProxyAgent
	|
	| - ControlledAgent


#. **ConfigSchema**:

    Configurable items within a new agent within PrimAITE should contain a ``ConfigSchema`` which holds all configurable variables of the agent. This should not include parameters related to its *state*.
	Agent generation will fail if incorrect or invalid parameters are passed to the ConfigSchema, of the chosen Agent.


    .. code-block:: python

        class ExampleAgent(AbstractAgent, identifier = "ExampleAgent"):
            """An example agent for demonstration purposes."""

            config: "ExampleAgent.ConfigSchema"
            """Agent configuration"""
            num_executions: int = 0
            """Number of action executions by agent"""

            class ConfigSchema(AbstractAgent.ConfigSchema):
                """ExampleAgent configuration schema"""

                type: str = "ExampleAgent
                """Name of agent"""
                starting_host: int
                """Host node that this agent should start from in the given environment."""


	.. code-block:: YAML

		- ref: example_green_agent
		  team: GREEN
		  type: ExampleAgent
		  observation_space: null
		  action_space:
		  	action_list:
				- type: do_nothing
			action_map:
				0:
					action: do_nothing
					options: {}
			options:
				nodes:
					- node_name: client_1
				max_folders_per_node: 1
				max_files_per_folder: 1
				max_services_per_node: 1
				max_nics_per_node: 2
				max_acl_rules: 10

		  reward_function:
		  	reward_components:
				- type: DUMMY

		  agent_settings:
			start_step: 25
			frequency: 20
			variance: 5
			starting_host: "Server_1"


#. **Identifiers**:

    All agent classes should have a ``identifier`` attribute, a unique kebab-case string, for when they are added to the base ``AbstractAgent`` registry. This is then specified in your configuration YAML, and used by PrimAITE to generate the correct Agent.

Changes to YAML file
====================

PrimAITE v4.0.0 introduces some breaking changes to how environment configuration yaml files are created. YAML files created for Primaite versions 3.3.0 should be compatible through a translation function, though it is encouraged that these are updated to reflect the updated format of 4.0.0+.

Agents now follow a more standardised settings definition, so should be more consistent across YAML files and the available agent types with PrimAITE.

# TODO: Show changes to YAML config needed here

All configurable items for agents sit under the ``agent_settings`` heading within your YAML files. There is no need for the inclusion of  a ``start_settings``.
