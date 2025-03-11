.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _extensible_agents:

Extensible Agents
*****************

Agents defined within PrimAITE have been updated to allow for easier creation of new bespoke agents for use in custom environments.


Developing Agents for PrimAITE
==============================

All agent types within PrimAITE must be subclassed from ``AbstractAgent`` in order to be used from configuration YAML files. This then allows you to implement any custom agent logic for the new agent in your training scenario. Examples of implementing custom agent logic can be seen in pre-existing agents, such as the ``DataManipulationBot`` and ``RandomAgent``.

The core features that should be implemented in any new agent are detailed below:

**ConfigSchema**:

Configurable items within a new agent within PrimAITE should contain a ``ConfigSchema`` which holds all configurable variables of the agent. This should not include parameters related to its *state*, these would be listed seperately.
Agent generation will fail pydantic checks if incorrect or invalid parameters are passed to the ConfigSchema of the chosen Agent.


.. code-block:: python

    class ExampleAgent(AbstractAgent, discriminator = "ExampleAgent"):
        """An example agent for demonstration purposes."""

        config: "ExampleAgent.ConfigSchema" = Field(default_factory= lambda: ExampleAgent.ConfigSchema())
        """Agent configuration"""
        num_executions: int = 0
        """Number of action executions by agent"""

        class ConfigSchema(AbstractAgent.ConfigSchema):
            """ExampleAgent configuration schema"""

            type: str = "ExampleAgent
            """Name of agent"""
            starting_host: int
            """Host node that this agent should start from in the given environment."""


.. code-block:: yaml

    - ref: example_green_agent
        team: GREEN
        type: example-agent

        action_space:
        action_map:
            0:
                action: do-nothing
                options: {}
        agent_settings:
        start_step: 25
        frequency: 20
        variance: 5
        starting_host: "Server_1"


**discriminators**:

    All agent classes should have an ``discriminator`` attribute, a unique kebab-case string, for when they are added to the base ``AbstractAgent`` registry. This is then specified in your configuration YAML, and used by PrimAITE to generate the correct Agent.

Changes to YAML file
====================

PrimAITE v4.0.0 introduces some breaking changes to how environment configuration yaml files are created. YAML files created for Primaite versions 3.3.0 should be compatible through a translation function, though it is encouraged that these are updated to reflect the updated format of 4.0.0+.

Agents now follow a more standardised settings definition, so should be more consistent across YAML files and the available agent types with PrimAITE.

All configurable items for agents sit under the ``agent_settings`` heading within your YAML files. There is no need for the inclusion of  a ``start_settings``. Please see the above YAML example for full changes to agents.
