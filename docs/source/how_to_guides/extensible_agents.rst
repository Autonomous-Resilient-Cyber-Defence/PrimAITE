.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _about:

Extensible Agents
*****************

Agents defined within PrimAITE have been updated to allow for easier creation of new bespoke agents.


Developing Agents for PrimAITE
==============================

Agents within PrimAITE, follow the shown inheritance structure, and

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
	|
	| - ProxyAgent
	|
	| - ControlledAgent


#. **ConfigSchema**:

    Configurable items within a new agent within PrimAITE should contain a ``ConfigSchema`` which holds all configurable variables of the agent. This should not include parameters related to its *state*.


    .. code-block:: python

        class ExampleAgent(AbstractAgent, identifier = "example_agent"):
            """An example agent for demonstration purposes."""

            config: "ExampleAgent.ConfigSchema"
            """Agent configuration"""
            num_executions: int
            """Number of action executions by agent"""

            class ConfigSchema(AbstractAgent.ConfigSchema):
                """ExampleAgent configuration schema"""

                agent_name: str
                """Name of agent"""
                action_interval: int
                """Number of steps between agent actions"""

#. **identifier**:

    All agent classes should have a unique ``identifier`` attribute, for when they are added to the base ``AbstractAgent`` registry. PrimAITE notation is for these to be written in snake_case

Changes to YAML file
====================

Agent configurations specified within YAML files used for earlier versions of PrimAITE will need updating to be compatible with PrimAITE v4.0.0+.

# TODO: Show changes to YAML config needed here
