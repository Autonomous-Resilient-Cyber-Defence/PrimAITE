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
* Saved agents


**Session Metadata**

PrimAITE creates a ``session_metadata.json`` file that contains the following metadata:

    * **uuid** - The UUID assigned to the session upon instantiation.
    * **start_datetime** - The date & time the session started in iso format.
    * **end_datetime** - The date & time the session ended in iso format.
    * **total_episodes** - The total number of training episodes completed.
    * **total_time_steps** - The total number of training time steps completed.
    * **env**
        * **training_config**
            * **All training config items**
        * **lay_down_config**
            * **All lay down config items**


**Results**

PrimAITE automatically creates two sets of results from each session:

* Average reward per episode - a csv file listing the average reward for each episode of the session. This provides, for example, an indication of the change over a training session of the reward value
* All transactions - a csv file listing the following values for every step of every episode:

    * Timestamp
    * Episode number
    * Step number
    * Initial observation space (what the blue agent observed when it decided its action)
    * Reward value
    * Action taken (as presented by the blue agent on this step). Individual elements of the action space are presented in the format AS_X

**Diagrams**

For each session, PrimAITE automatically creates a visualisation of the system / network lay down configuration.

**Saved agents**

For each training session, assuming the agent being trained implements the *save()* function and this function is called by the code, PrimAITE automatically saves the agent state.
