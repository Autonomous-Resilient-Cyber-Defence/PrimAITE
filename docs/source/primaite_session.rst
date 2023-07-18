.. only:: comment

    Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.

.. _run a primaite session:

Run a PrimAITE Session
======================

Run
---

A PrimAITE session can be ran either with the ``primaite session`` command from the cli
(See :func:`primaite.cli.session`), or by calling :func:`primaite.main.run` from a Python terminal or Jupyter Notebook.
Both the ``primaite session`` and :func:`primaite.main.run` take a training config and a lay down config as parameters.


.. tabs::

    .. code-tab:: bash
        :caption: Unix CLI

        cd ~/primaite
        source ./.venv/bin/activate
        primaite session ./config/my_training_config.yaml ./config/my_lay_down_config.yaml

    .. code-tab:: powershell
        :caption: Powershell CLI

        cd ~\primaite
        .\.venv\Scripts\activate
        primaite session .\config\my_training_config.yaml .\config\my_lay_down_config.yaml


    .. code-tab:: python
        :caption: Python

        from primaite.main import run

        training_config = <path to training config yaml file>
        lay_down_config = <path to lay down config yaml file>
        run(training_config, lay_down_config)

When a session is ran, a session output sub-directory is created in the users app sessions directory (``~/primaite/sessions``).
The sub-directory is formatted as such: ``~/primaite/sessions/<yyyy-mm-dd>/<yyyy-mm-dd>_<hh-mm-dd>/``

For example, when running a session at 17:30:00 on 31st January 2023, the session will output to:
``~/primaite/sessions/2023-01-31/2023-01-31_17-30-00/``.


Outputs
-------

PrimAITE produces four types of outputs:

* Session Metadata
* Results
* Diagrams
* Saved agents (training checkpoints and a final trained agent)


**Session Metadata**

PrimAITE creates a ``session_metadata.json`` file that contains the following metadata:

    * **uuid** - The UUID assigned to the session upon instantiation.
    * **start_datetime** - The date & time the session started in iso format.
    * **end_datetime** - The date & time the session ended in iso format.
    * **learning**
        * **total_episodes** - The total number of training episodes completed.
        * **total_time_steps** - The total number of training time steps completed.
    * **evaluation**
        * **total_episodes** - The total number of evaluation episodes completed.
        * **total_time_steps** - The total number of evaluation time steps completed.
    * **env**
        * **training_config**
            * **All training config items**
        * **lay_down_config**
            * **All lay down config items**


**Results**

PrimAITE automatically creates two sets of results from each learning and evaluation session:

* Average reward per episode - a csv file listing the average reward for each episode of the session. This provides, for example, an indication of the change over a training session of the reward value
* All transactions - a csv file listing the following values for every step of every episode:

    * Timestamp
    * Episode number
    * Step number
    * Reward value
    * Action taken (as presented by the blue agent on this step). Individual elements of the action space are presented in the format AS_X
    * Initial observation space (what the blue agent observed when it decided its action)

**Diagrams**

* For each session, PrimAITE automatically creates a visualisation of the system / network lay down configuration.
* For each learning and evaluation task within the session, PrimAITE automatically plots the average reward per episode using PlotLY and saves it to the learning or evaluation subdirectory in the session directory.

**Saved agents**

For each training session, assuming the agent being trained implements the *save()* function and this function is called by the code, PrimAITE automatically saves the agent state.

**Example Session Directory Structure**

.. code-block:: text

    ~/
    └── primaite/
        └── sessions/
            └── 2023-07-18/
                └── 2023-07-18_11-06-04/
                    ├── evaluation/
                    │   ├── all_transactions_2023-07-18_11-06-04.csv
                    │   ├── average_reward_per_episode_2023-07-18_11-06-04.csv
                    │   └── average_reward_per_episode_2023-07-18_11-06-04.png
                    ├── learning/
                    │   ├── all_transactions_2023-07-18_11-06-04.csv
                    │   ├── average_reward_per_episode_2023-07-18_11-06-04.csv
                    │   ├── average_reward_per_episode_2023-07-18_11-06-04.png
                    │   ├── checkpoints/
                    │   │   └── sb3ppo_10.zip
                    │   ├── SB3_PPO.zip
                    │   └── tensorboard_logs/
                    │       ├── PPO_1/
                    │       │   └── events.out.tfevents.1689674765.METD-9PMRFB3.42960.0
                    │       ├── PPO_2/
                    │       │   └── events.out.tfevents.1689674766.METD-9PMRFB3.42960.1
                    │       ├── PPO_3/
                    │       │   └── events.out.tfevents.1689674766.METD-9PMRFB3.42960.2
                    │       ├── PPO_4/
                    │       │   └── events.out.tfevents.1689674767.METD-9PMRFB3.42960.3
                    │       ├── PPO_5/
                    │       │   └── events.out.tfevents.1689674767.METD-9PMRFB3.42960.4
                    │       ├── PPO_6/
                    │       │   └── events.out.tfevents.1689674768.METD-9PMRFB3.42960.5
                    │       ├── PPO_7/
                    │       │   └── events.out.tfevents.1689674768.METD-9PMRFB3.42960.6
                    │       ├── PPO_8/
                    │       │   └── events.out.tfevents.1689674769.METD-9PMRFB3.42960.7
                    │       ├── PPO_9/
                    │       │   └── events.out.tfevents.1689674770.METD-9PMRFB3.42960.8
                    │       └── PPO_10/
                    │           └── events.out.tfevents.1689674770.METD-9PMRFB3.42960.9
                    ├── network_2023-07-18_11-06-04.png
                    └── session_metadata.json

Loading a session
-----------------

A previous session can be loaded by providing the **directory** of the previous session to either the ``primaite session`` command from the cli
(See :func:`primaite.cli.session`), or by calling :func:`primaite.main.run` with session_path.

.. tabs::

    .. code-tab:: bash
        :caption: Unix CLI

        cd ~/primaite
        source ./.venv/bin/activate
        primaite session --load "path/to/session"

    .. code-tab:: bash
        :caption: Powershell CLI

        cd ~\primaite
        .\.venv\Scripts\activate
        primaite session --load "path\to\session"


    .. code-tab:: python
        :caption: Python

        from primaite.main import run

        run(session_path=<previous session directory>)

When PrimAITE runs a loaded session, PrimAITE will output in the provided session directory
