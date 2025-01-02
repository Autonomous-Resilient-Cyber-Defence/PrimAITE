.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _about:

Extensible Agents
*****************

Agents defined within PrimAITE have been updated to allow for easier creation of new bespoke agents. 


Developing Agents for PrimAITE
==============================

Agents within PrimAITE, follow the shown inheritance structure below. 

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
	Agent generation will fail if incorrect parameters are passed to the ConfigSchema, for the chosen Agent.


    .. code-block:: python

        class ExampleAgent(AbstractAgent, identifier = "example_agent"):
            """An example agent for demonstration purposes."""

            config: "ExampleAgent.ConfigSchema"
            """Agent configuration"""
            num_executions: int = 0
            """Number of action executions by agent"""

            class ConfigSchema(AbstractAgent.ConfigSchema):
                """ExampleAgent configuration schema"""

                agent_name: str
                """Name of agent"""
                action_interval: int
                """Number of steps between agent actions"""


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
		  	start_settings:
				start_step: 25
				frequency: 20
				variance: 5


#. **identifier**:

    All agent classes should have a ``identifier`` attribute, a unique snake_case string, for when they are added to the base ``AbstractAgent`` registry. This is then specified in your configuration YAML, and used by PrimAITE to generate the correct Agent.

Changes to YAML file
====================

Agent configurations specified within YAML files used for earlier versions of PrimAITE will need updating to be compatible with PrimAITE v4.0.0+.

Agents now follow a more standardised settings definition, so should be more consistent across YAML.


# TODO: Show changes to YAML config needed here
