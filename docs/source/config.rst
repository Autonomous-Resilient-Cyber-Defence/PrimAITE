.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Primaite v3 config
******************

PrimAITE uses a single configuration file to define everything needed to train and evaluate an RL policy in a custom cybersecurity scenario. This includes the configuration of the network, the scripted or trained agents that interact with the network, as well as settings that define how to perform training in Stable Baselines 3 or Ray RLLib.
The entire config is used by the ``PrimaiteSession`` object for users who wish to let PrimAITE handle the agent definition and training. If you wish to define custom agents and control the training loop yourself, you can use the config with the ``PrimaiteGame``, and ``PrimaiteGymEnv`` objects instead. That way, only the network configuration and agent setup parts of the config are used, and the training section is ignored.

Configurable items
##################

.. toctree::
   :maxdepth: 1

   configuration/training_config.rst
   configuration/io_settings.rst
   configuration/game.rst
   configuration/agents.rst
   configuration/simulation.rst
