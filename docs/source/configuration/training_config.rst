.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

``training_config``
===================
Configuration items relevant to how the Reinforcement Learning agent(s) will be trained.

``training_config`` hierarchy
-----------------------------

.. code-block:: yaml

    training_config:
        rl_framework: SB3 # or RLLIB_single_agent or RLLIB_multi_agent
        rl_algorithm: PPO # or A2C
        n_learn_episodes: 5
        max_steps_per_episode: 200
        n_eval_episodes: 1
        deterministic_eval: True
        seed: 123


``rl_framework``
----------------
The RL (Reinforcement Learning) Framework to use in the training session

Options available are:

- ``SB3`` (Stable Baselines 3)
- ``RLLIB_single_agent`` (Single Agent Ray RLLib)
- ``RLLIB_multi_agent`` (Multi Agent Ray RLLib)

``rl_algorithm``
----------------
The Reinforcement Learning Algorithm to use in the training session

Options available are:

- ``PPO`` (Proximal Policy Optimisation)
- ``A2C`` (Advantage Actor Critic)

``n_learn_episodes``
--------------------
The number of episodes to train the agent(s).
This should be an integer value above ``0``

``max_steps_per_episode``
-------------------------
The number of steps each episode will last for.
This should be an integer value above ``0``.


``n_eval_episodes``
-------------------
Optional. Default value is ``0``.

The number of evaluation episodes to run the trained agent for.
This should be an integer value above ``0``.

``deterministic_eval``
----------------------
Optional. By default this value is ``False``.

If this is set to ``True``, the agents will act deterministically instead of stochastically.



``seed``
--------
Optional.

The seed is used (alongside ``deterministic_eval``) to reproduce a previous instance of training and evaluation of an RL agent.
The seed should be an integer value.
Useful for debugging.
