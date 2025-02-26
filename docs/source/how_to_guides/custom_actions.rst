.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _custom_actions:

Creating Custom Actions in PrimAITE
***********************************

PrimAITE contains a selection of available actions that can be exercised within a training session, listed within ``actions.py``. `Note`: Agents are only able to perform the actions listed within it's action_map, defined within it's configuration YAML. See :ref:`custom_environment` for more information.

Developing Custom Actions
============================

Actions within PrimAITE follow a default format, as seen below and in ``actions.py``. It's important that they have an identifier when declared, as this is used when creating the training environment.

.. code:: Python

    class ExampleActionClass(AbstractAction, identifier="ExampleActions"):
        """Example Action Class"""

        config: ExampleAction.ConfigSchema(AbstractAction.ConfigSchema)

        class ConfigSchema(AbstractAction.ConfigSchema)

            node_name: str
        
        @classmethod
        def form_request(cls, config: ConfigSchema) -> RequestFormat:
            return [config.node_name, "example_action"]

Integration with PrimAITE ActionManager
=======================================

Any custom actions should then be added to the `ActionManager` class, and the `act_class_identifiers` dictionary. This will map the action class to the corresponding action type string that would be passed through the PrimAITE `request_system`.


Interaction with the PrimAITE Request Manager
==============================================

Where an action would cause a request to be sent through the PrimAITE RequestManager, a `form_request` method is expected to be defined within the Action Class. This should format  the action into a format that can be ingested by the `RequestManager`. Examples of this include the `NodeFolderCreateAction`, which sends a formed request to create a folder on a given node (seen below).

.. code:: Python

    def form_request(self, node_id: int, folder_name: str) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        node_name = self.manager.get_node_name_by_idx(node_id)
        if node_name is None or folder_name is None:
            return ["do_nothing"]
        return ["network", "node", node_name, "file_system", "create", "folder", folder_name]

Action Masking
==============

Agents which use the `ProxyAgent` class within PrimAITE are able to use Action Masking. This allows the agent to know if the actions are valid/invalid based on the current environment.
Information on how to ensure this can be applied to your custom action can be found in :ref:`action_masking`
