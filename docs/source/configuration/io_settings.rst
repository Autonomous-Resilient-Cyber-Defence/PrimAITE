.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


``io_settings``
===============
This section configures how PrimAITE saves data during simulation and training.

**save_final_model**: Only used if training with PrimaiteSession, if true, the policy will be saved after the final training iteration.

**save_checkpoints**: Only used if training with PrimaiteSession, if true, the policy will be saved periodically during training.

**checkpoint_interval**: Only used if training with PrimaiteSession and if ``save_checkpoints`` is true. Defines how often to save the policy during training.

**save_logs**: *currently unused*.

**save_transactions**: *currently unused*.

**save_tensorboard_logs**: *currently unused*.

**save_step_metadata**: Whether to save the RL agents' action, environment state, and other data at every single step.

**save_pcap_logs**: Whether to save pcap files of all network traffic during the simulation.

**save_sys_logs**: Whether to save system logs from all nodes during the simulation.
