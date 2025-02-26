.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _custom_environment:

Creating Custom Environments for PrimAITE
*****************************************

PrimAITE generates it's training configuration/Environments through ingestion of YAML files. A detailed walkthrough of how to create your own environment can be found within the ``Creating-Custom-Environments`` jupyter notebook.

You configuration file should follow the hierarchy seen below:

.. code:: yaml

    io_settings:
    ...
    game:
    ...
    agents:
    ...
    simulation:
    ...


For detailed information about each configuration item found within the configuration file, see :ref:`Configurable Items`.
