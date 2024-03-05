.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


``io_settings``
===============
This section configures how PrimAITE saves data during simulation and training.

``io_settings`` hierarchy
-------------------------

.. code-block:: yaml

    io_settings:
        save_final_model: True
        save_checkpoints: False
        checkpoint_interval: 10
        # save_logs: True
        # save_transactions: False
        save_agent_actions: True
        save_step_metadata: False
        save_pcap_logs: False
        save_sys_logs: False

``save_final_model``
--------------------

Optional. Default value is ``True``.

Only used if training with PrimaiteSession.
If ``True``, the policy will be saved after the final training iteration.


``save_checkpoints``
--------------------

Optional. Default value is ``False``.

Only used if training with PrimaiteSession.
If ``True``, the policy will be saved periodically during training.


``checkpoint_interval``
-----------------------

Optional. Default value is ``10``.

Only used if training with PrimaiteSession and if ``save_checkpoints`` is ``True``.
Defines how often to save the policy during training.


``save_logs``
-------------

*currently unused*.


``save_agent_actions``

Optional. Default value is ``True``.

If ``True``, this will create a JSON file each episode detailing every agent's action in each step of that episode, formatted according to the CAOS format. This includes scripted, RL, and red agents.

``save_step_metadata``
----------------------

Optional. Default value is ``False``.

If ``True``, The RL agent(s) actions, environment states and other data will be saved at every single step.


``save_pcap_logs``
------------------

Optional. Default value is ``False``.

If ``True``, then the pcap files which contain all network traffic during the simulation will be saved.


``save_sys_logs``
-----------------

Optional. Default value is ``False``.

If ``True``, then the log files which contain all node actions during the simulation will be saved.
