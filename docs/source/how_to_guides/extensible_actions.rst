.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _about:

Extensible Actions
******************

Actions defined within PrimAITE have been updated to allow for easier creation of new bespoke actions, without the need to make changes to the ActionManager class within the core PrimAITE repository.


Developing Actions for PrimAITE
===============================

When developing new actions for PrimAITE, it's important to ensure new actions inherit from the AbstractAction class. This is so that the `ActionManager` has visibility
of the new action through the `AbstractAction` registry attribute. This also removes the need for actions to contain an `__init__` method.

New actions to be used within PrimAITE require:

#. **ConfigSchema**:

   This should be a nested class that defines the required configuration items for the new action.

   .. code-block:: python

    class ExampleAction(AbstractAction, identifier="Example_action"):
        """An example action for demonstration purposes."""

        config: "ExampleAction.ConfigSchema"

        class ConfigSchema(AbstractAction.ConfigSchema):
            """The configuration schema with all attributes expected goes here."""
            target_application: str

   The ConfigSchema is used when the class is called to form the action, within the `form_request` method, detailed below.


#. **Unique Identifier**:

   New actions should have a Unique identifier when declared. This is used by the `ActionManager` when forming/processing action commands from agents. See the example code block in ConfigSchema for how this should be implemented.

#. **form_request method**:

   New actions need a `form_request()` method, to convert the action into a ``Requestformat`` that can be ingested by PrimAITE's `RequestManager`.
   The below is an example of how this is done, taken from the `NodeFolderCreateAction`.

   .. code-block:: python

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        if config.node_name is None or config.folder_name is None:
            return ["do_nothing"]
        return [
            "network",
            "node",
            config.node_name,
            "file_system",
            config.verb,
            "folder",
            config.folder_name,
        ]

There is no longer a need for a `from_config()` method to be defined within new actions, as this is handled within the base `AbstractAction` class.

Changes to YAML file.
=====================

Action identifiers now follow the snake_case naming style, instead of the MACRO_CASE that has been seen previously. Please review any custom YAML files for any issues seen. This should be backwards compatible.
