.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _custom_environments:

Creating Custom Environments for PrimAITE
*****************************************

PrimAITE generates it's training configuration/Environments through ingestion of YAML files. A detailed walkthrough of how to create your own environment can be found within the ``Creating-Custom-Environments`` jupyter notebook.

You configuration file should follow the hierarchy seen below:

.. code:: yaml

    metadata:
        version: 4.0

    io_settings:
    ...
    game:
    ...
    agents:
    ...
    simulation:
    ...

It's important to include the metadata tag within your YAML file, as this is used to ensure PrimAITE can interpret the configuration correctly. This should also include any plugins that are required for the defined environment, along with their respective version.

For detailed information about each configuration item found within the configuration file, see :ref:`Configurable Items`.

