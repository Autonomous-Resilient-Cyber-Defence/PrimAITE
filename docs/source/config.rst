.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

PrimAITE |VERSION| Configuration
********************************

PrimAITE uses a single configuration file to define everything needed to create the training environment for RL agents, including the network, the scripted agents, and the RL agent's action space, observation space, and reward function.

Example Configuration Hierarchy
###############################
The top level configuration items in a configuration file is as follows

.. code-block:: yaml

    io_settings:
    ...
    game:
    ...
    agents:
    ...
    simulation:
    ...

These are expanded upon in the Configurable items section below

Configurable items
##################

.. toctree::
   :maxdepth: 1

   configuration/io_settings.rst
   configuration/game.rst
   configuration/agents.rst
   configuration/simulation.rst
