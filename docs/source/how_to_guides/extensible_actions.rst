.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _extensible_actions:

Extensible Actions
******************


Changes to Actions class Structure.
===================================

Actions within PrimAITE have been updated to inherit from a base class, AbstractAction, standardising their format and allowing for easier creation of custom actions. Actions now use a ``ConfigSchema`` to define the possible configuration variables, and use pydantic to enforce correct parameters are passed through.


Developing Custom Actions.
==========================

Custom actions within PrimAITE must be a sub-class of `AbstractAction`, and contain 3 key items:

#. ConfigSchema class

#. Unique discriminator

#. `form_request` method.


ConfigSchema
############

The ConfigSchema sub-class of the action must contain all `configurable` variables within the action, that would be specified within the environments configuration YAML file.


Unique discriminator
#################

When declaring a custom class, it must have a unique discriminator string, that allows PrimAITE to generate the correct action when needed.

.. code:: Python

    class CreateDirectoryAction(AbstractAction, discriminator="node-folder-create")

        config: CreateDirectoryAction.ConfigSchema

        class ConfigSchema(AbstractAction.ConfigSchema):

            verb: ClassVar[str] = "create"
            node_name: str
            directory_name: str

        @classmethod
        def form_request(cls, config: ConfigSchema) -> RequestFormat:
            return ["network",
                    "node",
                    config.node_name,
                    "file_system",
                    config.verb,
                    "folder",
                    config.directory_name,
                ]

The above action would fail pydantic validation as the discriminator "node-folder-create" is already used by the `NodeFolderCreateAction`, and would create a duplicate listing within `AbstractAction._registry`.


form_request method
###################

PrimAITE actions need to have a `form_request` method, which can be passed to the `RequestManager` for processing. This allows the custom action to be actioned within the simulation environment.
