.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

RL Environments
***************

RL environments are the objects that directly interface with RL libraries such as Stable-Baselines3 and Ray RLLib. The PrimAITE simulation is exposed via three different environment APIs:

* Gymnasium API - this is the standard interface that works with many RL libraries like SB3, Ray, Tianshou, etc.  ``PrimaiteGymEnv`` adheres to the `Official Gymnasium documentation <https://gymnasium.farama.org/api/env/>`_.
* Ray Single agent API - For training a single Ray RLLib agent
* Ray MARL API - For training multi-agent systems with Ray RLLib. ``PrimaiteRayMARLEnv`` adheres to the `Official Ray documentation <https://docs.ray.io/en/latest/rllib/package_ref/env/multi_agent_env.html>`_.

There are Jupyter notebooks which demonstrate integration with each of these three environments. They are located in ``~/primaite/<VERSION>/notebooks/example_notebooks``.
